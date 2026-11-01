import os
import re
import time
import winsound

from activitysmith import ActivitySmith, action
from curl_cffi import requests


AUTH_TOKEN = os.environ["INSTACART_AUTH_TOKEN"]
COOKIES = os.environ["INSTACART_COOKIES"]
SHOPPER_ID = os.environ.get("INSTACART_SHOPPER_ID", "40757189")

OFFERS_URL = (
    "https://shopper-api.instacart.com/rpc/instacart.fulfillment.public_apis."
    "work_details.work_offers_service.v1.WorkOffersService/GetWorkOffers"
)

smith = ActivitySmith(api_key=os.environ["ACTIVITYSMITH_API_KEY"])
last_batch_signature = None


def _first_number(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def check_batches():
    global last_batch_signature

    headers = {
        "accept": "application/json",
        "content-type": "application/protobuf",
        "authorization": AUTH_TOKEN,
        "cookie": COOKIES,
        "x-shopper-id": SHOPPER_ID,
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
        time.sleep(30)
        return

    response.raise_for_status()
    response_text = response.text

    numbers = re.findall(r"\d+(?:\.\d+)?", response_text)
    current_signature = ",".join(numbers)
    if current_signature == last_batch_signature:
        return
    last_batch_signature = current_signature

    pay = _first_number(
        (
            r"(?:pay|earnings|total[_ ]?pay|batch[_ ]?pay)[^\d$]{0,30}\$?([0-9]+(?:\.[0-9]{1,2})?)",
            r"\$\s*([0-9]+\.[0-9]{1,2})",
        ),
        response_text,
    )
    distance = _first_number(
        (
            r"(?:distance|miles|kilomet(?:er|re)s?)[^\d]{0,30}([0-9]+(?:\.[0-9]{1,2})?)",
        ),
        response_text,
    )

    if pay is None or distance is None or distance <= 0:
        return

    gas_price = 1.84
    fuel_economy = 9.4
    maintenance_per_km = 0.12
    fuel_cost = distance * fuel_economy / 100 * gas_price
    maintenance_cost = distance * maintenance_per_km
    net_estimate = pay - fuel_cost - maintenance_cost
    hourly_estimate = net_estimate / 0.75

    rec = "✅ ACCEPT" if pay / distance >= 1.00 and hourly_estimate >= 25.00 else "⚠️ CONSIDER"
    body = f"Pay: ${pay} | Dist: {distance}km\nNet: ${net_estimate:.2f} | $/hr: ${hourly_estimate:.2f}"

    winsound.Beep(1000, 500)
    smith.notifications.send(
        title=f"Batch Buddy: {rec}",
        message=body,
        actions=[
            action(
                title="Accept",
                type="open_url",
                url="instacartshopper://",
            ),
            action(
                title="Reject",
                type="open_url",
                url="activitysmith://dismiss",
            ),
        ],
    )


if __name__ == "__main__":
    while True:
        try:
            check_batches()
        except Exception as error:
            print(f"Batch monitor error: {error}")
        time.sleep(8)
