import os
import getpass
from dotenv import load_dotenv
from garmin_export import export_garmin_data, export_daily_health_data

# Load environment variables
load_dotenv()

def main():
    print("Garmin Stats Export to CSV Tool")
    print("\nWhat would you like to export?")
    print("1. Activities with health metrics (for activity days only)")
    print("2. Daily health data (for ALL days, including rest days)")
    print("3. Both")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    # Garmin Credentials
    username = os.getenv("GARMIN_USER")
    password = os.getenv("GARMIN_PASSWORD") or os.getenv("PASSWORD")
    
    if username and password:
        print(f"\nUsing credentials from .env for user: {username}")
    else:
        print("\nCredentials not found in .env (GARMIN_USER, GARMIN_PASSWORD/PASSWORD)")
        username = input("Enter Garmin Connect Username: ")
        password = getpass.getpass("Enter Garmin Connect Password: ")
    
    if choice in ['1', '3']:
        # Export activities
        output_file = "garmin_stats.csv"
        print("\n--- Starting Activity Export ---")
        try:
            export_garmin_data(username, password, output_file)
            print(f"\n✓ Activities saved to {output_file}")
        except Exception as e:
            print(f"✗ Activity export failed: {e}")
            if choice == '1':
                return
    
    if choice in ['2', '3']:
        # Export daily health data
        health_file = "garmin_daily_health.csv"
        print("\n--- Starting Daily Health Data Export ---")
        print("This will export health metrics for ALL days (including rest days).")
        print("This may take a while depending on the date range...")
        
        start_date = input("Start date (YYYY-MM-DD, or press Enter for 2000-01-01): ").strip()
        if not start_date:
            start_date = "2000-01-01"
        
        end_date = input("End date (YYYY-MM-DD, or press Enter for today): ").strip()
        if not end_date:
            end_date = None
        
        try:
            export_daily_health_data(username, password, health_file, start_date, end_date)
            print(f"\n✓ Daily health data saved to {health_file}")
        except Exception as e:
            print(f"✗ Daily health data export failed: {e}")

if __name__ == "__main__":
    main()
