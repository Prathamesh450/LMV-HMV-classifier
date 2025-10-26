"""Helper to acquire common model weights for the AI worker.

This script will try to use the installed ultralytics package to ensure
`yolov8n.pt` is available. If ultralytics is not installed it prints
instructions to obtain weights manually.
"""

import subprocess
import sys
import os


def try_download_with_ultralytics():
    try:
        # Attempt to import and instantiate YOLO which will download weights if needed
        from ultralytics import YOLO

        print('Attempting to instantiate YOLO("yolov8n.pt") to download weights...')
        YOLO("yolov8n.pt")
        print("yolov8n.pt should now be available.")
        return True
    except Exception as e:
        print("Failed to use ultralytics to download weights:", e)
        return False


def main():
    ok = try_download_with_ultralytics()
    if not ok:
        print("\nPlease install the ultralytics package and re-run:")
        print("    pip install ultralytics")
        print("Or download YOLOv8 weights manually and place them into ai/models/")
        print("Example manual download URL (copy to browser):")
        print("https://github.com/ultralytics/assets/releases")


if __name__ == "__main__":
    main()
