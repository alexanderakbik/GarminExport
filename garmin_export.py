import logging
import os
import datetime
import csv
from garminconnect import Garmin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    return 'sleepDuration' in activity or 'stressAvg' in activity or 'bodyBatteryAvg' in activity

def has_training_readiness(activity):
    """Check if activity already has training readiness data."""
    return 'trainingReadinessScore' in activity or 'trainingStatus' in activity

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
            if sleep_data and 'sleep' in sleep_data:
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
                health_data['stressAvg'] = stress_data.get('averageStressLevel', None)
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
                health_data['bodyBatteryAvg'] = body_battery.get('averageBodyBattery', None)
                health_data['bodyBatteryMax'] = body_battery.get('maxBodyBattery', None)
                health_data['bodyBatteryMin'] = body_battery.get('minBodyBattery', None)
        except Exception as e:
            logger.debug(f"Could not fetch body battery for {date}: {e}")
        
        # Resting heart rate
        try:
            rhr = client.get_rhr_day(date)
            if rhr:
                health_data['restingHeartRate'] = rhr.get('value', None)
        except Exception as e:
            logger.debug(f"Could not fetch RHR for {date}: {e}")
        
        # Steps
        try:
            steps = client.get_daily_steps(date)
            if steps:
                health_data['dailySteps'] = steps.get('steps', None)
        except Exception as e:
            logger.debug(f"Could not fetch steps for {date}: {e}")
        
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
                readiness_data['trainingReadinessScore'] = readiness.get('trainingReadinessScore', None)
                readiness_data['trainingReadiness'] = readiness.get('trainingReadiness', None)
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

def export_garmin_data(username, password, output_file, gps_tracks_dir="gps_tracks"):
    """
    Fetches activities from Garmin Connect and saves them to a CSV file.
    Includes health metrics, training readiness, and GPS tracks.
    Only downloads missing data (delta updates).
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
        start_date = "2000-01-01"
        end_date = datetime.date.today().isoformat()
        
        logger.info(f"Fetching activity list from {start_date} to {end_date}...")
        activities = client.get_activities_by_date(start_date, end_date)
        logger.info(f"Found {len(activities)} total activities from Garmin.")

        # Create a map of existing activities by ID for easy lookup
        existing_map = {a.get('activityId'): a for a in existing_activities if a.get('activityId')}
        
        # Process activities and enhance with missing data
        enhanced_activities = []
        new_count = 0
        updated_count = 0
        
        for i, activity in enumerate(activities):
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
                    logger.info(f"Updating activity {activity_id} ({i+1}/{len(activities)})...")
                else:
                    # Use existing data as-is
                    enhanced_activities.append(existing)
                    continue
            else:
                # New activity
                new_count += 1
                logger.info(f"Processing new activity {activity_id} ({i+1}/{len(activities)})...")
                needs_health = True
                needs_readiness = True
                needs_gps = activity.get('hasPolyline', False)
            
            # Start with base activity data
            enhanced_activity = activity.copy()
            
            # Get activity date for health metrics
            activity_date = get_activity_date(activity)
            
            # Fetch health metrics if needed
            if needs_health and activity_date:
                logger.debug(f"Fetching health metrics for {activity_date}...")
                health_metrics = get_health_metrics(client, activity_date)
                enhanced_activity.update(health_metrics)
            
            # Fetch training readiness if needed
            if needs_readiness and activity_date:
                logger.debug(f"Fetching training readiness for {activity_date}...")
                readiness = get_training_readiness(client, activity_date)
                enhanced_activity.update(readiness)
            
            # Download GPS track if needed
            if needs_gps and activity_id:
                logger.debug(f"Downloading GPS track for activity {activity_id}...")
                gps_file = download_gps_track(client, activity_id, gps_tracks_dir)
                if gps_file:
                    enhanced_activity['gpsTrackFile'] = os.path.relpath(gps_file, os.path.dirname(output_file))
                else:
                    enhanced_activity['gpsTrackFile'] = None
            
            # If updating existing, merge with existing data
            if activity_id in existing_map:
                existing = existing_map[activity_id]
                # Preserve existing fields that might not be in new data
                for key, value in existing.items():
                    if key not in enhanced_activity or not enhanced_activity[key]:
                        enhanced_activity[key] = value
            
            enhanced_activities.append(enhanced_activity)
        
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
