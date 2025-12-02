import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- Configuration ---
st.set_page_config(page_title="Garmin Analytics Dashboard", layout="wide")

# --- Title ---
st.title("Garmin Analytics Dashboard")

# --- Data Loading Function ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file)
        
        # Convert startTimeLocal to datetime
        if 'startTimeLocal' in df.columns:
            df['startTimeLocal'] = pd.to_datetime(df['startTimeLocal'])
        else:
            st.error("CSV must contain 'startTimeLocal' column.")
            return None

        # Ensure numeric columns (fill NaNs with 0)
        numeric_cols = ['duration', 'calories', 'distance', 'averageHR']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0 # Create if missing to avoid errors

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
        st.error(f"Error loading data: {e}")
        return None

# --- File Uploader ---
uploaded_file = st.file_uploader("Upload your Garmin CSV file", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)

    if df is not None:
        # --- Sidebar Filters ---
        st.sidebar.header("Filters")
        
        # Date Range
        min_date = df['startTimeLocal'].min().date()
        max_date = df['startTimeLocal'].max().date()
        
        start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
        
        # Validate date range
        if start_date > end_date:
            st.sidebar.error("⚠️ Start date must be before or equal to end date")
            start_date = min_date
            end_date = max_date
        
        # Activity Type
        activity_types = ["All"] + sorted(df['Category'].unique().tolist())
        selected_activity_type = st.sidebar.selectbox("Activity Type", activity_types)
        
        # Apply Filters
        mask = (df['startTimeLocal'].dt.date >= start_date) & (df['startTimeLocal'].dt.date <= end_date)
        if selected_activity_type != "All":
            mask = mask & (df['Category'] == selected_activity_type)
            
        filtered_df = df[mask].copy()
        
        # Show filter summary
        if len(filtered_df) == 0:
            st.sidebar.warning("⚠️ No activities match the selected filters")
        elif len(filtered_df) != len(df):
            st.sidebar.success(f"Showing {len(filtered_df)} of {len(df)} activities")
        else:
            st.sidebar.info(f"Showing all {len(df)} activities")
        
        # --- Key Metrics ---
        st.subheader("Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_activities = len(filtered_df)
        total_duration_seconds = filtered_df['duration'].sum()
        hours = int(total_duration_seconds // 3600)
        minutes = int((total_duration_seconds % 3600) // 60)
        total_duration_str = f"{hours}h {minutes}m"
        
        # Distance is usually in meters in Garmin exports, convert to km
        # Check if distance is likely meters (if avg > 100, probably meters)
        # Assuming input is meters for safety based on typical API
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
            
            # Calculate highlights
            highlights = []
            
            # Longest training session (by duration)
            if 'duration' in filtered_df.columns:
                longest_idx = filtered_df['duration'].idxmax()
                longest_duration = filtered_df.loc[longest_idx, 'duration']
                longest_hours = int(longest_duration // 3600)
                longest_mins = int((longest_duration % 3600) // 60)
                longest_activity = filtered_df.loc[longest_idx, 'activityName'] if 'activityName' in filtered_df.columns else "Activity"
                longest_date = filtered_df.loc[longest_idx, 'startTimeLocal'].strftime('%Y-%m-%d') if 'startTimeLocal' in filtered_df.columns else ""
                highlights.append({
                    'title': 'Longest Session',
                    'value': f"{longest_hours}h {longest_mins}m",
                    'detail': f"{longest_activity} on {longest_date}"
                })
            
            # Longest run (by distance for running activities)
            if 'distance' in filtered_df.columns and 'Category' in filtered_df.columns:
                running_df = filtered_df[filtered_df['Category'] == 'Running']
                if not running_df.empty:
                    longest_run_idx = running_df['distance'].idxmax()
                    longest_run_distance = running_df.loc[longest_run_idx, 'distance'] / 1000.0
                    longest_run_activity = running_df.loc[longest_run_idx, 'activityName'] if 'activityName' in running_df.columns else "Run"
                    longest_run_date = running_df.loc[longest_run_idx, 'startTimeLocal'].strftime('%Y-%m-%d') if 'startTimeLocal' in running_df.columns else ""
                    highlights.append({
                        'title': 'Longest Run',
                        'value': f"{longest_run_distance:.2f} km",
                        'detail': f"{longest_run_activity} on {longest_run_date}"
                    })
            
            # Highest heart rate
            if 'maxHR' in filtered_df.columns:
                max_hr_idx = filtered_df['maxHR'].idxmax()
                max_hr_value = filtered_df.loc[max_hr_idx, 'maxHR']
                max_hr_activity = filtered_df.loc[max_hr_idx, 'activityName'] if 'activityName' in filtered_df.columns else "Activity"
                max_hr_date = filtered_df.loc[max_hr_idx, 'startTimeLocal'].strftime('%Y-%m-%d') if 'startTimeLocal' in filtered_df.columns else ""
                highlights.append({
                    'title': 'Highest HR',
                    'value': f"{max_hr_value:.0f} bpm",
                    'detail': f"{max_hr_activity} on {max_hr_date}"
                })
            
            # Fastest pace/speed
            if 'maxSpeed' in filtered_df.columns:
                max_speed_idx = filtered_df['maxSpeed'].idxmax()
                max_speed_value = filtered_df.loc[max_speed_idx, 'maxSpeed']
                # Convert m/s to km/h if speed seems to be in m/s (typical range 0-20 m/s)
                if max_speed_value < 30:
                    max_speed_kmh = max_speed_value * 3.6
                    speed_display = f"{max_speed_kmh:.1f} km/h"
                else:
                    speed_display = f"{max_speed_value:.1f} km/h"
                max_speed_activity = filtered_df.loc[max_speed_idx, 'activityName'] if 'activityName' in filtered_df.columns else "Activity"
                max_speed_date = filtered_df.loc[max_speed_idx, 'startTimeLocal'].strftime('%Y-%m-%d') if 'startTimeLocal' in filtered_df.columns else ""
                highlights.append({
                    'title': 'Fastest Speed',
                    'value': speed_display,
                    'detail': f"{max_speed_activity} on {max_speed_date}"
                })
            
            # Most elevation gain
            if 'elevationGain' in filtered_df.columns:
                elevation_df = filtered_df[filtered_df['elevationGain'] > 0]
                if not elevation_df.empty:
                    max_elevation_idx = elevation_df['elevationGain'].idxmax()
                    max_elevation_value = elevation_df.loc[max_elevation_idx, 'elevationGain']
                    max_elevation_activity = elevation_df.loc[max_elevation_idx, 'activityName'] if 'activityName' in elevation_df.columns else "Activity"
                    max_elevation_date = elevation_df.loc[max_elevation_idx, 'startTimeLocal'].strftime('%Y-%m-%d') if 'startTimeLocal' in elevation_df.columns else ""
                    highlights.append({
                        'title': 'Most Elevation',
                        'value': f"{max_elevation_value:.0f} m",
                        'detail': f"{max_elevation_activity} on {max_elevation_date}"
                    })
            
            # Most calories in a single session
            if 'calories' in filtered_df.columns:
                max_calories_idx = filtered_df['calories'].idxmax()
                max_calories_value = filtered_df.loc[max_calories_idx, 'calories']
                max_calories_activity = filtered_df.loc[max_calories_idx, 'activityName'] if 'activityName' in filtered_df.columns else "Activity"
                max_calories_date = filtered_df.loc[max_calories_idx, 'startTimeLocal'].strftime('%Y-%m-%d') if 'startTimeLocal' in filtered_df.columns else ""
                highlights.append({
                    'title': 'Most Calories',
                    'value': f"{max_calories_value:,.0f}",
                    'detail': f"{max_calories_activity} on {max_calories_date}"
                })
            
            # Longest distance overall
            if 'distance' in filtered_df.columns:
                max_distance_idx = filtered_df['distance'].idxmax()
                max_distance_value = filtered_df.loc[max_distance_idx, 'distance'] / 1000.0
                max_distance_activity = filtered_df.loc[max_distance_idx, 'activityName'] if 'activityName' in filtered_df.columns else "Activity"
                max_distance_date = filtered_df.loc[max_distance_idx, 'startTimeLocal'].strftime('%Y-%m-%d') if 'startTimeLocal' in filtered_df.columns else ""
                highlights.append({
                    'title': 'Longest Distance',
                    'value': f"{max_distance_value:.2f} km",
                    'detail': f"{max_distance_activity} on {max_distance_date}"
                })
            
            # Display highlights in a grid
            if highlights:
                num_cols = min(len(highlights), 6)
                cols = st.columns(num_cols)
                
                for i, highlight in enumerate(highlights[:num_cols]):
                    with cols[i]:
                        st.metric(
                            label=highlight['title'],
                            value=highlight['value']
                        )
                        st.caption(highlight['detail'])
        
        st.markdown("---")
        
        # --- Visualizations ---
        
        # Row 1: Volume Trends & Activity Mix
        col_viz1, col_viz2 = st.columns(2)
        
        with col_viz1:
            st.subheader("Volume Trends")
            # Group by Month
            if not filtered_df.empty:
                filtered_df['Month'] = filtered_df['startTimeLocal'].dt.to_period('M').astype(str)
                monthly_stats = filtered_df.groupby('Month').agg({'duration': 'sum', 'activityId': 'count'}).reset_index()
                monthly_stats['duration_hours'] = monthly_stats['duration'] / 3600
                
                fig_volume = px.bar(monthly_stats, x='Month', y='duration_hours', 
                                    title="Total Duration per Month (Hours)",
                                    labels={'duration_hours': 'Duration (Hours)'})
                # Adding secondary axis for count is tricky in simple plotly express, 
                # sticking to duration for cleaner UI or using graph_objects if strictly needed.
                # Let's stick to a clean bar chart for duration as requested primarily.
                st.plotly_chart(fig_volume, use_container_width=True)
            else:
                st.info("No data for volume trends.")

        with col_viz2:
            st.subheader("Activity Mix")
            if not filtered_df.empty:
                fig_mix = px.pie(filtered_df, names='Category', title="Distribution of Activities", hole=0.4)
                st.plotly_chart(fig_mix, use_container_width=True)
            else:
                st.info("No data for activity mix.")
        
        # Row 2: Intensity vs Duration
        st.subheader("Intensity vs Duration")
        if not filtered_df.empty:
            # Convert duration to minutes for scatter plot
            filtered_df['duration_min'] = filtered_df['duration'] / 60
            
            fig_scatter = px.scatter(filtered_df, x='duration_min', y='averageHR',
                                     size='calories', color='Category',
                                     hover_data=['activityName', 'startTimeLocal'],
                                     title="Average HR vs Duration (Size = Calories)",
                                     labels={'duration_min': 'Duration (Minutes)', 'averageHR': 'Avg Heart Rate'})
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No data for scatter plot.")
            
        st.markdown("---")
        
        # --- Raw Data Table ---
        st.subheader("Raw Data")
        
        # Column selection
        default_cols = ['startTimeLocal', 'activityName', 'Category', 'duration', 'distance', 'calories', 'averageHR']
        # Filter default cols to only those present
        default_cols = [c for c in default_cols if c in filtered_df.columns]
        
        all_cols = filtered_df.columns.tolist()
        selected_cols = st.multiselect("Select columns to display", all_cols, default=default_cols)
        
        if not filtered_df.empty:
            st.dataframe(filtered_df[selected_cols].sort_values(by='startTimeLocal', ascending=False), use_container_width=True)
        else:
            st.info("No data to display.")

        st.markdown("---")

        # --- Comparative Analysis ---
        st.subheader("Comparative Analysis")
        
        # Prepare data for time-based analysis using filtered data
        filtered_df['Year'] = filtered_df['startTimeLocal'].dt.year
        filtered_df['Month'] = filtered_df['startTimeLocal'].dt.month
        filtered_df['MonthName'] = filtered_df['startTimeLocal'].dt.strftime('%b')
        filtered_df['MonthNumber'] = filtered_df['startTimeLocal'].dt.month
        # Sort month names correctly
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_name_to_number = {name: i+1 for i, name in enumerate(month_order)}
        
        # Pre-calculate derived columns
        filtered_df['distance_km'] = filtered_df['distance'] / 1000.0
        filtered_df['duration_hours'] = filtered_df['duration'] / 3600.0
        filtered_df['count'] = 1
        
        # Metric Selector
        metric_options = {'Distance (km)': 'distance_km', 'Duration (hours)': 'duration_hours', 'Calories': 'calories', 'Activities': 'count'}
        selected_metric_label = st.selectbox("Select Metric for Comparison", list(metric_options.keys()))
        selected_metric = metric_options[selected_metric_label]
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("### Year on Year Comparison")
            if not filtered_df.empty:
                # Group by Year and Month
                yoy_data = filtered_df.groupby(['Year', 'Month', 'MonthName'])[selected_metric].sum().reset_index()
                
                fig_yoy = px.line(yoy_data, x='MonthName', y=selected_metric, color='Year',
                                  title=f"Monthly {selected_metric_label} (Year over Year)",
                                  category_orders={'MonthName': month_order},
                                  markers=True)
                st.plotly_chart(fig_yoy, use_container_width=True)
            else:
                st.info("No data available for comparison.")
            
        with col_c2:
            st.markdown("### Month-by-Month Comparison")
            if not filtered_df.empty:
                # Get available months from filtered data
                available_months = sorted(filtered_df['MonthName'].unique(), 
                                         key=lambda x: month_name_to_number.get(x, 13))
                
                # Month filter
                selected_months = st.multiselect(
                    "Select months to compare",
                    month_order,
                    default=available_months if len(available_months) <= 6 else available_months[:6],
                    key="month_comparison_filter"
                )
                
                if selected_months:
                    # Filter data to selected months
                    month_comparison_df = filtered_df[filtered_df['MonthName'].isin(selected_months)].copy()
                    
                    # Group by Year and MonthName, then aggregate
                    mom_data = month_comparison_df.groupby(['Year', 'MonthName', 'MonthNumber'])[selected_metric].sum().reset_index()
                    
                    # Create visualization comparing same months across years
                    fig_mom = px.bar(mom_data, x='MonthName', y=selected_metric, color='Year',
                                     title=f"{selected_metric_label} by Month (Comparing Same Months Across Years)",
                                     labels={selected_metric: selected_metric_label, 'MonthName': 'Month'},
                                     category_orders={'MonthName': month_order},
                                     barmode='group')
                    st.plotly_chart(fig_mom, use_container_width=True)
                else:
                    st.info("Please select at least one month to compare.")
            else:
                st.info("No data available for comparison.")

else:
    st.info("Please upload a CSV file to begin.")
