import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Instant CSV Dashboard", layout="wide")
st.title("📊 Instant CSV Dashboard")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Attempt to detect date columns for selection
    date_columns = df.select_dtypes(include=['object','datetime', 'datetimetz']).columns.tolist()
    st.subheader("Preview")
    st.dataframe(df)
    
    # Ask user to pick the date column (default to 'Date' if present)
    date_col = st.selectbox("Select Date column (for filtering period):", date_columns, 
                            index=date_columns.index("Date") if "Date" in date_columns else 0)

    # Convert the selected column to datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    df = df.sort_values(by=date_col)

    # Define period options
    period_option = st.selectbox("Select period", ["All", "1 Month", "3 Months", "6 Months", "1 Year", "Custom"])
    max_date = df[date_col].max()
    min_date = df[date_col].min()

    if period_option == "1 Month":
        start_date = max_date - pd.DateOffset(months=1)
        end_date = max_date
    elif period_option == "3 Months":
        start_date = max_date - pd.DateOffset(months=3)
        end_date = max_date
    elif period_option == "6 Months":
        start_date = max_date - pd.DateOffset(months=6)
        end_date = max_date
    elif period_option == "1 Year":
        start_date = max_date - pd.DateOffset(years=1)
        end_date = max_date
    elif period_option == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", min_value=min_date.date(), max_value=max_date.date(), value=min_date.date())
        with col2:
            end_date = st.date_input("End date", min_value=min_date.date(), max_value=max_date.date(), value=max_date.date())
        # Convert to Timestamp for filtering
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
    else:
        start_date, end_date = min_date, max_date

    # Filter the dataframe
    df_period = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]

    st.write(f"Selected period: {start_date.date()} to {end_date.date()}")
    st.dataframe(df_period)

    # Show summary statistics for the filtered period
    st.subheader("Summary Statistics")
    st.write(df_period.describe())

    # Chart selections
    columns = df_period.columns.tolist()
    chart_type = st.selectbox("Select chart type", ["Bar", "Line", "Pie", "Scatter"])
    x_axis = st.selectbox("X-axis", columns)
    y_axis = st.selectbox("Y-axis (for Bar/Line/Scatter)", columns, index=1 if len(columns) > 1 else 0)

    if chart_type == "Bar":
        fig = px.bar(df_period, x=x_axis, y=y_axis)
    elif chart_type == "Line":
        fig = px.line(df_period, x=x_axis, y=y_axis)
    elif chart_type == "Pie":
        fig = px.pie(df_period, names=x_axis, values=y_axis)
    elif chart_type == "Scatter":
        fig = px.scatter(df_period, x=x_axis, y=y_axis)

    st.subheader(f"{chart_type} Chart")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Upload a CSV file to see the dashboard features.")

# Run with: streamlit run filename.py
