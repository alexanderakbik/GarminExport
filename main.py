import os
import getpass
from garmin_export import export_garmin_data

def main():
    print("Garmin Stats Export to CSV Tool")
    
    # Garmin Credentials
    username = input("Enter Garmin Connect Username: ")
    password = getpass.getpass("Enter Garmin Connect Password: ")
    
    output_file = "garmin_stats.csv"
    
    # 1. Export from Garmin
    print("\n--- Starting Garmin Export ---")
    try:
        export_garmin_data(username, password, output_file)
        print(f"\nSuccess! Stats saved to {output_file}")
    except Exception as e:
        print(f"Garmin export failed: {e}")
        return

if __name__ == "__main__":
    main()
