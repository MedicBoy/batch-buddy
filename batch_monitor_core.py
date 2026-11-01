from __future__ import annotations

import re
import threading
import time
import winsound
from dataclasses import dataclass
from typing import Callable

from activitysmith import ActivitySmith, action, content_state
from curl_cffi import requests

from apns_live_activity import send_live_activity_update


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
    live_activity_push_token: str = ""
    apple_team_id: str = ""
    apple_key_id: str = ""
    apple_private_key_path: str = ""
    bundle_id: str = "com.batchbuddy.advisor"
    apns_production: bool = False


@dataclass(frozen=True)
class BatchResult:
    pay: float
    distance: float
    items: int
    net_estimate: float
    hourly_estimate: float
    recommendation: str
    body: str
    fuel_cost: float = 0.0
    maintenance_cost: float = 0.0
    pay_per_km: float = 0.0
    signature: str = ""
    observed_at: float = 0.0


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
        pay_per_km = pay / distance
        recommendation = "✅ ACCEPT" if pay_per_km >= 1.00 and hourly_estimate >= 25.00 else "⚠️ CONSIDER"
        body = f"Pay: ${pay} | Dist: {distance}km\nNet: ${net_estimate:.2f} | $/hr: ${hourly_estimate:.2f}"
        item_value = _first_number(
            (r"(?:items?|units?)[^\d]{0,20}([0-9]+)",),
            response_text,
        )
        items = int(item_value or 0)
        body = f"Pay: ${pay} | Dist: {distance}km | Items: {items}\nNet: ${net_estimate:.2f} | $/hr: ${hourly_estimate:.2f}"
        observed_at = time.time()
        result = BatchResult(
            pay=pay,
            distance=distance,
            items=items,
            net_estimate=net_estimate,
            hourly_estimate=hourly_estimate,
            recommendation=recommendation,
            body=body,
            fuel_cost=fuel_cost,
            maintenance_cost=maintenance_cost,
            pay_per_km=pay_per_km,
            signature=current_signature,
            observed_at=observed_at,
        )

        winsound.Beep(1000, 500)
        day_tag = time.strftime("%Y-%m-%d", time.localtime(observed_at))
        recommendation_tag = "accept" if recommendation == "✅ ACCEPT" else "consider"
        tags = [
            "batch-buddy",
            f"shopper:{self.config.shopper_id}",
            f"date:{day_tag}",
            f"recommendation:{recommendation_tag}",
        ]
        metadata = {
            "batch_signature": current_signature[:4000],
            "pay": pay,
            "distance_km": distance,
            "items": items,
            "pay_per_km": pay_per_km,
            "fuel_cost": fuel_cost,
            "maintenance_cost": maintenance_cost,
            "net_estimate": net_estimate,
            "hourly_estimate": hourly_estimate,
            "recommendation": recommendation,
            "shopper_id": self.config.shopper_id,
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(observed_at)),
        }
        self._smith.notifications.send(
            title=f"Batch Buddy: {recommendation}",
            message=body,
            metadata=metadata,
            tags=tags,
            actions=[
                action(title="Accept", type="open_url", url="instacartshopper://"),
                action(title="Reject", type="open_url", url="activitysmith://dismiss"),
            ],
        )
        try:
            self._smith.live_activities.stream(
                "batch-buddy-current",
                content_state=content_state(
                    title=f"Batch Buddy: {recommendation}",
                    message=body,
                    type="alert",
                    color="green" if recommendation == "✅ ACCEPT" else "orange",
                ),
                action=action(title="Open Shopper", type="open_url", url="instacartshopper://"),
                secondary_action=action(title="Reject", type="open_url", url="activitysmith://dismiss"),
                metadata=metadata,
                tags=tags,
            )
        except Exception as error:
            self._status(f"ActivitySmith alert sent; Live Activity update skipped: {error}")

        if all(
            (
                self.config.live_activity_push_token,
                self.config.apple_team_id,
                self.config.apple_key_id,
                self.config.apple_private_key_path,
            )
        ):
            try:
                send_live_activity_update(
                    push_token=self.config.live_activity_push_token,
                    team_id=self.config.apple_team_id,
                    key_id=self.config.apple_key_id,
                    private_key_path=self.config.apple_private_key_path,
                    bundle_id=self.config.bundle_id,
                    recommendation=recommendation,
                    pay=pay,
                    kilometres=distance,
                    items=items,
                    estimated_net=net_estimate,
                    hourly_rate=hourly_estimate,
                    score=0,
                    message=body,
                    production=self.config.apns_production,
                )
                self._status("Native Batch Buddy Live Activity updated for Lock Screen/CarPlay.")
            except Exception as error:
                self._status(f"ActivitySmith sent; native Live Activity update failed: {error}")
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
