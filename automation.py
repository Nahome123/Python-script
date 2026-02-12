import os
import json
import time
import shutil
import logging
import requests
from datetime import datetime

# =============================
# CONFIGURATION
# =============================
INCOMING_DIR = "./incoming"
PROCESSED_DIR = "./processed"
LOG_FILE = "./logs/automation.log"
API_ENDPOINT = "https://example.com/api/data"
API_KEY = "YOUR_API_KEY"
RETRY_LIMIT = 3
SLEEP_INTERVAL = 10  # seconds

# =============================
# LOGGING SETUP
# =============================
os.makedirs("./logs", exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =============================
# NORMALIZATION FUNCTION
# =============================
def normalize_payload(data):
    """
    Normalize inconsistent schemas into standard format
    """
    return {
        "device_id": data.get("id") or data.get("deviceId"),
        "timestamp": data.get("timestamp") or datetime.utcnow().isoformat(),
        "status": data.get("status", "unknown"),
        "metrics": data.get("metrics", {})
    }

# =============================
# API PUSH FUNCTION WITH RETRIES
# =============================
def send_to_api(payload):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logging.info(f"Successfully sent payload: {payload['device_id']}")
            return True
        except requests.RequestException as e:
            logging.error(f"Attempt {attempt} failed: {str(e)}")
            time.sleep(2)

    return False

# =============================
# PROCESS FILE FUNCTION
# =============================
def process_file(file_path):
    try:
        with open(file_path, "r") as f:
            raw_data = json.load(f)

        normalized = normalize_payload(raw_data)

        success = send_to_api(normalized)

        if success:
            shutil.move(file_path, os.path.join(PROCESSED_DIR, os.path.basename(file_path)))
        else:
            logging.error(f"Failed to send file after retries: {file_path}")

    except Exception as e:
        logging.exception(f"Error processing file {file_path}: {str(e)}")

# =============================
# MAIN LOOP
# =============================
def run():
    os.makedirs(INCOMING_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    logging.info("Automation server started...")

    while True:
        try:
            files = [f for f in os.listdir(INCOMING_DIR) if f.endswith(".json")]

            for filename in files:
                file_path = os.path.join(INCOMING_DIR, filename)
                process_file(file_path)

        except Exception as e:
            logging.exception(f"Unexpected error: {str(e)}")

        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    run()
