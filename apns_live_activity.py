from __future__ import annotations

import time
from pathlib import Path

import jwt
from curl_cffi import requests


def send_live_activity_update(
    *,
    push_token: str,
    team_id: str,
    key_id: str,
    private_key_path: str,
    bundle_id: str,
    recommendation: str,
    pay: float,
    kilometres: float,
    items: int,
    estimated_net: float,
    hourly_rate: float,
    score: int,
    message: str,
    production: bool = True,
) -> None:
    private_key = Path(private_key_path).read_text(encoding="utf-8")
    now = int(time.time())
    token = jwt.encode(
        {"iss": team_id, "iat": now},
        private_key,
        algorithm="ES256",
        headers={"kid": key_id},
    )
    host = "api.push.apple.com" if production else "api.sandbox.push.apple.com"
    payload = {
        "aps": {
            "timestamp": now,
            "event": "update",
            "content-state": {
                "recommendation": recommendation,
                "pay": pay,
                "kilometres": kilometres,
                "items": items,
                "estimatedNet": estimated_net,
                "hourlyRate": hourly_rate,
                "score": score,
                "message": message,
                "updatedAt": now - 978307200,
            },
            "stale-date": now + 1800,
        }
    }
    response = requests.post(
        f"https://{host}/3/device/{push_token.strip().replace(' ', '')}",
        headers={
            "authorization": f"bearer {token}",
            "apns-topic": f"{bundle_id}.push-type.liveactivity",
            "apns-push-type": "liveactivity",
            "apns-priority": "10",
            "content-type": "application/json",
        },
        json=payload,
        impersonate="chrome110",
        timeout=20,
    )
    if response.status_code >= 300:
        raise RuntimeError(f"APNs live activity update failed ({response.status_code}): {response.text}")
