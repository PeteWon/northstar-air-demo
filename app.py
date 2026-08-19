from datetime import datetime, timezone
from pathlib import Path
import json
import secrets

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

EVENT_LOG = Path(__file__).resolve().parent / "events.jsonl"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_event(event_name, **fields):
    event = {
        "event": event_name,
        "anonymous_token": secrets.token_urlsafe(16),
        "timestamp_utc": utc_now(),
        **fields,
    }

    # Print the complete event to Render Logs
    print(
        json.dumps(event, indent=2, ensure_ascii=False),
        flush=True
    )

    # Also save the event locally
    with EVENT_LOG.open("a", encoding="utf-8") as log:
        log.write(json.dumps(event) + "\n")


@app.get("/")
def home():
    write_event("page_view")

    return render_template("index.html")


@app.post("/fingerprint")
def record_fingerprint():
    body = request.get_json(silent=True) or {}

    fingerprint = {
        "userAgent": body.get("userAgent"),
        "platform": body.get("platform"),
        "language": body.get("language"),
        "languages": body.get("languages"),
        "timezone": body.get("timezone"),

        "screenWidth": body.get("screenWidth"),
        "screenHeight": body.get("screenHeight"),
        "colorDepth": body.get("colorDepth"),

        "cpuCores": body.get("cpuCores"),
        "deviceMemory": body.get("deviceMemory"),

        "touchPoints": body.get("touchPoints"),

        "cookieEnabled": body.get("cookieEnabled"),
        "doNotTrack": body.get("doNotTrack"),
    }

    write_event(
        "browser_fingerprint",
        fingerprint=fingerprint,
    )

    return jsonify({
        "ok": True
    })


@app.post("/consent")
def record_consent():
    body = request.get_json(silent=True) or {}

    if body.get("consent") is not True:
        return jsonify({
            "ok": False,
            "error": "Consent required"
        }), 400

    device_label = body.get("device_label", "")

    if not isinstance(device_label, str):
        return jsonify({
            "ok": False,
            "error": "Invalid device label"
        }), 400

    if len(device_label) > 80:
        return jsonify({
            "ok": False,
            "error": "Device label must be 80 characters or fewer"
        }), 400

    write_event(
        "awareness_demo_click",
        device_label=device_label.strip()
    )

    return jsonify({
        "ok": True
    })


@app.post("/location")
def record_location():
    body = request.get_json(silent=True) or {}

    if body.get("consent") is not True:
        return jsonify({
            "ok": False,
            "error": "Location consent required"
        }), 400

    latitude = body.get("latitude")
    longitude = body.get("longitude")
    device_label = body.get("device_label", "")

    if not isinstance(device_label, str):
        return jsonify({
            "ok": False,
            "error": "Invalid device label"
        }), 400

    if len(device_label) > 80:
        return jsonify({
            "ok": False,
            "error": "Device label must be 80 characters or fewer"
        }), 400

    if not isinstance(latitude, (int, float)):
        return jsonify({
            "ok": False,
            "error": "Invalid latitude"
        }), 400

    if not isinstance(longitude, (int, float)):
        return jsonify({
            "ok": False,
            "error": "Invalid longitude"
        }), 400

    if not -90 <= latitude <= 90:
        return jsonify({
            "ok": False,
            "error": "Latitude out of range"
        }), 400

    if not -180 <= longitude <= 180:
        return jsonify({
            "ok": False,
            "error": "Longitude out of range"
        }), 400

    # Store only coarse location
    write_event(
        "location_shared",
        latitude=round(latitude, 2),
        longitude=round(longitude, 2),
        device_label=device_label.strip(),
    )

    return jsonify({
        "ok": True
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "ok"
    }), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )