from __future__ import annotations

import re
import threading
import time
import winsound
from dataclasses import dataclass
from typing import Callable

from activitysmith import ActivitySmith, action
from curl_cffi import requests


OFFERS_URL = (
    "https://shopper-api.instacart.com/rpc/instacart.fulfillment.public_apis."
    "work_details.work_offers_service.v1.WorkOffersService/GetWorkOffers"
)


@dataclass(frozen=True)
class MonitorConfig:
    activitysmith_api_key: str
    auth_token: str
    cookies: str
    shopper_id: str
    gas_price: float = 1.84
    fuel_economy: float = 9.4
    maintenance_per_km: float = 0.12
    poll_seconds: int = 8


@dataclass(frozen=True)
class BatchResult:
    pay: float
    distance: float
    net_estimate: float
    hourly_estimate: float
    recommendation: str
    body: str


def _first_number(patterns: tuple[str, ...], text: str) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


class BatchMonitor:
    def __init__(
        self,
        config: MonitorConfig,
        on_batch: Callable[[BatchResult], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        self.config = config
        self.on_batch = on_batch or (lambda result: None)
        self.on_status = on_status or (lambda message: None)
        self._last_batch_signature: str | None = None
        self._smith = ActivitySmith(api_key=config.activitysmith_api_key)

    def _status(self, message: str) -> None:
        self.on_status(message)

    def check_once(self) -> BatchResult | None:
        headers = {
            "accept": "application/json",
            "content-type": "application/protobuf",
            "authorization": self.config.auth_token,
            "cookie": self.config.cookies,
            "x-shopper-id": self.config.shopper_id,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/110.0.0.0 Safari/537.36",
            "accept-language": "en-CA,en;q=0.9",
            "origin": "https://shopper.instacart.com",
            "referer": "https://shopper.instacart.com/",
        }
        response = requests.post(
            OFFERS_URL,
            headers=headers,
            data=b"",
            impersonate="chrome110",
            timeout=20,
        )
        if response.status_code == 429:
            self._status("Instacart rate limited the monitor; waiting 30 seconds.")
            time.sleep(30)
            return None
        response.raise_for_status()

        response_text = response.text
        numbers = re.findall(r"\d+(?:\.\d+)?", response_text)
        current_signature = ",".join(numbers)
        if current_signature == self._last_batch_signature:
            return None
        self._last_batch_signature = current_signature

        pay = _first_number(
            (
                r"(?:pay|earnings|total[_ ]?pay|batch[_ ]?pay)[^\d$]{0,30}\$?([0-9]+(?:\.[0-9]{1,2})?)",
                r"\$\s*([0-9]+\.[0-9]{1,2})",
            ),
            response_text,
        )
        distance = _first_number(
            (r"(?:distance|miles|kilomet(?:er|re)s?)[^\d]{0,30}([0-9]+(?:\.[0-9]{1,2})?)",),
            response_text,
        )
        if pay is None or distance is None or distance <= 0:
            self._status("Live response received, but no complete batch details were found.")
            return None

        fuel_cost = distance * self.config.fuel_economy / 100 * self.config.gas_price
        maintenance_cost = distance * self.config.maintenance_per_km
        net_estimate = pay - fuel_cost - maintenance_cost
        hourly_estimate = net_estimate / 0.75
        recommendation = "✅ ACCEPT" if pay / distance >= 1.00 and hourly_estimate >= 25.00 else "⚠️ CONSIDER"
        body = f"Pay: ${pay} | Dist: {distance}km\nNet: ${net_estimate:.2f} | $/hr: ${hourly_estimate:.2f}"
        result = BatchResult(pay, distance, net_estimate, hourly_estimate, recommendation, body)

        winsound.Beep(1000, 500)
        self._smith.notifications.send(
            title=f"Batch Buddy: {recommendation}",
            message=body,
            actions=[
                action(title="Accept", type="open_url", url="instacartshopper://"),
                action(title="Reject", type="open_url", url="activitysmith://dismiss"),
            ],
        )
        self.on_batch(result)
        self._status("New live batch sent to ActivitySmith.")
        return result

    def run(self, stop_event: threading.Event) -> None:
        self._status("Monitor started; polling live Instacart data.")
        while not stop_event.is_set():
            try:
                self.check_once()
            except Exception as error:
                self._status(f"Monitor error: {error}")
            stop_event.wait(self.config.poll_seconds)
        self._status("Monitor stopped.")
