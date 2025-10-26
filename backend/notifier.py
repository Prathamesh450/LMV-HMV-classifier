"""Simple Redis subscriber that listens for violation:<jurisdiction> events
and logs or forwards notifications to a notification endpoint (placeholder).

Run this script alongside your backend to observe events emitted by the AI worker.
"""

import os
import json
import time

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
NOTIFY_ENDPOINT = os.environ.get(
    "NOTIFY_ENDPOINT"
)  # optional HTTP endpoint to forward events
FCM_SERVER_KEY = os.environ.get("FCM_SERVER_KEY")  # optional: send FCM notifications
BACKEND_PUBLIC_URL = os.environ.get("BACKEND_PUBLIC_URL", "http://localhost:8000")


def send_fcm_notification(topic, title, body):
    if not FCM_SERVER_KEY:
        return False
    try:
        import requests

        payload = {
            "to": f"/topics/{topic}",
            "notification": {"title": title, "body": body},
        }
        headers = {
            "Authorization": "key=" + FCM_SERVER_KEY,
            "Content-Type": "application/json",
        }
        resp = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            headers=headers,
            json=payload,
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def main():
    try:
        import redis
    except Exception as e:
        print("redis package not installed:", e)
        return

    r = redis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    pubsub.psubscribe("violation:*")
    print("Subscribed to violation:* on", REDIS_URL)

    for message in pubsub.listen():
        if message is None:
            time.sleep(0.1)
            continue
        if message.get("type") not in ("message", "pmessage"):
            continue
        data = message.get("data")
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            payload = json.loads(data)
        except Exception:
            payload = {"raw": data}

        channel = message.get("channel") or message.get("pattern")
        print("[violation event]", channel, payload)

        # Forward to a HTTP endpoint if configured
        if NOTIFY_ENDPOINT:
            try:
                import requests

                requests.post(NOTIFY_ENDPOINT, json=payload, timeout=5)
            except Exception as e:
                print("Failed to forward event:", e)

        # Optionally send an FCM topic notification to authorities
        if FCM_SERVER_KEY:
            try:
                title = f"Violation in {payload.get('jurisdiction', 'unknown')}"
                body = (
                    f"{payload.get('vehicle_type')} - {payload.get('plate') or 'N/A'}"
                )
                # include an artifact link if evidence path is provided
                evidence_path = payload.get("evidence_path")
                if evidence_path:
                    # only include the basename in the link - backend serves artifacts by filename
                    from os.path import basename

                    fname = basename(evidence_path)
                    evidence_url = (
                        f"{BACKEND_PUBLIC_URL.rstrip('/')}/artifact?file={fname}"
                    )
                    body = body + f"\nView evidence: {evidence_url}"

                send_fcm_notification("authorities", title, body)
            except Exception as e:
                print("Failed to send FCM:", e)

            # If firebase credentials are available and evidence file is local, upload evidence
            if os.environ.get("SERVICE_ACCOUNT_PATH") and payload.get("evidence_path"):
                evidence_path = payload.get("evidence_path")
                try:
                    if os.path.exists(evidence_path):
                        try:
                            from database.upload_vehicle_evidence import (
                                upload_vehicle_record,
                            )

                            plate = payload.get("plate") or ""
                            # camera info unknown in event; use placeholders
                            cam_id = os.environ.get("CAMERA_ID", "unknown_cam")
                            cam_name = os.environ.get("CAMERA_NAME", "unknown")
                            cam_lat = float(os.environ.get("CAMERA_LAT", 0.0))
                            cam_lon = float(os.environ.get("CAMERA_LON", 0.0))
                            vtype = payload.get("vehicle_type", "HMV")
                            ref, doc = upload_vehicle_record(
                                evidence_path,
                                plate,
                                cam_id,
                                cam_name,
                                cam_lat,
                                cam_lon,
                                vtype,
                            )
                            print(
                                "Uploaded evidence to Firebase, doc:",
                                getattr(ref[1], "id", str(ref)),
                            )
                        except Exception as e:
                            print("Failed to upload evidence via Firebase helper:", e)
                    else:
                        print(
                            "Evidence path not found locally, skipping upload:",
                            evidence_path,
                        )
                except Exception as e:
                    print("Error checking evidence path:", e)


if __name__ == "__main__":
    main()
