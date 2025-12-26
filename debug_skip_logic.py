import csv
import os
from garmin_export import has_health_metrics

output_file = "garmin_daily_health.csv"

if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        
        print(f"Total rows: {len(rows)}")
        skipped = 0
        for i, row in enumerate(rows):
            has_metrics = has_health_metrics(row)
            if has_metrics:
                skipped += 1
            
            if i < 5:
                print(f"\nRow {i}: {row['date']}")
                print(f"  sleepDuration: '{row.get('sleepDuration')}'")
                print(f"  stressAvg: '{row.get('stressAvg')}'")
                print(f"  has_health_metrics: {has_metrics} (Bool: {bool(has_metrics)})")
        
        print(f"\nTotal skipped: {skipped}")
else:
    print("CSV file not found.")
