"""Small helper to publish a test violation event to Redis for smoke testing."""

import os
import json

try:
    import redis
except Exception:
    redis = None


def publish_test():
    REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    if redis is None:
        print("redis module not available")
        return
    r = redis.from_url(REDIS_URL)
    event = {
        "jurisdiction": "pune",
        "track_id": 123,
        "vehicle_type": "HMV",
        "plate": "MH12AB1234",
        "evidence_path": None,
    }
    r.publish("violation:pune", json.dumps(event))
    print("published sample event")


if __name__ == "__main__":
    publish_test()
