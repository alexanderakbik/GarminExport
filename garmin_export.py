import csv
import datetime
import importlib
import logging
import os
import subprocess
import sys

GARMINCONNECT_PACKAGE = "garminconnect"
GARMINCONNECT_VERSION = "0.2.11"
GARMINCONNECT_SPEC = f"{GARMINCONNECT_PACKAGE}=={GARMINCONNECT_VERSION}"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _load_garmin_client():
    """Ensure garminconnect is available and return the Garmin client class."""
    try:
        module = importlib.import_module(GARMINCONNECT_PACKAGE)
        return getattr(module, "Garmin")
    except ModuleNotFoundError:
        logger.info(
            "Missing dependency '%s'. Installing it via pip so the export can proceed...",
            GARMINCONNECT_PACKAGE,
        )
        install_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            GARMINCONNECT_SPEC,
        ]
        try:
            subprocess.check_call(install_cmd)
        except Exception as install_error:
            raise ModuleNotFoundError(
                f"Could not import '{GARMINCONNECT_PACKAGE}' and automatic installation "
                f"using '{' '.join(install_cmd)}' failed. "
                "Install the dependency manually with 'pip install -r requirements.txt'."
            ) from install_error
        module = importlib.import_module(GARMINCONNECT_PACKAGE)
        return getattr(module, "Garmin")

Garmin = _load_garmin_client()

def load_existing_csv(output_file):
    """Load existing CSV file if it exists and return as list of dicts."""
    if not os.path.exists(output_file):
        return []
    
    try:
        with open(output_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)
    except Exception as e:
        logger.warning(f"Could not load existing CSV: {e}")
        return []

def get_activity_date(activity):
    """Extract date from activity for health metrics lookup."""
    if 'startTimeLocal' in activity and activity['startTimeLocal']:
        try:
            date_str = str(activity['startTimeLocal'])
            # Handle various date formats
            if 'T' in date_str:
                # ISO format with time
                dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0].split('.')[0])
            else:
                # Just date
                dt = datetime.datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d')
            return dt.date().isoformat()
        except Exception as e:
            logger.debug(f"Could not parse date from {activity.get('startTimeLocal')}: {e}")
    return None

def has_health_metrics(activity):
    """Check if activity already has health metrics data."""
    return (activity.get('sleepDuration') and activity.get('stressAvg'))

def has_training_readiness(activity):
    """Check if activity already has training readiness data."""
    return ('trainingReadinessScore' in activity and activity['trainingReadinessScore']) or \
           ('trainingStatus' in activity and activity['trainingStatus'])

def has_gps_track(activity):
    """Check if activity already has GPS track downloaded."""
    return 'gpsTrackFile' in activity and activity['gpsTrackFile']

def get_health_metrics(client, date):
    """Fetch health metrics for a specific date."""
    try:
        health_data = {}
        
        # Sleep data
        try:
            sleep_data = client.get_sleep_data(date)
            # Handle different sleep data structures
            if sleep_data:
                if 'dailySleepDTO' in sleep_data:
                    sleep = sleep_data['dailySleepDTO']
                    health_data['sleepDuration'] = sleep.get('sleepTimeSeconds', 0) / 3600 if sleep.get('sleepTimeSeconds') else None
                    health_data['sleepDeepDuration'] = sleep.get('deepSleepSeconds', 0) / 3600 if sleep.get('deepSleepSeconds') else None
                    health_data['sleepLightDuration'] = sleep.get('lightSleepSeconds', 0) / 3600 if sleep.get('lightSleepSeconds') else None
                    health_data['sleepRemDuration'] = sleep.get('remSleepSeconds', 0) / 3600 if sleep.get('remSleepSeconds') else None
                    health_data['sleepAwakeDuration'] = sleep.get('awakeSleepSeconds', 0) / 3600 if sleep.get('awakeSleepSeconds') else None
                    # Try to get sleep quality from sleepScores
                    if 'sleepScores' in sleep and 'overall' in sleep['sleepScores']:
                        health_data['sleepQuality'] = sleep['sleepScores']['overall'].get('value', None)
                    else:
                        health_data['sleepQuality'] = sleep.get('sleepQualityScore', None)
                elif 'sleep' in sleep_data: # Legacy or alternative format
                    sleep = sleep_data['sleep']
                    health_data['sleepDuration'] = sleep.get('sleepTimeSeconds', 0) / 3600 if sleep.get('sleepTimeSeconds') else None
                    health_data['sleepDeepDuration'] = sleep.get('deepSleepSeconds', 0) / 3600 if sleep.get('deepSleepSeconds') else None
                    health_data['sleepLightDuration'] = sleep.get('lightSleepSeconds', 0) / 3600 if sleep.get('lightSleepSeconds') else None
                    health_data['sleepRemDuration'] = sleep.get('remSleepSeconds', 0) / 3600 if sleep.get('remSleepSeconds') else None
                    health_data['sleepAwakeDuration'] = sleep.get('awakeSleepSeconds', 0) / 3600 if sleep.get('awakeSleepSeconds') else None
                    health_data['sleepQuality'] = sleep.get('sleepQuality', None)
        except Exception as e:
            logger.debug(f"Could not fetch sleep data for {date}: {e}")
        
        # Stress data
        try:
            stress_data = client.get_stress_data(date)
            if stress_data:
                # Check if it's a list or dict
                if isinstance(stress_data, list) and stress_data:
                    stress_data = stress_data[0]
                
                health_data['stressAvg'] = stress_data.get('avgStressLevel', stress_data.get('averageStressLevel'))
                health_data['stressMax'] = stress_data.get('maxStressLevel', None)
                health_data['stressRestDuration'] = stress_data.get('restStressDuration', None)
                health_data['stressLowDuration'] = stress_data.get('lowStressDuration', None)
                health_data['stressMediumDuration'] = stress_data.get('mediumStressDuration', None)
                health_data['stressHighDuration'] = stress_data.get('highStressDuration', None)
        except Exception as e:
            logger.debug(f"Could not fetch stress data for {date}: {e}")
        
        # Body battery
        try:
            body_battery = client.get_body_battery(date)
            if body_battery:
                # API returns a list of dicts
                if isinstance(body_battery, list) and body_battery:
                    body_battery = body_battery[0]
                
                # Try to get summary values first
                health_data['bodyBatteryAvg'] = body_battery.get('averageBodyBattery', None)
                health_data['bodyBatteryMax'] = body_battery.get('maxBodyBattery', None)
                health_data['bodyBatteryMin'] = body_battery.get('minBodyBattery', None)
                
                # If summary values are missing, calculate from values array
                if health_data['bodyBatteryMax'] is None and 'bodyBatteryValuesArray' in body_battery:
                    values = [v[1] for v in body_battery['bodyBatteryValuesArray'] if v[1] is not None]
                    if values:
                        health_data['bodyBatteryMax'] = max(values)
                        health_data['bodyBatteryMin'] = min(values)
                        health_data['bodyBatteryAvg'] = sum(values) / len(values)
                    else:
                        logger.info(f"Body battery values array empty for {date}")
                elif health_data['bodyBatteryMax'] is None:
                    logger.info(f"No body battery summary or values array for {date}. Keys: {list(body_battery.keys())}")
        except Exception as e:
            logger.info(f"Could not fetch body battery for {date}: {e}")
        
        # Resting heart rate
        try:
            rhr = client.get_rhr_day(date)
            if rhr:
                # API returns nested structure: allMetrics -> metricsMap -> WELLNESS_RESTING_HEART_RATE -> [0] -> value
                if 'allMetrics' in rhr and 'metricsMap' in rhr['allMetrics']:
                    metrics = rhr['allMetrics']['metricsMap']
                    if 'WELLNESS_RESTING_HEART_RATE' in metrics and metrics['WELLNESS_RESTING_HEART_RATE']:
                        health_data['restingHeartRate'] = metrics['WELLNESS_RESTING_HEART_RATE'][0].get('value', None)
                elif 'value' in rhr: # Fallback
                    health_data['restingHeartRate'] = rhr.get('value', None)
        except Exception as e:
            logger.debug(f"Could not fetch RHR for {date}: {e}")
        
        # Daily steps
        try:
            steps_data = client.get_daily_steps(date, date)
            if steps_data:
                health_data['dailySteps'] = steps_data[-1].get('totalSteps', None)
        except Exception as e:
            logger.debug(f"Could not fetch daily steps for {date}: {e}")
        
        return health_data
    except Exception as e:
        logger.debug(f"Error fetching health metrics for {date}: {e}")
        return {}

def get_training_readiness(client, date):
    """Fetch training readiness data for a specific date."""
    try:
        readiness_data = {}
        
        # Training readiness
        try:
            readiness = client.get_training_readiness(date)
            if readiness:
                # API returns a list of dicts
                if isinstance(readiness, list) and readiness:
                    readiness = readiness[0]
                
                readiness_data['trainingReadinessScore'] = readiness.get('score', None) # Key is 'score'
                readiness_data['trainingReadiness'] = readiness.get('level', None) # Key is 'level'
        except Exception as e:
            logger.debug(f"Could not fetch training readiness for {date}: {e}")
        
        # Training status
        try:
            status = client.get_training_status()
            if status:
                readiness_data['trainingStatus'] = status.get('status', None)
                readiness_data['trainingStatusText'] = status.get('statusText', None)
        except Exception as e:
            logger.debug(f"Could not fetch training status: {e}")
        
        return readiness_data
    except Exception as e:
        logger.debug(f"Error fetching training readiness for {date}: {e}")
        return {}

def download_gps_track(client, activity_id, gps_dir):
    """Download GPS track for an activity and return file path."""
    try:
        os.makedirs(gps_dir, exist_ok=True)
        
        # Try to download as GPX
        try:
            gpx_data = client.download_activity(activity_id, Garmin.ActivityDownloadFormat.GPX)
            if gpx_data:
                gpx_file = os.path.join(gps_dir, f"{activity_id}.gpx")
                with open(gpx_file, 'wb') as f:
                    f.write(gpx_data)
                return gpx_file
        except:
            pass
        
        # Try TCX as fallback
        try:
            tcx_data = client.download_activity(activity_id, Garmin.ActivityDownloadFormat.TCX)
            if tcx_data:
                tcx_file = os.path.join(gps_dir, f"{activity_id}.tcx")
                with open(tcx_file, 'wb') as f:
                    f.write(tcx_data)
                return tcx_file
        except:
            pass
        
        return None
    except Exception as e:
        logger.debug(f"Could not download GPS track for activity {activity_id}: {e}")
        return None

def enhance_activity(client, activity, needs_health, needs_readiness, needs_gps, activity_date, activity_id, gps_tracks_dir, output_file, existing):
    """Enhance a single activity with additional data using the provided client."""
    try:
        enhanced_activity = activity.copy()
        
        # Fetch health metrics if needed
        if needs_health and activity_date:
            try:
                health_metrics = get_health_metrics(client, activity_date)
                enhanced_activity.update(health_metrics)
            except Exception as e:
                logger.debug(f"Could not fetch health metrics for {activity_date}: {e}")
        
        # Fetch training readiness if needed
        if needs_readiness and activity_date:
            try:
                readiness = get_training_readiness(client, activity_date)
                enhanced_activity.update(readiness)
            except Exception as e:
                logger.debug(f"Could not fetch training readiness for {activity_date}: {e}")
        
        # Download GPS track if needed
        if needs_gps and activity_id:
            try:
                gps_file = download_gps_track(client, activity_id, gps_tracks_dir)
                if gps_file:
                    enhanced_activity['gpsTrackFile'] = os.path.relpath(gps_file, os.path.dirname(output_file))
                else:
                    enhanced_activity['gpsTrackFile'] = None
            except Exception as e:
                logger.debug(f"Could not download GPS track for {activity_id}: {e}")
                enhanced_activity['gpsTrackFile'] = None
        
        # Merge with existing data if updating
        if existing:
            for key, value in existing.items():
                if key not in enhanced_activity or not enhanced_activity[key]:
                    enhanced_activity[key] = value
        
        return enhanced_activity
    except Exception as e:
        logger.error(f"Error enhancing activity {activity_id}: {e}")
        # Return existing or base activity on error
        return existing if existing else activity

def export_garmin_data(username, password, output_file, gps_tracks_dir="gps_tracks", start_date="2000-01-01"):
    """
    Fetches activities from Garmin Connect and saves them to a CSV file.
    Includes health metrics, training readiness, and GPS tracks.
    Only downloads missing data (delta updates).
    
    Args:
        username: Garmin Connect username
        password: Garmin Connect password
        output_file: Path to output CSV file
        gps_tracks_dir: Directory for GPS track files (default: "gps_tracks")
        start_date: Start date for fetching activities (default: "2000-01-01")
    """
    try:
        logger.info("Authenticating with Garmin Connect...")
        client = Garmin(username, password)
        client.login()
        logger.info("Authentication successful.")

        # Load existing data
        existing_activities = load_existing_csv(output_file)
        existing_activity_ids = {a.get('activityId') for a in existing_activities if a.get('activityId')}
        logger.info(f"Found {len(existing_activities)} existing activities in CSV.")

        # Get activities for a wide range
        # start_date is now passed as an argument
        end_date = datetime.date.today().isoformat()
        
        logger.info(f"Fetching activity list from {start_date} to {end_date}...")
        activities = client.get_activities_by_date(start_date, end_date)
        logger.info(f"Found {len(activities)} total activities from Garmin.")

        # Create a map of existing activities by ID for easy lookup
        existing_map = {a.get('activityId'): a for a in existing_activities if a.get('activityId')}
        
        # Separate activities that need processing from those that are complete
        activities_to_process = []
        enhanced_activities = []
        new_count = 0
        updated_count = 0
        
        for activity in activities:
            activity_id = str(activity.get('activityId', ''))
            
            # Check if this is a new activity or needs updates
            if activity_id in existing_map:
                # Existing activity - check what's missing
                existing = existing_map[activity_id]
                needs_health = not has_health_metrics(existing)
                needs_readiness = not has_training_readiness(existing)
                needs_gps = not has_gps_track(existing) and activity.get('hasPolyline', False)
                
                if needs_health or needs_readiness or needs_gps:
                    updated_count += 1
                    activity_date = get_activity_date(activity)
                    activities_to_process.append((
                        activity, needs_health, needs_readiness, needs_gps,
                        activity_date, activity_id, existing
                    ))
                else:
                    # Use existing data as-is
                    enhanced_activities.append(existing)
            else:
                # New activity
                new_count += 1
                activity_date = get_activity_date(activity)
                activities_to_process.append((
                    activity, True, True, activity.get('hasPolyline', False),
                    activity_date, activity_id, None
                ))
        
        logger.info(f"Processing {len(activities_to_process)} activities ({new_count} new, {updated_count} updates)...")
        logger.info("Using sequential processing to avoid authentication issues.")
        
        # Process activities sequentially
        processed_activities = []
        completed = 0
        
        for args in activities_to_process:
            activity, needs_health, needs_readiness, needs_gps, activity_date, activity_id, existing = args
            try:
                enhanced = enhance_activity(
                    client, activity, needs_health, needs_readiness, needs_gps,
                    activity_date, activity_id, gps_tracks_dir, output_file, existing
                )
                processed_activities.append(enhanced)
                completed += 1
                if completed % 5 == 0:
                    logger.info(f"Processed {completed}/{len(activities_to_process)} activities...")
            except Exception as e:
                logger.error(f"Error processing activity {activity_id}: {e}")
                # Keep existing if available
                if existing:
                    processed_activities.append(existing)
        
        # Combine existing and processed activities
        enhanced_activities.extend(processed_activities)
        
        logger.info(f"Processed {new_count} new activities and updated {updated_count} existing activities.")
        
        # Collect all unique keys for CSV headers
        keys = set()
        for activity in enhanced_activities:
            keys.update(activity.keys())
        fieldnames = sorted(list(keys))

        logger.info(f"Saving to {output_file}...")
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(enhanced_activities)
        
        logger.info(f"Export complete. Total activities: {len(enhanced_activities)}")
        logger.info(f"New: {new_count}, Updated: {updated_count}, Unchanged: {len(enhanced_activities) - new_count - updated_count}")

    except Exception as e:
        logger.error(f"Error during Garmin export: {e}")
        raise

def fetch_daily_health(client, date_str, existing_record):
    """Fetch daily health data for a specific date using the provided client."""
    try:
        daily_record = {'date': date_str}
        
        # Fetch health metrics
        try:
            health_metrics = get_health_metrics(client, date_str)
            daily_record.update(health_metrics)
        except Exception as e:
            logger.debug(f"Could not fetch health metrics for {date_str}: {e}")
        
        # Fetch training readiness
        try:
            readiness = get_training_readiness(client, date_str)
            daily_record.update(readiness)
        except Exception as e:
            logger.debug(f"Could not fetch training readiness for {date_str}: {e}")
        
        # Merge with existing data if updating
        if existing_record:
            for key, value in existing_record.items():
                if key not in daily_record or not daily_record[key]:
                    daily_record[key] = value
        
        return daily_record
    except Exception as e:
        logger.error(f"Error fetching data for {date_str}: {e}")
        # Return existing record or empty record on error
        return existing_record if existing_record else {'date': date_str}

def export_daily_health_data(username, password, output_file, start_date="2000-01-01", end_date=None):
    """
    Export daily health metrics for all dates (not just activity days).
    This includes sleep, stress, body battery, resting heart rate, and steps for every day.
    
    Args:
        username: Garmin Connect username
        password: Garmin Connect password
        output_file: Path to output CSV file
        start_date: Start date in YYYY-MM-DD format (default: "2000-01-01")
        end_date: End date in YYYY-MM-DD format (default: today)
    """
    if end_date is None:
        end_date = datetime.date.today().isoformat()
    
    try:
        logger.info("Authenticating with Garmin Connect...")
        client = Garmin(username, password)
        client.login()
        logger.info("Authentication successful.")

        # Load existing data if it exists
        existing_data = load_existing_csv(output_file)
        existing_dates = {row.get('date') for row in existing_data if row.get('date')}
        logger.info(f"Found {len(existing_data)} existing daily records in CSV.")

        # Parse date range
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Generate all dates in range
        all_dates = []
        current_date = start
        while current_date <= end:
            all_dates.append(current_date.isoformat())
            current_date += datetime.timedelta(days=1)
        
        logger.info(f"Fetching health data for {len(all_dates)} days from {start_date} to {end_date}...")
        logger.info("Using sequential processing to avoid authentication issues.")
        
        # Create a map of existing data by date
        existing_map = {row.get('date'): row for row in existing_data if row.get('date')}
        
        # Separate dates that need fetching from those that are complete
        dates_to_fetch = []
        daily_records = []
        skipped_count = 0
        
        for date_str in all_dates:
            if date_str in existing_map:
                existing = existing_map[date_str]
                if has_health_metrics(existing):
                    # Use existing data
                    daily_records.append(existing)
                    skipped_count += 1
                else:
                    # Needs update
                    dates_to_fetch.append((date_str, existing))
            else:
                # New date
                dates_to_fetch.append((date_str, None))
        
        new_count = len([d for d in dates_to_fetch if d[1] is None])
        updated_count = len([d for d in dates_to_fetch if d[1] is not None])
        
        logger.info(f"Skipping {skipped_count} dates with existing data.")
        logger.info(f"Fetching {len(dates_to_fetch)} dates ({new_count} new, {updated_count} updates)...")
        
        # Process dates sequentially
        fetched_records = []
        completed = 0
        
        for date_str, existing_record in dates_to_fetch:
            try:
                record = fetch_daily_health(client, date_str, existing_record)
                fetched_records.append(record)
                completed += 1
                if completed % 10 == 0:
                    logger.info(f"Fetched {completed}/{len(dates_to_fetch)} dates...")
            except Exception as e:
                logger.error(f"Error processing {date_str}: {e}")
                fetched_records.append({'date': date_str})
        
        # Combine existing and fetched records, sort by date
        daily_records.extend(fetched_records)
        daily_records.sort(key=lambda x: x.get('date', ''))
        
        logger.info(f"Processed {new_count} new dates and updated {updated_count} existing dates.")
        
        # Collect all unique keys for CSV headers
        keys = set()
        for record in daily_records:
            keys.update(record.keys())
        fieldnames = sorted(list(keys))
        # Ensure 'date' is first
        if 'date' in fieldnames:
            fieldnames.remove('date')
            fieldnames.insert(0, 'date')

        logger.info(f"Saving to {output_file}...")
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(daily_records)
        
        logger.info(f"Daily health data export complete. Total records: {len(daily_records)}")
        logger.info(f"New: {new_count}, Updated: {updated_count}, Unchanged: {skipped_count}")

    except Exception as e:
        logger.error(f"Error during daily health data export: {e}")
        raise
