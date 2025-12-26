import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- Configuration ---
st.set_page_config(page_title="Garmin Analytics Dashboard", layout="wide")

# --- Title ---
st.title("Garmin Analytics Dashboard")

# --- Data Loading Functions ---
@st.cache_data
def load_activity_data(file):
    try:
        df = pd.read_csv(file)
        
        # Convert startTimeLocal to datetime
        if 'startTimeLocal' in df.columns:
            df['startTimeLocal'] = pd.to_datetime(df['startTimeLocal'])
        else:
            st.error("Activity CSV must contain 'startTimeLocal' column.")
            return None

        # Ensure numeric columns (fill NaNs with 0)
        numeric_cols = ['duration', 'calories', 'distance', 'averageHR']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0 

        # Categorization
        def categorize_activity(name):
            if not isinstance(name, str):
                return "Other"
            name_lower = name.lower()
            if "run" in name_lower:
                return "Running"
            elif "cycle" in name_lower or "cycling" in name_lower or "bike" in name_lower:
                return "Cycling"
            elif "strength" in name_lower or "weight" in name_lower:
                return "Strength"
            elif "yoga" in name_lower:
                return "Yoga"
            elif "swim" in name_lower:
                return "Swimming"
            elif "walk" in name_lower:
                return "Walking"
            else:
                return "Other"

        if 'activityName' in df.columns:
            df['Category'] = df['activityName'].apply(categorize_activity)
        else:
            df['Category'] = "Other"
            
        return df
    except Exception as e:
        st.error(f"Error loading activity data: {e}")
        return None

@st.cache_data
def load_health_data(file):
    try:
        df = pd.read_csv(file)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        else:
            st.error("Health CSV must contain 'date' column.")
            return None
            
        # Ensure numeric columns
        numeric_cols = ['sleepDuration', 'sleepQuality', 'stressAvg', 'bodyBatteryMax', 'restingHeartRate', 'dailySteps']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading health data: {e}")
        return None

# --- Sidebar File Uploaders ---
st.sidebar.header("Data Upload")
activity_file = st.sidebar.file_uploader("Upload Activities (garmin_stats.csv)", type=["csv"])
health_file = st.sidebar.file_uploader("Upload Health Data (garmin_daily_health.csv)", type=["csv"])

# --- Tabs ---
tab1, tab2 = st.tabs(["Activities", "Health"])

# --- TAB 1: ACTIVITIES ---
with tab1:
    if activity_file is not None:
        df = load_activity_data(activity_file)

        if df is not None:
            # --- Filters ---
            st.subheader("Activity Filters")
            col_f1, col_f2 = st.columns(2)
            
            # Date Range
            min_date = df['startTimeLocal'].min().date()
            max_date = df['startTimeLocal'].max().date()
            
            with col_f1:
                start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="act_start")
            with col_f2:
                end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="act_end")
            
            if start_date > end_date:
                st.error("⚠️ Start date must be before or equal to end date")
                start_date, end_date = min_date, max_date
            
            # Activity Type
            activity_types = ["All"] + sorted(df['Category'].unique().tolist())
            selected_activity_type = st.selectbox("Activity Type", activity_types)
            
            # Apply Filters
            mask = (df['startTimeLocal'].dt.date >= start_date) & (df['startTimeLocal'].dt.date <= end_date)
            if selected_activity_type != "All":
                mask = mask & (df['Category'] == selected_activity_type)
                
            filtered_df = df[mask].copy()
            
            st.markdown("---")
            
            # --- Key Metrics ---
            st.subheader("Key Metrics")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            total_activities = len(filtered_df)
            total_duration_seconds = filtered_df['duration'].sum()
            hours = int(total_duration_seconds // 3600)
            minutes = int((total_duration_seconds % 3600) // 60)
            total_duration_str = f"{hours}h {minutes}m"
            total_distance_km = filtered_df['distance'].sum() / 1000.0
            total_calories = filtered_df['calories'].sum()
            avg_hr = filtered_df['averageHR'].mean()
            
            col1.metric("Total Activities", total_activities)
            col2.metric("Total Duration", total_duration_str)
            col3.metric("Total Distance", f"{total_distance_km:.2f} km")
            col4.metric("Total Calories", f"{total_calories:,.0f}")
            col5.metric("Avg Heart Rate", f"{avg_hr:.0f} bpm")
            
            st.markdown("---")
            
            # --- Highlights ---
            if not filtered_df.empty:
                st.subheader("Highlights")
                highlights = []
                
                # Helper to format highlight
                def add_highlight(title, value, idx, df, col_name, suffix=""):
                    activity = df.loc[idx, 'activityName'] if 'activityName' in df.columns else "Activity"
                    date = df.loc[idx, 'startTimeLocal'].strftime('%Y-%m-%d')
                    highlights.append({'title': title, 'value': f"{value}{suffix}", 'detail': f"{activity} on {date}"})

                # Longest Session
                if 'duration' in filtered_df.columns:
                    idx = filtered_df['duration'].idxmax()
                    val = filtered_df.loc[idx, 'duration']
                    h, m = int(val // 3600), int((val % 3600) // 60)
                    add_highlight('Longest Session', f"{h}h {m}m", idx, filtered_df, 'duration')

                # Longest Run
                if 'distance' in filtered_df.columns:
                    run_df = filtered_df[filtered_df['Category'] == 'Running']
                    if not run_df.empty:
                        idx = run_df['distance'].idxmax()
                        val = run_df.loc[idx, 'distance'] / 1000.0
                        add_highlight('Longest Run', f"{val:.2f}", idx, run_df, 'distance', " km")

                # Highest HR
                if 'maxHR' in filtered_df.columns:
                    idx = filtered_df['maxHR'].idxmax()
                    val = filtered_df.loc[idx, 'maxHR']
                    add_highlight('Highest HR', f"{val:.0f}", idx, filtered_df, 'maxHR', " bpm")
                
                # Display Highlights
                if highlights:
                    cols = st.columns(min(len(highlights), 4))
                    for i, h in enumerate(highlights[:4]):
                        with cols[i]:
                            st.metric(h['title'], h['value'])
                            st.caption(h['detail'])
            
            st.markdown("---")
            
            # --- Visualizations ---
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                st.subheader("Volume Trends")
                if not filtered_df.empty:
                    filtered_df['Month'] = filtered_df['startTimeLocal'].dt.to_period('M').astype(str)
                    monthly_stats = filtered_df.groupby('Month').agg({'duration': 'sum'}).reset_index()
                    monthly_stats['duration_hours'] = monthly_stats['duration'] / 3600
                    fig = px.bar(monthly_stats, x='Month', y='duration_hours', title="Monthly Duration (Hours)")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col_viz2:
                st.subheader("Activity Mix")
                if not filtered_df.empty:
                    fig = px.pie(filtered_df, names='Category', title="Activity Distribution", hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)

            # --- Raw Data ---
            with st.expander("View Raw Activity Data"):
                st.dataframe(filtered_df.sort_values('startTimeLocal', ascending=False), use_container_width=True)

    else:
        st.info("Please upload `garmin_stats.csv` to view activity analytics.")

# --- TAB 2: HEALTH ---
with tab2:
    if health_file is not None:
        hdf = load_health_data(health_file)
        
        if hdf is not None:
            # --- Filters ---
            st.subheader("Health Filters")
            min_h_date = hdf['date'].min().date()
            max_h_date = hdf['date'].max().date()
            
            # Default to last 30 days
            default_start = max_h_date - datetime.timedelta(days=30)
            if default_start < min_h_date:
                default_start = min_h_date
            
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                start_h_date = st.date_input("Start Date", default_start, min_value=min_h_date, max_value=max_h_date, key="health_start")
            with col_h2:
                end_h_date = st.date_input("End Date", max_h_date, min_value=min_h_date, max_value=max_h_date, key="health_end")
            
            # Filter Data
            mask_h = (hdf['date'].dt.date >= start_h_date) & (hdf['date'].dt.date <= end_h_date)
            filtered_hdf = hdf[mask_h].copy()
            
            st.markdown("---")
            
            # --- Key Metrics ---
            st.subheader("Average Health Metrics")
            hc1, hc2, hc3, hc4, hc5 = st.columns(5)
            
            avg_sleep = filtered_hdf['sleepDuration'].mean()
            avg_stress = filtered_hdf['stressAvg'].mean()
            avg_bb = filtered_hdf['bodyBatteryMax'].mean()
            avg_rhr = filtered_hdf['restingHeartRate'].mean()
            avg_steps = filtered_hdf['dailySteps'].mean()
            
            hc1.metric("Avg Sleep", f"{avg_sleep:.1f} hrs" if pd.notnull(avg_sleep) else "-")
            hc2.metric("Avg Stress", f"{avg_stress:.0f}" if pd.notnull(avg_stress) else "-")
            hc3.metric("Avg Body Battery (Max)", f"{avg_bb:.0f}" if pd.notnull(avg_bb) else "-")
            hc4.metric("Avg RHR", f"{avg_rhr:.0f} bpm" if pd.notnull(avg_rhr) else "-")
            hc5.metric("Avg Steps", f"{avg_steps:,.0f}" if pd.notnull(avg_steps) else "-")
            
            st.markdown("---")
            
            # --- Insights ---
            st.subheader("Insights")
            ic1, ic2, ic3 = st.columns(3)
            
            # Best Sleep
            if 'sleepQuality' in filtered_hdf.columns and filtered_hdf['sleepQuality'].notnull().any():
                best_sleep_idx = filtered_hdf['sleepQuality'].idxmax()
                best_sleep_val = filtered_hdf.loc[best_sleep_idx, 'sleepQuality']
                best_sleep_date = filtered_hdf.loc[best_sleep_idx, 'date'].strftime('%Y-%m-%d')
                ic1.metric("Best Sleep Score", f"{best_sleep_val:.0f}", f"on {best_sleep_date}")
            else:
                ic1.info("No sleep quality data")
            
            # Lowest Stress
            if 'stressAvg' in filtered_hdf.columns and filtered_hdf['stressAvg'].notnull().any():
                # Filter out 0 or -1 if they exist as errors, though usually null
                valid_stress = filtered_hdf[filtered_hdf['stressAvg'] > 0]
                if not valid_stress.empty:
                    low_stress_idx = valid_stress['stressAvg'].idxmin()
                    low_stress_val = valid_stress.loc[low_stress_idx, 'stressAvg']
                    low_stress_date = valid_stress.loc[low_stress_idx, 'date'].strftime('%Y-%m-%d')
                    ic2.metric("Lowest Stress Day", f"{low_stress_val:.0f}", f"on {low_stress_date}", delta_color="inverse")
                else:
                    ic2.info("No valid stress data")
            else:
                ic2.info("No stress data")

            # Highest Steps
            if 'dailySteps' in filtered_hdf.columns and filtered_hdf['dailySteps'].notnull().any():
                max_steps_idx = filtered_hdf['dailySteps'].idxmax()
                max_steps_val = filtered_hdf.loc[max_steps_idx, 'dailySteps']
                max_steps_date = filtered_hdf.loc[max_steps_idx, 'date'].strftime('%Y-%m-%d')
                ic3.metric("Most Active Day", f"{max_steps_val:,.0f} steps", f"on {max_steps_date}")
            else:
                ic3.info("No steps data")

            st.markdown("---")

            # --- Visualizations ---
            st.subheader("Health Trends")
            
            # Sleep Trend
            if 'sleepDuration' in filtered_hdf.columns and filtered_hdf['sleepDuration'].notnull().any():
                color_col = 'sleepQuality' if 'sleepQuality' in filtered_hdf.columns and filtered_hdf['sleepQuality'].notnull().any() else None
                fig_sleep = px.bar(filtered_hdf, x='date', y='sleepDuration', 
                                   title="Daily Sleep Duration (Hours)", 
                                   color=color_col, 
                                   color_continuous_scale='RdBu')
                if not color_col:
                    fig_sleep.update_traces(marker_color='#1f77b4')
                st.plotly_chart(fig_sleep, use_container_width=True)
            else:
                st.info("No sleep duration data available.")
            
            # Stress vs Body Battery
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                metrics_to_plot = []
                if 'stressAvg' in filtered_hdf.columns and filtered_hdf['stressAvg'].notnull().any():
                    metrics_to_plot.append('stressAvg')
                if 'bodyBatteryMax' in filtered_hdf.columns and filtered_hdf['bodyBatteryMax'].notnull().any():
                    metrics_to_plot.append('bodyBatteryMax')
                
                if metrics_to_plot:
                    fig_stress = px.line(filtered_hdf, x='date', y=metrics_to_plot, 
                                         title="Stress vs Body Battery",
                                         labels={'value': 'Score', 'variable': 'Metric'})
                    st.plotly_chart(fig_stress, use_container_width=True)
                else:
                    st.info("No Stress or Body Battery data available.")
            
            with col_v2:
                if 'restingHeartRate' in filtered_hdf.columns and filtered_hdf['restingHeartRate'].notnull().any():
                    fig_rhr = px.line(filtered_hdf, x='date', y='restingHeartRate', 
                                      title="Resting Heart Rate Trend",
                                      markers=True)
                    fig_rhr.update_traces(line_color='red')
                    st.plotly_chart(fig_rhr, use_container_width=True)
                else:
                    st.info("No Resting Heart Rate data available.")

            # --- Raw Data ---
            with st.expander("View Raw Health Data"):
                st.dataframe(filtered_hdf.sort_values('date', ascending=False), use_container_width=True)
                
    else:
        st.info("Please upload `garmin_daily_health.csv` to view health analytics.")
