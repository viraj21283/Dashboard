import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

st.set_page_config(page_title="Universal Data Dashboard", layout="wide")
st.title("📊 Universal Data Dashboard")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Try to detect date columns
    date_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col]) or
                    (df[col].dtype == object and
                     any(k in col.lower() for k in ['date', 'time', 'day']) )]

    if date_columns:
        # Attempt conversion
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='ignore')

    st.subheader("Preview (first 10 rows)")
    st.dataframe(df.head(10))

    # Select date column for period filtering (if available)
    filter_by_date = False
    if date_columns:
        date_col = st.selectbox("Select date/time column (for period filtering):", date_columns)
        filter_by_date = True

        # Remove rows with missing dates in selected column
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col)
        min_date, max_date = df[date_col].min(), df[date_col].max()

        # Period filtering
        period_option = st.selectbox("Select period", ["All", "1 Month", "3 Months", "6 Months", "1 Year", "Custom"])
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
                start_date = st.date_input("Start date", value=min_date.date(), min_value=min_date.date(), max_value=max_date.date())
            with col2:
                end_date = st.date_input("End date", value=max_date.date(), min_value=min_date.date(), max_value=max_date.date())
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
        else:  # All
            start_date, end_date = min_date, max_date

        # Filter
        filtered_df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
        st.write(f"Selected period: {start_date.date()} to {end_date.date()} | Rows: {len(filtered_df)}")
    else:
        filtered_df = df

    # Show only numeric columns in summary
    numeric_cols = filtered_df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        st.subheader("Summary Statistics (Numeric Columns)")
        st.write(filtered_df[numeric_cols].describe())
    else:
        st.warning("No numeric columns detected for summary statistics.")

    # Axis selection: X can be date or categorical; Y: only numeric columns
    axis_x_candidates = [c for c in filtered_df.columns if c in date_columns or
                         filtered_df[c].dtype == 'object' or filtered_df[c].dtype.name == 'category']
    axis_y_candidates = list(numeric_cols)

    # Special: Candlestick for OHLC data
    o_col = [c for c in filtered_df.columns if c.lower().startswith("o") and "open" in c.lower()]
    h_col = [c for c in filtered_df.columns if c.lower().startswith("h") and "high" in c.lower()]
    l_col = [c for c in filtered_df.columns if c.lower().startswith("l") and "low" in c.lower()]
    c_col = [c for c in filtered_df.columns if c.lower().startswith("c") and "close" in c.lower()]

    # Decide if candlestick chart option is available:
    candlestick_ready = (filter_by_date and len(o_col) > 0 and len(h_col) > 0 and len(l_col) > 0 and len(c_col) > 0)

    chart_types = ["Bar", "Line", "Pie", "Scatter"]
    if candlestick_ready:
        chart_types.insert(0, "Candlestick (OHLC)")  # add candlestick to start

    chart_type = st.selectbox("Select chart type", chart_types)

    if chart_type == "Pie" and axis_x_candidates and axis_y_candidates:
        pie_label = st.selectbox("Pie labels (categorical)", axis_x_candidates)
        pie_value = st.selectbox("Pie values (numeric)", axis_y_candidates)
        fig = px.pie(filtered_df, names=pie_label, values=pie_value)
    elif chart_type == "Candlestick (OHLC)":
        fig = go.Figure(data=[
            go.Candlestick(
                x=filtered_df[date_col], open=filtered_df[o_col[0]],
                high=filtered_df[h_col[0]],
                low=filtered_df[l_col[0]],
                close=filtered_df[c_col[0]],
                name='Candlestick')
        ])
        fig.update_layout(xaxis_title=str(date_col), yaxis_title="Price")
    else:
        x_axis = st.selectbox("X-axis", axis_x_candidates) if axis_x_candidates else None
        y_axis = st.selectbox("Y-axis", axis_y_candidates) if axis_y_candidates else None

        if chart_type == "Bar" and x_axis and y_axis:
            fig = px.bar(filtered_df, x=x_axis, y=y_axis)
        elif chart_type == "Line" and x_axis and y_axis:
            fig = px.line(filtered_df, x=x_axis, y=y_axis)
        elif chart_type == "Scatter" and x_axis and y_axis:
            fig = px.scatter(filtered_df, x=x_axis, y=y_axis)
        else:
            fig = None

    st.subheader(f"{chart_type} Chart")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please ensure axes are selected for your chart type, and your data contains the required columns.")

else:
    st.info("Upload a CSV file to see the dashboard features.")

# Save as: universal_dashboard.py
# Run with: streamlit run universal_dashboard.py
