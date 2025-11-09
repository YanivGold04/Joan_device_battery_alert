#!/usr/bin/env python3
"""
Joan Device Battery Alert
-------------------------
Monitors Joan display devices' battery levels and posts alerts to Slack if any
devices fall below a given threshold.

All secrets and identifiers are loaded from environment variables. No sensitive
information is committed to the repository.

Endpoints:
- GET /        -> runs a full battery check and sends alerts if needed
- GET /health  -> returns {"status": "healthy"}

Author: (Yaniv Goldman / immunai)
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, jsonify

# --- Configuration (loaded from environment variables) ---
CLIENT_ID = os.getenv("JOAN_CLIENT_ID", "<REDACTED>")
CLIENT_SECRET = os.getenv("JOAN_CLIENT_SECRET", "<REDACTED>")
TOKEN_URL = os.getenv("JOAN_TOKEN_URL", "https://portal.getjoan.com/api/token/")
DEVICES_URL = os.getenv("JOAN_DEVICES_URL", "https://portal.getjoan.com/api/v1.0/devices/")
BATTERY_THRESHOLD = int(os.getenv("BATTERY_THRESHOLD", "90"))
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "<REDACTED>")

# Example sanitized device lists (use your own internally)
ISRAEL_DEVICES = {
    "uuid-1": "Israel Office - Room A",
    "uuid-2": "Israel Office - Room B",
    "uuid-3": "Israel Office - Room C",
}
US_DEVICES = {
    "uuid-4": "US Office - Room D",
    "uuid-5": "US Office - Room E",
    "uuid-6": "US Office - Room F",
}

# Create lowercase lookup maps
ISRAEL_DEVICES_LC = {k.lower(): v for k, v in ISRAEL_DEVICES.items()}
US_DEVICES_LC = {k.lower(): v for k, v in US_DEVICES.items()}

app = Flask(__name__)


# --- Slack Notification ---
def send_to_slack(message: str) -> None:
    """Send formatted alert message to Slack."""
    if not SLACK_WEBHOOK or SLACK_WEBHOOK == "<REDACTED>":
        print("Slack webhook not configured. Message not sent.")
        return
    try:
        res = requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=10)
        res.raise_for_status()
        print("Slack message sent successfully.")
    except Exception as e:
        print("Failed to send Slack message:", e)


# --- Joan API ---
def get_token() -> str:
    """Request access token from Joan API."""
    print("Requesting access token...")
    r = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        timeout=10,
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    print("Access token received.")
    return token


def fetch_devices(token: str):
    """Fetch all Joan devices and their battery levels."""
    print("Fetching devices list...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(DEVICES_URL, headers=headers, timeout=10)
    r.raise_for_status()
    print("Devices list fetched.")
    return r.json().get("results", [])


def build_message_lines(devices):
    """Build readable message lines grouped by region."""
    israel_lines = []
    us_lines = []

    for d in devices:
        uuid = (d.get("uuid") or "").lower()
        battery = d.get("battery")
        if battery is None:
            continue

        if battery < BATTERY_THRESHOLD:
            if uuid in ISRAEL_DEVICES_LC:
                israel_lines.append(f"- {ISRAEL_DEVICES_LC[uuid]}: {battery}%")
            elif uuid in US_DEVICES_LC:
                us_lines.append(f"- {US_DEVICES_LC[uuid]}: {battery}%")
            else:
                name = d.get("roomResources")[0].get("name") if d.get("roomResources") else uuid
                us_lines.append(f"- {name}: {battery}%")

    return israel_lines, us_lines


# --- Flask Routes ---
@app.route("/", methods=["GET"])
def battery_check():
    """Main route to check device batteries and send alerts."""
    try:
        token = get_token()
        devices = fetch_devices(token)
        israel_lines, us_lines = build_message_lines(devices)

        if not israel_lines and not us_lines:
            return jsonify({"message": "No devices below battery threshold."}), 200

        message_parts = []
        if israel_lines:
            message_parts.append(f":flag-il: *Israel devices below {BATTERY_THRESHOLD}%*:alert:")
            message_parts.extend(israel_lines)
        if israel_lines and us_lines:
            message_parts.append("")
        if us_lines:
            message_parts.append(f":us: *US devices below {BATTERY_THRESHOLD}%*:alert:")
            message_parts.extend(us_lines)

        final_message = "\n".join(message_parts)
        send_to_slack(final_message)
        return jsonify({"message": "Alert sent successfully", "details": final_message}), 200

    except Exception as e:
        print("Error during battery check:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
