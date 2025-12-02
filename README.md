# Garmin Export & Analytics Dashboard

A comprehensive tool for exporting Garmin Connect activity data and visualizing it through an interactive dashboard. This project allows you to download your complete Garmin activity history, including health metrics, training readiness, and GPS tracks, with intelligent incremental updates that only download missing data.

## Features

### 📊 Data Export
- **Complete Activity History**: Export all activities from Garmin Connect to CSV
- **Health Metrics**: Sleep, stress, body battery, resting heart rate, and daily steps
- **Training Readiness**: Training readiness scores and status
- **GPS Tracks**: Download GPS tracks (GPX/TCX format) for activities with location data
- **Incremental Updates**: Only downloads missing data on subsequent runs (delta updates)

### 📈 Interactive Dashboard
- **Key Metrics**: Total activities, duration, distance, calories, and average heart rate
- **Highlights**: Personal records including longest run, highest HR, fastest speed, most elevation, etc.
- **Visualizations**:
  - Volume trends over time
  - Activity mix (pie chart)
  - Intensity vs duration scatter plots
  - Year-over-year comparisons
  - Month-by-month comparisons with filtering
- **Advanced Filtering**: Filter by date range and activity type
- **Raw Data Table**: View and export filtered activity data

## Installation

### Prerequisites
- Python 3.7 or higher
- Garmin Connect account

### Setup

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Usage

### Exporting Data

#### Basic Export
Run the main export script:
```bash
python main.py
```

You'll be prompted to choose what to export:
1. **Activities with health metrics** - Exports activities with health data for activity days only
2. **Daily health data** - Exports health metrics for ALL days (including rest days without activities)
3. **Both** - Exports both datasets

**Activities Export** (`garmin_stats.csv`):
- Fetches all activities from Garmin Connect
- Downloads health metrics for each activity date
- Downloads training readiness data
- Downloads GPS tracks (if available)

**Daily Health Data Export** (`garmin_daily_health.csv`):
- Exports health metrics for every day in the specified date range
- Includes sleep, stress, body battery, resting heart rate, and steps
- Includes training readiness scores
- Useful for analyzing rest days and overall health trends

#### Advanced Export (Programmatic)

**Export Activities:**
```python
from garmin_export import export_garmin_data

export_garmin_data(
    username="your_username",
    password="your_password",
    output_file="garmin_stats.csv",
    gps_tracks_dir="gps_tracks"  # Optional: directory for GPS track files
)
```

**Export Daily Health Data (All Days):**
```python
from garmin_export import export_daily_health_data

export_daily_health_data(
    username="your_username",
    password="your_password",
    output_file="garmin_daily_health.csv",
    start_date="2000-01-01",  # Optional: start date
    end_date=None  # Optional: end date (default: today)
)
```

#### Incremental Updates
Both export functions support incremental updates and automatically detect existing data:

**Activities Export** only downloads:
- New activities not in the CSV
- Missing health metrics for existing activities
- Missing training readiness for existing activities
- Missing GPS tracks for existing activities

**Daily Health Data Export** only downloads:
- New dates not in the CSV
- Missing health metrics for existing dates
- Missing training readiness for existing dates

This makes subsequent runs much faster and API-friendly.

### Running the Dashboard

1. **Start the Streamlit dashboard**:
```bash
streamlit run dashboard.py
```

2. **Open your browser** to the URL shown (typically `http://localhost:8501`)

3. **Upload your CSV file** using the file uploader at the top

4. **Explore your data**:
   - Use sidebar filters to narrow down by date range and activity type
   - View key metrics and personal records
   - Explore visualizations and trends
   - Export filtered data from the raw data table

## Project Structure

```
GarminExport/
├── main.py                 # Main entry point for data export
├── garmin_export.py         # Core export functionality with incremental updates
├── dashboard.py             # Streamlit dashboard application
├── inspect_data.py          # Utility script to inspect Garmin API data
├── requirements.txt         # Python dependencies
├── garmin_stats.csv         # Exported activity data (generated)
├── garmin_daily_health.csv  # Daily health metrics for all days (generated)
├── gps_tracks/              # GPS track files directory (generated)
└── README.md               # This file
```

## Data Exported

### Activity Data
- Basic info: Activity name, type, ID, dates/times
- Performance: Duration, distance, calories, pace, speed
- Heart rate: Average, max, time in zones
- Elevation: Gain, loss, min, max
- Power, cadence, stride length
- Training effect and load
- Location and device information

### Health Metrics
Available in both activity export and daily health export:
- **Sleep**: Duration, deep/light/REM/awake sleep, sleep quality
- **Stress**: Average, max, time in stress zones
- **Body Battery**: Average, max, min levels
- **Resting Heart Rate**: Daily RHR
- **Daily Steps**: Step count

**Note**: 
- Activity export includes health metrics for activity days only
- Daily health export includes health metrics for ALL days (including rest days)

### Training Readiness
- Training readiness score
- Training status and status text

### GPS Tracks (New)
- GPS track files downloaded as GPX (or TCX) format
- File paths stored in CSV column `gpsTrackFile`
- Only downloaded for activities with GPS data

## Dashboard Features

### Key Metrics
Displays aggregate statistics for filtered activities:
- Total activities count
- Total duration (hours and minutes)
- Total distance (km)
- Total calories burned
- Average heart rate

### Highlights Section
Shows personal records and achievements:
- **Longest Session**: Longest training session by duration
- **Longest Run**: Longest run by distance (running activities only)
- **Highest HR**: Maximum heart rate achieved
- **Fastest Speed**: Highest speed recorded
- **Most Elevation**: Greatest elevation gain
- **Most Calories**: Highest calorie burn in a single session
- **Longest Distance**: Longest distance overall

Each highlight shows the activity name and date.

### Visualizations

1. **Volume Trends**: Monthly duration totals (bar chart)
2. **Activity Mix**: Distribution of activities by category (pie chart)
3. **Intensity vs Duration**: Scatter plot showing heart rate vs duration (colored by category, sized by calories)
4. **Year-over-Year Comparison**: Line chart comparing same months across different years
5. **Month-by-Month Comparison**: Grouped bar chart comparing selected months across years (with month filter)

### Filtering
- **Date Range**: Filter activities by start and end date
- **Activity Type**: Filter by activity category (Running, Cycling, Strength, etc.)
- Filters apply to all metrics, visualizations, and data tables

## Requirements

See `requirements.txt` for full list. Main dependencies:
- `garminconnect` - Garmin Connect API client
- `streamlit` - Dashboard framework
- `pandas` - Data manipulation
- `plotly` - Interactive visualizations

## Troubleshooting

### Export Issues

**Authentication Failed**
- Verify your Garmin Connect username and password
- Check if two-factor authentication is enabled (may require additional setup)

**Missing Data**
- Some activities may not have all metrics (e.g., indoor activities won't have GPS)
- Health metrics are fetched by date - if an activity date has no health data, those fields will be empty
- Training readiness may not be available for all dates

**Slow Downloads**
- GPS tracks can be large - be patient for activities with long routes
- The incremental update feature helps speed up subsequent runs

### Dashboard Issues

**CSV Upload Fails**
- Ensure the CSV has a `startTimeLocal` column
- Check that the file is a valid CSV format

**No Data Showing**
- Adjust date range filters - they may be too restrictive
- Check that your CSV file has data in the selected date range

**Visualizations Not Loading**
- Ensure required columns exist in your CSV
- Some visualizations require numeric data - check for missing values

## Privacy & Security

- Your Garmin credentials are only used for authentication and are not stored
- All data is stored locally in CSV files and GPS track files
- GPS tracks are stored in the `gps_tracks/` directory
- The dashboard runs locally and does not send data anywhere

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for personal use.

## Acknowledgments

- Built using the [garminconnect](https://github.com/cyberjunky/python-garminconnect) Python library
- Dashboard powered by [Streamlit](https://streamlit.io/) and [Plotly](https://plotly.com/)

