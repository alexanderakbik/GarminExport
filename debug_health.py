import logging
import datetime
import json
import getpass
import os
from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_health():
    load_dotenv()

    # Credentials
    username = os.getenv("GARMIN_USER")
    password = os.getenv("GARMIN_PASSWORD") or os.getenv("PASSWORD")
    
    if not username or not password:
        print("Credentials not found in .env. Please set GARMIN_USER and GARMIN_PASSWORD (or PASSWORD).")
        return

    # Get date to inspect
    date_str = "2024-01-02"

    try:
        logger.info("Authenticating...")
        client = Garmin(username, password)
        client.login()
        
        # 1. Sleep Data
        try:
            print("\n--- SLEEP DATA ---")
            sleep_data = client.get_sleep_data(date_str)
            print(json.dumps(sleep_data, indent=2))
        except Exception as e:
            print(f"Error fetching sleep data: {e}")

        # 2. Stress Data
        try:
            print("\n--- STRESS DATA ---")
            stress_data = client.get_stress_data(date_str)
            print(json.dumps(stress_data, indent=2))
        except Exception as e:
            print(f"Error fetching stress data: {e}")

        # 3. Body Battery
        try:
            print("\n--- BODY BATTERY ---")
            bb_data = client.get_body_battery(date_str)
            print(json.dumps(bb_data, indent=2))
            
            # Inspect values
            if bb_data and isinstance(bb_data, list) and 'bodyBatteryValuesArray' in bb_data[0]:
                vals = bb_data[0]['bodyBatteryValuesArray']
                print(f"\nFirst 5 BB values: {vals[:5]}")
                if vals:
                    print(f"Type of value: {type(vals[0][1])}")
        except Exception as e:
            print(f"Error fetching body battery: {e}")

        # 4. Resting Heart Rate
        try:
            print("\n--- RHR ---")
            rhr = client.get_rhr_day(date_str)
            print(json.dumps(rhr, indent=2))
        except Exception as e:
            print(f"Error fetching RHR: {e}")

        # 5. Daily Steps
        try:
            print("\n--- DAILY STEPS ---")
            steps = client.get_daily_steps(date_str, date_str)
            print(json.dumps(steps, indent=2))
        except Exception as e:
            print(f"Error fetching steps: {e}")
            
        # 6. Training Readiness
        try:
            print("\n--- TRAINING READINESS ---")
            readiness = client.get_training_readiness(date_str)
            print(json.dumps(readiness, indent=2))
        except Exception as e:
            print(f"Error fetching training readiness: {e}")

    except Exception as e:
        logger.error(f"Authentication or connection error: {e}")

if __name__ == "__main__":
    debug_health()
