import csv
import os

def has_health_metrics(activity):
    """Check if activity already has health metrics data."""
    return (activity.get('sleepDuration') and activity.get('stressAvg'))

output_file = "garmin_daily_health.csv"

if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        
        print(f"Total rows: {len(rows)}")
        for i, row in enumerate(rows[:5]):
            print(f"\nRow {i}: {row['date']}")
            print(f"  sleepDuration: '{row.get('sleepDuration')}' (Bool: {bool(row.get('sleepDuration'))})")
            print(f"  stressAvg: '{row.get('stressAvg')}' (Bool: {bool(row.get('stressAvg'))})")
            print(f"  bodyBatteryAvg: '{row.get('bodyBatteryAvg')}' (Bool: {bool(row.get('bodyBatteryAvg'))})")
            print(f"  has_health_metrics: {has_health_metrics(row)}")
else:
    print("CSV file not found.")
