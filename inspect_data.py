import logging
import os
import datetime
import json
from garminconnect import Garmin
import getpass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inspect_data():
    username = input("Enter Garmin Connect Username: ")
    password = getpass.getpass("Enter Garmin Connect Password: ")

    try:
        logger.info("Authenticating...")
        client = Garmin(username, password)
        client.login()
        
        start_date = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        end_date = datetime.date.today().isoformat()
        
        logger.info(f"Fetching activities from {start_date} to {end_date}...")
        activities = client.get_activities_by_date(start_date, end_date)
        
        if activities:
            print(json.dumps(activities[0], indent=2))
        else:
            logger.info("No activities found in the last 7 days.")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    inspect_data()
