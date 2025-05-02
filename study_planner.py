import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import os
import json

# --- Configuration ---
APP_TITLE = "IFOA CP1 Study Planner & Daily Tracker"
GOAL_HOURS = 600
EXAM_PAPER_1_DATE = date(2025, 9, 8)
EXAM_PAPER_2_DATE = date(2025, 9, 9)
STUDY_END_DATE = EXAM_PAPER_1_DATE - timedelta(days=1)  # Study until the day before the first exam

# Define Study Phases
phases = [
    {
        "name": "Phase 1: Foundation Building",
        "start_date": date(2025, 5, 1),
        "end_date": date(2025, 5, 31),
        "focus": "Cover core syllabus topics. Build strong fundamentals.",
        "availability": "Full-time work (Mon-Fri, 8am-5pm)",
        "target_hours_min": 85,
        "target_hours_max": 100,
        "study_leave_days_per_week": 0,
    },
    {
        "name": "Phase 2: Deep Dive & Early Practice",
        "start_date": date(2025, 6, 1),
        "end_date": date(2025, 7, 31),
        "focus": "Complete syllabus, start practice questions/intro past papers.",
        "availability": "Full-time work + 2 study leave days per week",
        "target_hours_min": 300,
        "target_hours_max": 330,
        "study_leave_days_per_week": 2,
    },
    {
        "name": "Phase 3: Consolidation",
        "start_date": date(2025, 8, 1),
        "end_date": date(2025, 8, 17),
        "focus": "Consolidate knowledge, review weaker areas, continue practice.",
        "availability": "Full-time work (Mon-Fri, 8am-5pm)",
        "target_hours_min": 50,
        "target_hours_max": 60,
        "study_leave_days_per_week": 0,
    },
    {
        "name": "Phase 4: Intense Practice & Revision",
        "start_date": date(2025, 8, 18),
        "end_date": STUDY_END_DATE,  # Ends day before exam 1
        "focus": "Maximize past papers under exam conditions. Refine technique.",
        "availability": "Full study leave",
        "target_hours_min": 170,
        "target_hours_max": 210,
        "study_leave_days_per_week": 7,  # Assuming full leave means study is possible every day
    },
]

# Default trackers
DEFAULT_TRACKERS = {
    "Study Hours": {"type": "float", "unit": "hours", "color": "blue"},
    "Screen Time": {"type": "float", "unit": "hours", "color": "red"},
    "Sleep": {"type": "float", "unit": "hours", "color": "purple"},
    "Exercise": {"type": "float", "unit": "hours", "color": "green"},
    "Meditation": {"type": "boolean", "unit": "", "color": "orange"},
    "Yess": {"type": "boolean", "unit": "", "color": "gray"},
}

# --- Utility Functions ---
def get_current_phase(current_date=None):
    """Return the current phase based on date"""
    if current_date is None:
        current_date = date.today()
    
    for phase in phases:
        if phase["start_date"] <= current_date <= phase["end_date"]:
            return phase
    
    # If no phase is found
    if current_date < phases[0]["start_date"]:
        return {"name": "Pre-Study Period", "target_hours_min": 0, "target_hours_max": 0}
    else:
        return {"name": "Post-Exam Period", "target_hours_min": 0, "target_hours_max": 0}

def save_tracker_data(data):
    """Save tracker data to a JSON file"""
    with open("tracker_data.json", "w") as f:
        # Convert date objects to strings for JSON serialization
        serializable_data = {}
        for date_str, values in data.items():
            serializable_data[date_str] = values
        
        json.dump(serializable_data, f)

def load_tracker_data():
    """Load tracker data from a JSON file"""
    if os.path.exists("tracker_data.json"):
        with open("tracker_data.json", "r") as f:
            data = json.load(f)
            # Convert string dates back to date objects for internal use
            return data
    return {}

def save_custom_trackers(trackers):
    """Save custom trackers to a JSON file"""
    with open("custom_trackers.json", "w") as f:
        json.dump(trackers, f)

def load_custom_trackers():
    """Load custom trackers from a JSON file"""
    if os.path.exists("custom_trackers.json"):
        with open("custom_trackers.json", "r") as f:
            return json.load(f)
    return DEFAULT_TRACKERS.copy()

def calculate_study_progress(tracker_data, phase):
    """Calculate study progress for a given phase"""
    phase_start = phase["start_date"].isoformat()
    phase_end = phase["end_date"].isoformat()
    
    # Filter data for the current phase
    phase_data = {k: v for k, v in tracker_data.items() 
                 if phase_start <= k <= phase_end and "Study Hours" in v}
    
    # Calculate total study hours in this phase
    total_hours = sum(float(v["Study Hours"]) for v in phase_data.values() if v["Study Hours"])
    
    # Calculate target progress
    target_min = phase["target_hours_min"]
    target_max = phase["target_hours_max"]
    target_avg = (target_min + target_max) / 2
    
    # Calculate percentage of completion
    if target_avg > 0:
        completion_pct = (total_hours / target_avg) * 100
    else:
        completion_pct = 0
        
    return {
        "total_hours": total_hours,
        "target_min": target_min,
        "target_max": target_max,
        "completion_pct": completion_pct
    }

def calculate_daily_targets(phase):
    """Calculate daily target hours for a given phase"""
    days_in_phase = (phase["end_date"] - phase["start_date"]).days + 1
    daily_min = phase["target_hours_min"] / days_in_phase
    daily_max = phase["target_hours_max"] / days_in_phase
    return daily_min, daily_max

def date_to_phase_day(current_date, phase):
    """Convert a date to day number within the phase"""
    if current_date < phase["start_date"] or current_date > phase["end_date"]:
        return None
    return (current_date - phase["start_date"]).days + 1

def days_to_completion(current_date, phase):
    """Calculate days remaining until phase completion"""
    if current_date > phase["end_date"]:
        return 0
    return (phase["end_date"] - current_date).days + 1

# --- App Layout ---
st.set_page_config(page_title=APP_TITLE, layout="wide")

# Initialize session state for tab selection
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Daily Tracker"

# Load saved data
tracker_data = load_tracker_data()
custom_trackers = load_custom_trackers()

# Application tabs
tabs = [
    "Daily Tracker", 
    "Study Plan Overview", 
    "Progress Analytics", 
    "Health Analytics",  
    "Settings"
]

st.session_state.active_tab = st.sidebar.radio("Navigation", tabs)

# Sidebar info
st.sidebar.divider()
st.sidebar.header("Exam Dates")
st.sidebar.write(f"**CP1 Paper 1:** {EXAM_PAPER_1_DATE.strftime('%A, %B %d, %Y')}")
st.sidebar.write(f"**CP1 Paper 2:** {EXAM_PAPER_2_DATE.strftime('%A, %B %d, %Y')}")
st.sidebar.divider()

# Get current date (with option to override for testing)
today = date.today()
if st.session_state.active_tab in ["Daily Tracker", "Progress Analytics"]:
    selected_date = st.sidebar.date_input("Select Date", value=today, 
                                         min_value=date(2025, 1, 1), 
                                         max_value=EXAM_PAPER_2_DATE)
else:
    selected_date = today

# Identify current phase
current_phase = get_current_phase(selected_date)
st.sidebar.write(f"**Current Phase:** {current_phase['name']}")

# --- Daily Tracker Tab ---
if st.session_state.active_tab == "Daily Tracker":
    st.title(f"Daily Tracker - {selected_date.strftime('%A, %B %d, %Y')}")
    
    # Calculate which day of the phase this is
    phase_day = date_to_phase_day(selected_date, current_phase)
    days_remaining = days_to_completion(selected_date, current_phase)
    
    if phase_day is not None:
        st.info(f"Day {phase_day} of current phase. {days_remaining} days remaining in this phase.")
    
    # Create form for daily input
    with st.form("daily_tracker_form"):
        # Create input fields for each tracker
        tracker_values = {}
        col1, col2 = st.columns(2)
        
        for i, (tracker_name, tracker_info) in enumerate(custom_trackers.items()):
            # Alternate between columns
            current_col = col1 if i % 2 == 0 else col2
            
            # Get previous value if it exists
            date_str = selected_date.isoformat()
            prev_value = ""
            if date_str in tracker_data and tracker_name in tracker_data[date_str]:
                prev_value = tracker_data[date_str][tracker_name]
            
            # Create appropriate input based on tracker type
            with current_col:
                if tracker_info["type"] == "float":
                    unit_text = f" ({tracker_info['unit']})" if tracker_info['unit'] else ""
                    tracker_values[tracker_name] = st.number_input(
                        f"{tracker_name}{unit_text}", 
                        min_value=0.0, 
                        value=float(prev_value) if prev_value else 0.0,
                        step=0.5
                    )
                elif tracker_info["type"] == "boolean":
                    tracker_values[tracker_name] = st.checkbox(
                        tracker_name,
                        value=True if prev_value == "True" else False
                    )
                elif tracker_info["type"] == "integer":
                    unit_text = f" ({tracker_info['unit']})" if tracker_info['unit'] else ""
                    tracker_values[tracker_name] = st.number_input(
                        f"{tracker_name}{unit_text}", 
                        min_value=0, 
                        value=int(prev_value) if prev_value else 0,
                        step=1
                    )
                elif tracker_info["type"] == "text":
                    tracker_values[tracker_name] = st.text_input(
                        tracker_name,
                        value=prev_value if prev_value else ""
                    )
        
        submit_button = st.form_submit_button("Save Daily Data")
        
        if submit_button:
            # Convert values to strings for storage
            for k, v in tracker_values.items():
                tracker_values[k] = str(v)
            
            # Save the data
            date_str = selected_date.isoformat()
            tracker_data[date_str] = tracker_values
            save_tracker_data(tracker_data)
            st.success(f"Data saved for {selected_date.strftime('%A, %B %d, %Y')}")
    
    # Display study progress for today
    if "Study Hours" in custom_trackers:
        st.divider()
        st.subheader("Today's Study Progress")
        
        # Calculate daily targets
        daily_min, daily_max = calculate_daily_targets(current_phase)
        
        # Get today's study hours
        date_str = selected_date.isoformat()
        today_hours = 0
        if date_str in tracker_data and "Study Hours" in tracker_data[date_str]:
            today_hours = float(tracker_data[date_str]["Study Hours"])
        
        # Create a progress bar
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            progress_pct = min(today_hours / daily_max * 100, 100) if daily_max > 0 else 0
            st.progress(progress_pct / 100)
            
        with col2:
            st.metric("Today's Hours", f"{today_hours:.1f} hrs")
            
        with col3:
            st.metric("Daily Target", f"{daily_min:.1f} - {daily_max:.1f} hrs")
        
        # Status message
        if today_hours >= daily_min and today_hours <= daily_max:
            st.success("On target for today! 🎯")
        elif today_hours > daily_max:
            st.success("Exceeded today's target! 🚀")
        elif today_hours > 0:
            st.warning(f"Below target. Need {daily_min - today_hours:.1f} more hours to reach minimum.")
        else:
            st.error("No study hours recorded today.")

# --- Study Plan Overview Tab ---
elif st.session_state.active_tab == "Study Plan Overview":
    st.title(APP_TITLE)
    st.subheader(f"Goal: Achieve {GOAL_HOURS} study hours")
    st.caption(f"Study Period: May 1st, 2025 - {STUDY_END_DATE.strftime('%B %d, %Y')}")
    st.divider()
    
    total_min_hours = 0
    total_max_hours = 0
    
    # Display details for each phase
    for i, phase in enumerate(phases):
        st.header(phase["name"])
        
        # Highlight current phase
        if phase == current_phase:
            st.markdown("**🔴 CURRENT PHASE 🔴**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Duration",
                value=f"{(phase['end_date'] - phase['start_date']).days + 1} days",
                delta=f"{phase['start_date'].strftime('%b %d')} - {phase['end_date'].strftime('%b %d')}"
            )
        
        # Calculate average hours needed
        duration_days = (phase['end_date'] - phase['start_date']).days + 1
        duration_weeks = duration_days / 7.0
        avg_weekly_min = phase['target_hours_min'] / duration_weeks
        avg_weekly_max = phase['target_hours_max'] / duration_weeks
        avg_daily_min = phase['target_hours_min'] / duration_days
        avg_daily_max = phase['target_hours_max'] / duration_days
        
        with col2:
            st.metric(
                label="Target Hours",
                value=f"{phase['target_hours_min']} - {phase['target_hours_max']} hrs",
            )
        
        with col3:
            st.metric(
                label="Avg. Weekly Pace",
                value=f"{avg_weekly_min:.1f} - {avg_weekly_max:.1f} hrs/week",
                help=f"Based on {duration_weeks:.1f} weeks in this phase."
            )
            st.metric(
                label="Avg. Daily Pace",
                value=f"{avg_daily_min:.1f} - {avg_daily_max:.1f} hrs/day",
                help=f"Based on {duration_days} days in this phase. Requires balancing work/leave days."
            )
        
        # Calculate and display progress for this phase
        progress = calculate_study_progress(tracker_data, phase)
        
        # Progress bar
        col1, col2 = st.columns([3, 1])
        with col1:
            progress_pct = min(progress["completion_pct"], 100)
            st.progress(progress_pct / 100)
            st.caption(f"Progress: {progress_pct:.1f}% ({progress['total_hours']:.1f} hrs of {progress['target_min']}-{progress['target_max']} hrs)")
        
        with col2:
            if today >= phase["start_date"] and today <= phase["end_date"]:
                days_elapsed = (today - phase["start_date"]).days + 1
                days_total = duration_days
                time_pct = (days_elapsed / days_total) * 100
                
                # Compare time elapsed vs progress
                if progress_pct >= time_pct:
                    st.success(f"Ahead of schedule! 🚀")
                elif progress_pct >= time_pct * 0.8:
                    st.info(f"Nearly on track")
                else:
                    st.warning(f"Behind schedule")
                
                st.caption(f"Time elapsed: {time_pct:.1f}% ({days_elapsed} of {days_total} days)")
        
        st.write(f"**Focus:** {phase['focus']}")
        st.write(f"**Availability:** {phase['availability']}")
        
        # Add notes based on availability
        if phase["study_leave_days_per_week"] == 0 and "Full-time work" in phase["availability"]:
            st.info("Requires dedicated evening and weekend study.")
        elif phase["study_leave_days_per_week"] == 2:
            st.info("Utilize the 2 study leave days fully (e.g., 8+ hrs each) plus evenings/weekends.")
        elif phase["study_leave_days_per_week"] == 7:
            st.success("Full leave: Aim for consistent daily hours, simulating exam workload.")
        
        st.divider()
        
        total_min_hours += phase["target_hours_min"]
        total_max_hours += phase["target_hours_max"]
    
    # --- Summary ---
    st.header("Overall Plan Summary")
    
    # Calculate overall progress
    total_study_hours = sum([float(v.get("Study Hours", 0)) for v in tracker_data.values() 
                           if "Study Hours" in v and v["Study Hours"]])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Estimated Hours",
            value=f"{total_min_hours} - {total_max_hours} hours"
        )
    
    with col2:
        overall_progress = (total_study_hours / GOAL_HOURS) * 100 if GOAL_HOURS > 0 else 0
        st.metric(
            label="Overall Progress",
            value=f"{total_study_hours:.1f} hours",
            delta=f"{overall_progress:.1f}% of goal"
        )
    
    with col3:
        days_until_exam = (EXAM_PAPER_1_DATE - today).days
        st.metric(
            label="Days Until Exam",
            value=days_until_exam
        )
    
    # Progress bar for overall goal
    st.progress(min(overall_progress / 100, 1.0))
    
    if total_min_hours <= GOAL_HOURS <= total_max_hours:
        st.success(f"The plan aligns with your goal of {GOAL_HOURS} hours.")
    elif GOAL_HOURS < total_min_hours:
        st.warning(f"The plan exceeds your goal of {GOAL_HOURS} hours. You have some buffer.")
    else:
        st.error(f"The plan falls short of your goal of {GOAL_HOURS} hours. Consider increasing hours in some phases.")
    
    st.subheader("Tips for Success")
    st.markdown("""
    * **Consistency:** Stick to your weekly goals.
    * **Active Learning:** Practice questions, make notes, test yourself.
    * **Past Papers:** Dedicate Phase 4 to timed past papers. Analyze mistakes.
    * **Well-being:** Schedule breaks and get enough sleep.
    """)

# --- Progress Analytics Tab ---
elif st.session_state.active_tab == "Progress Analytics":
    st.title("Progress Analytics")
    
    # Convert tracker data to DataFrame for easier analysis
    if tracker_data:
        # Create list of dates and convert to pandas dataframe
        df_list = []
        for date_str, values in tracker_data.items():
            row = {"date": date_str}
            row.update(values)
            df_list.append(row)
        
        df = pd.DataFrame(df_list)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        
        # Convert numeric columns
        for col in df.columns:
            if col != "date":
                try:
                    # Try to convert to float, but if it's boolean it will fail
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        # Time series for numeric values
        st.header("Daily Tracking")
        
        # Create tabs for different types of visualizations
        viz_tabs = st.tabs(["Study Progress", "Daily Metrics", "Habit Calendar"])
        
        with viz_tabs[0]:
            st.subheader("Study Hours Progress")
            
            if "Study Hours" in df.columns:
                # Study hours over time
                fig = px.line(df, 
                             x="date", 
                             y="Study Hours", 
                             title="Daily Study Hours",
                             markers=True)
                
                # Add a 7-day moving average
                df['7day_avg'] = df['Study Hours'].rolling(window=7, min_periods=1).mean()
                fig.add_scatter(x=df['date'], y=df['7day_avg'], 
                               mode='lines', name='7-day Average',
                               line=dict(color='red', width=2))
                
                # Add recommended daily range
                if current_phase:
                    daily_min, daily_max = calculate_daily_targets(current_phase)
                    fig.add_shape(
                        type="line", line=dict(dash='dash', color="green"),
                        x0=df['date'].min(), x1=df['date'].max(), y0=daily_min, y1=daily_min
                    )
                    fig.add_shape(
                        type="line", line=dict(dash='dash', color="green"),
                        x0=df['date'].min(), x1=df['date'].max(), y0=daily_max, y1=daily_max
                    )
                    
                    # Add annotation for target range
                    fig.add_annotation(
                        x=df['date'].max(), y=daily_max,
                        text=f"Target Range",
                        showarrow=True,
                        arrowhead=1
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate cumulative study hours
                df['Cumulative Hours'] = df['Study Hours'].cumsum()
                
                # Plot cumulative hours
                fig = px.line(df, 
                             x="date", 
                             y="Cumulative Hours", 
                             title="Cumulative Study Hours",
                             markers=True)
                
                # Add goal line
                fig.add_shape(
                    type="line", line=dict(dash='dash', color="red"),
                    x0=df['date'].min(), x1=STUDY_END_DATE, y0=GOAL_HOURS, y1=GOAL_HOURS
                )
                
                # Add annotation for goal
                fig.add_annotation(
                    x=STUDY_END_DATE, y=GOAL_HOURS,
                    text=f"Goal: {GOAL_HOURS} hours",
                    showarrow=True,
                    arrowhead=1
                )
                
                # Calculate ideal progress line
                study_start = phases[0]["start_date"]
                study_end = STUDY_END_DATE
                total_days = (study_end - study_start).days + 1
                
                # Create ideal progress line
                ideal_dates = pd.date_range(start=study_start, end=study_end)
                ideal_progress = [(i / total_days) * GOAL_HOURS for i in range(len(ideal_dates))]
                
                # Add ideal progress line
                fig.add_scatter(
                    x=ideal_dates,
                    y=ideal_progress,
                    mode='lines',
                    name='Ideal Progress',
                    line=dict(color='green', dash='dot')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Weekly summary
                st.subheader("Weekly Study Summary")
                df['week'] = df['date'].dt.isocalendar().week
                df['year'] = df['date'].dt.isocalendar().year
                weekly_df = df.groupby(['year', 'week']).agg({'Study Hours': 'sum'}).reset_index()
                weekly_df['Week'] = weekly_df['year'].astype(str) + '-W' + weekly_df['week'].astype(str)
                
                fig = px.bar(weekly_df, 
                            x='Week', 
                            y='Study Hours',
                            title="Weekly Study Hours")
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No study hours data available yet.")
        
        with viz_tabs[1]:
            st.subheader("Daily Metrics")
            
            # Get numeric columns for plotting
            numeric_cols = [col for col in df.columns if col != 'date' and pd.api.types.is_numeric_dtype(df[col])]
            
            if numeric_cols:
                # Let user select metrics to view
                selected_metrics = st.multiselect(
                    "Select metrics to view",
                    options=numeric_cols,
                    default=["Study Hours"] if "Study Hours" in numeric_cols else numeric_cols[:1]
                )
                
                if selected_metrics:
                    # Line chart for selected metrics
                    fig = px.line(df, 
                                 x="date", 
                                 y=selected_metrics,
                                 title="Daily Metrics Comparison",
                                 markers=True)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Correlation heatmap
                    st.subheader("Correlation Analysis")
                    
                    # Calculate correlation matrix
                    corr_matrix = df[numeric_cols].corr()
                    
                    # Create heatmap
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        color_continuous_scale='RdBu_r',
                        title="Correlation Between Metrics"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Scatter plot for correlations
                    if len(selected_metrics) >= 2:
                        st.subheader("Relationship Analysis")
                        
                        x_var = st.selectbox("X-axis", options=numeric_cols, index=0)
                        y_var = st.selectbox("Y-axis", options=numeric_cols, 
                                           index=1 if len(numeric_cols) > 1 else 0)
                        
                        fig = px.scatter(
                            df,
                            x=x_var,
                            y=y_var,
                            title=f"{y_var} vs {x_var}",
                            trendline="ols"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show Pearson correlation coefficient
                        correlation = df[x_var].corr(df[y_var])
                        st.info(f"Correlation coefficient: {correlation:.3f}")
                        
                        if abs(correlation) > 0.7:
                            st.success("Strong correlation detected!")
                        elif abs(correlation) > 0.4:
                            st.info("Moderate correlation detected.")
                        else:
                            st.warning("Weak or no correlation detected.")
            else:
                st.warning("No numeric data available for analysis.")
        
        with viz_tabs[2]:
            st.subheader("Habit Calendar")
            
            # Create calendar heatmap for boolean values
            boolean_cols = [col for col in df.columns 
                           if col != 'date' and df[col].isin(['True', 'False']).all()]
            
            if boolean_cols:
                # Let user select a habit to view
                selected_habit = st.selectbox(
                    "Select habit to view",
                    options=boolean_cols
                )
                
                # Convert selected column to boolean
                df[selected_habit] = df[selected_habit] == 'True'
                
                # Create calendar heatmap
                df['year'] = df['date'].dt.year
                df['month'] = df['date'].dt.month
                df['day'] = df['date'].dt.day
                
                # Create a pivot table for the calendar
                calendar_data = df.pivot_table(
                    index='day',
                    columns=['year', 'month'],
                    values=selected_habit,
                    aggfunc='sum'
                ).fillna(0)
                
                # Convert to integer (0 or 1)
                calendar_data = calendar_data.astype(int)
                
                # Create heatmap
                fig = px.imshow(
                    calendar_data,
                    color_continuous_scale=['#f8f9fa', '#198754'],
                    title=f"{selected_habit} Calendar"
                )
                
                # Update x-axis to show month names
                month_names = {
                    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
                }
                
                # Format x-axis labels
                new_labels = []
                for col in calendar_data.columns:
                    year, month = col
                    new_labels.append(f"{month_names[month]} {year}")
                
                fig.update_layout(
                    xaxis=dict(
                        tickmode='array',
                        tickvals=list(range(len(new_labels))),
                        ticktext=new_labels
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate streak statistics
                if len(df) > 0:
                    # Convert to boolean series
                    habit_series = df[selected_habit].astype(bool)
                    
                    # Calculate current streak
                    current_streak = 0
                    for val in habit_series[::-1]:  # Reverse to count from most recent
                        if val:
                            current_streak += 1
                        else:
                            break
                    
                    # Calculate longest streak
                    streaks = []
                    current = 0
                    for val in habit_series:
                        if val:
                            current += 1
                        else:
                            streaks.append(current)
                            current = 0
                    streaks.append(current)  # Add the last streak
                    longest_streak = max(streaks) if streaks else 0
                    
                    # Calculate completion rate
                    completion_rate = (habit_series.sum() / len(habit_series)) * 100
                    
                    # Display statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current Streak", f"{current_streak} days")
                    with col2:
                        st.metric("Longest Streak", f"{longest_streak} days")
                    with col3:
                        st.metric("Completion Rate", f"{completion_rate:.1f}%")
            else:
                st.warning("No boolean (yes/no) data available for habit tracking.")
    else:
        st.warning("No tracking data available yet. Start recording daily data to see analytics.")
elif st.session_state.active_tab == "Health Analytics":
    st.title("Health Analytics")
    
    if tracker_data:
        # Create DataFrame from tracker data
        df_list = []
        for date_str, values in tracker_data.items():
            row = {"date": date_str}
            row.update(values)
            df_list.append(row)
        df = pd.DataFrame(df_list)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        
        # Convert to numeric values
        health_metrics = ["Sleep", "Screen Time", "Exercise"]
        for col in health_metrics:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Time frame selection
        time_frame = st.selectbox(
            "Aggregation Period",
            ["Daily", "Weekly Average", "Monthly Average"],
            key="health_time_frame"
        )
        
        # Process data based on time frame
        if time_frame == "Weekly Average":
            resampled_df = df.set_index("date").resample("W-MON").mean().reset_index()
            title_suffix = " (Weekly Average)"
        elif time_frame == "Monthly Average":
            resampled_df = df.set_index("date").resample("ME").mean().reset_index()
            title_suffix = " (Monthly Average)"
        else:
            resampled_df = df.copy()
            title_suffix = ""
        
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)
        
        # Sleep Visualization
        with col1:
            st.subheader("Sleep Hours")
            if "Sleep" in df.columns:
                fig = px.bar(resampled_df, x="date", y="Sleep", 
                            title=f"Sleep Hours{title_suffix}")
                fig.add_hrect(y0=6, y1=7, line_width=0, 
                            fillcolor="green", opacity=0.2,
                            annotation_text="Target 6-7 hours")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No sleep data available")
        
        # Screen Time Visualization
        with col2:
            st.subheader("Screen Time")
            if "Screen Time" in df.columns:
                fig = px.bar(resampled_df, x="date", y="Screen Time",
                            title=f"Screen Time{title_suffix}")
                fig.add_hline(y=3, line_dash="dash", line_color="red",
                            annotation_text="Target: 3 hours")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No screen time data available")
        
        # Exercise Visualization
        with col3:
            st.subheader("Exercise Hours")
            if "Exercise" in df.columns:
                fig = px.bar(resampled_df, x="date", y="Exercise",
                            title=f"Exercise Hours{title_suffix}")
                fig.add_hrect(y0=1, y1=2, line_width=0,
                            fillcolor="blue", opacity=0.2,
                            annotation_text="Target 1-2 hours")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No exercise data available")
        
        # Add summary statistics
        st.divider()
        st.subheader("Summary Statistics")
        
        # Calculate averages
        if time_frame == "Daily":
            avg_text = "Current Month Averages"
            filtered_df = df[df["date"].dt.month == pd.Timestamp.today().month]
        else:
            avg_text = "All-Time Averages"
            filtered_df = df
            
        col1, col2, col3 = st.columns(3)
        with col1:
            if "Sleep" in filtered_df:
                avg_sleep = filtered_df["Sleep"].mean()
                st.metric("Average Sleep", f"{avg_sleep:.1f} hours", 
                         delta="Within target" if 6 <= avg_sleep <= 7 else "Outside target")
        
        with col2:
            if "Screen Time" in filtered_df:
                avg_screen = filtered_df["Screen Time"].mean()
                st.metric("Average Screen Time", f"{avg_screen:.1f} hours", 
                         delta="Within target" if avg_screen <= 3 else "Over target")
        
        with col3:
            if "Exercise" in filtered_df:
                avg_exercise = filtered_df["Exercise"].mean()
                st.metric("Average Exercise", f"{avg_exercise:.1f} hours", 
                         delta="Within target" if 1 <= avg_exercise <= 2 else "Outside target")
        
    else:
        st.warning("No tracking data available yet")
# --- Settings Tab ---
elif st.session_state.active_tab == "Settings":
    st.title("Settings")
    
    st.header("Custom Trackers")
    st.write("Configure what metrics you want to track daily. Changes will apply to future data entry.")
    
    with st.form("tracker_settings_form"):
        # Display current trackers with options to edit or remove
        st.subheader("Current Trackers")
        
        trackers_to_remove = []
        new_tracker_settings = {}
        
        for tracker_name, tracker_info in custom_trackers.items():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
            
            with col1:
                st.write(f"**{tracker_name}**")
            
            with col2:
                tracker_type = st.selectbox(
                    f"Type for {tracker_name}",
                    options=["float", "integer", "boolean", "text"],
                    index=["float", "integer", "boolean", "text"].index(tracker_info["type"]),
                    key=f"type_{tracker_name}"
                )
            
            with col3:
                unit = st.text_input(
                    f"Unit for {tracker_name}",
                    value=tracker_info.get("unit", ""),
                    key=f"unit_{tracker_name}"
                )
            
            
            with col4:
                # Can't remove core trackers
                if tracker_name in ["Study Hours"]:
                    st.write("Required")
                else:
                    remove = st.checkbox(f"Remove {tracker_name}", key=f"remove_{tracker_name}")
                    if remove:
                        trackers_to_remove.append(tracker_name)
            
            # Store new settings
            if tracker_name not in trackers_to_remove:
                new_tracker_settings[tracker_name] = {
                    "type": tracker_type,
                    "unit": unit,
                }
        
        # Add new tracker
        st.subheader("Add New Tracker")
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            new_tracker_name = st.text_input("New Tracker Name")
        
        with col2:
            new_tracker_type = st.selectbox(
                "Type",
                options=["float", "integer", "boolean", "text"]
            )
        
        with col3:
            new_tracker_unit = st.text_input("Unit (optional)")
        
        with col4:
            new_tracker_color = st.color_picker("Color", value="#0000FF")
        
        # Save button
        save_settings = st.form_submit_button("Save Settings")
        
        if save_settings:
            # Remove trackers marked for removal
            for tracker in trackers_to_remove:
                if tracker in custom_trackers:
                    del custom_trackers[tracker]
            
            # Update existing trackers
            for tracker_name, settings in new_tracker_settings.items():
                custom_trackers[tracker_name] = settings
            
            # Add new tracker if name is provided
            if new_tracker_name and new_tracker_name not in custom_trackers:
                custom_trackers[new_tracker_name] = {
                    "type": new_tracker_type,
                    "unit": new_tracker_unit,
                    "color": new_tracker_color
                }
            
            # Save custom trackers
            save_custom_trackers(custom_trackers)
            st.success("Settings saved successfully!")
    
    # Study plan settings
    st.divider()
    st.header("Study Plan Settings")
    
    with st.form("study_plan_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_goal_hours = st.number_input(
                "Total Study Goal (hours)",
                min_value=1,
                value=GOAL_HOURS,
                step=10
            )
        
        with col2:
            new_exam_date = st.date_input(
                "Exam Date (Paper 1)",
                value=EXAM_PAPER_1_DATE,
                min_value=date.today()
            )
        
        save_plan_settings = st.form_submit_button("Save Plan Settings")
        
        if save_plan_settings:
            st.warning("This feature is not yet implemented. Currently, changing these settings requires modifying the code directly.")
    
    # Data management
    st.divider()
    st.header("Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Data"):
            # Generate CSV from tracker data
            if tracker_data:
                df_list = []
                for date_str, values in tracker_data.items():
                    row = {"date": date_str}
                    row.update(values)
                    df_list.append(row)
                
                df = pd.DataFrame(df_list)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="study_tracker_data.csv",
                    mime="text/csv",
                )
            else:
                st.error("No data available to export.")
    
    with col2:
        if st.button("Reset All Data", type="primary", use_container_width=True):
            confirm = st.checkbox("I understand this will delete all my tracking data")
            
            if confirm and st.button("Confirm Reset", type="primary"):
                # Delete data files
                if os.path.exists("tracker_data.json"):
                    os.remove("tracker_data.json")
                
                # Reset to default trackers
                save_custom_trackers(DEFAULT_TRACKERS.copy())
                
                st.success("All data has been reset!")
                st.warning("Please refresh the page to see changes.")