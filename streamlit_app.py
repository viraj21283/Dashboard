import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

st.set_page_config(page_title="Universal Data Dashboard", layout="wide")
st.title("📊 Universal Data Dashboard")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

def percent_change(start, end):
    if start == 0 or pd.isnull(start) or pd.isnull(end):
        return None
    return 100 * (end - start) / abs(start)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # --- Date/time detection ---
    date_columns = [col for col in df.columns if any(key in col.lower() for key in ["date", "time"])]
    if date_columns:
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        df = df.dropna(subset=date_columns)
        df = df.sort_values(by=date_columns[0])
        date_col = st.selectbox("Select Date/Time column (for filtering):", date_columns)
        min_date, max_date = df[date_col].min(), df[date_col].max()
        period_option = st.selectbox("Period", ["All", "1 Month", "3 Months", "6 Months", "1 Year", "Custom"])
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
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
        else:
            start_date, end_date = min_date, max_date
        filtered_df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
        st.caption(f"Selected period: {start_date.date()} to {end_date.date()} | Rows: {len(filtered_df)}")
    else:
        filtered_df = df

    # --- Numeric and categorical columns ---
    numeric_cols = list(filtered_df.select_dtypes(include='number').columns)
    non_numeric_cols = [col for col in filtered_df.columns if col not in numeric_cols]
    
    # --- Key Automatic Stat Boxes (per numeric column) ---
    st.subheader("Key Stats (auto for numeric columns)")
    if numeric_cols:
        stat_cols = st.columns(min(4, len(numeric_cols)))
        for idx, col in enumerate(numeric_cols):
            ser = filtered_df[col]
            # For time series, show initial and recent, else global min/max
            rec_val = ser.iloc[-1]
            prev_val = ser.iloc[0] if len(ser) > 0 else rec_val
            pc = percent_change(prev_val, rec_val)
            stat_cols[idx % 4].metric(f"{col} (latest)", f"{rec_val:,.2f}")
            stat_cols[idx % 4].write(
                f"Min: {ser.min():,.2f}\n\n"
                f"Max: {ser.max():,.2f}\n\n"
                f"Mean: {ser.mean():,.2f}\n\n"
                f"Sum: {ser.sum():,.2f}\n\n"
                f"Std Dev: {ser.std():,.2f}\n\n"
                + (f"% Change: {pc:.2f}%" if pc is not None else "")
            )
    else:
        st.info("No numeric columns detected for stats.")

    # --- Custom Stat Box (user selects numeric column) ---
    if numeric_cols:
        st.subheader("Custom Stat Box")
        col_custom = st.selectbox("Show stats for column:", numeric_cols, key="customstats")
        ser = filtered_df[col_custom]
        st.write({
            "Recent": ser.iloc[-1] if len(ser) > 0 else None,
            "First": ser.iloc[0] if len(ser) > 0 else None,
            "Min": ser.min(),
            "Max": ser.max(),
            "Mean": ser.mean(),
            "Median": ser.median(),
            "Std Dev": ser.std(),
            "Sum": ser.sum(),
            "% Change": percent_change(ser.iloc[0], ser.iloc[-1]) if len(ser)>1 else None
        })

    # --- Top categories (if col with few unique values) ---
    cat_cols = [col for col in non_numeric_cols if filtered_df[col].nunique() < 20 and filtered_df[col].dtype == 'object']
    if cat_cols:
        st.subheader("Top categories (counts):")
        for col in cat_cols:
            st.write(f"{col}:")
            st.write(filtered_df[col].value_counts())

    st.subheader("Preview (top 10 rows)")
    st.dataframe(filtered_df.head(10))

    # --- Chart section ---
    chart_types = ["Bar", "Line", "Pie", "Scatter"]
    # Candlestick if OHLC present
    ohlc_cols = dict(
        open=[c for c in numeric_cols if "open" in c.lower()],
        high=[c for c in numeric_cols if "high" in c.lower()],
        low=[c for c in numeric_cols if "low" in c.lower()],
        close=[c for c in numeric_cols if "close" in c.lower()]
    )
    if date_columns and all(ohlc_cols.values()):
        chart_types.insert(0, "Candlestick")

    chart_type = st.selectbox("Chart type", chart_types)
    # For sensible axis selection
    axis_x_cand = date_columns + [col for col in non_numeric_cols if filtered_df[col].dtype == 'object']
    axis_y_cand = numeric_cols

    if chart_type == "Candlestick" and date_columns and all(ohlc_cols.values()):
        fig = go.Figure(
            go.Candlestick(
                x=filtered_df[date_col],
                open=filtered_df[ohlc_cols['open'][0]],
                high=filtered_df[ohlc_cols['high'][0]],
                low=filtered_df[ohlc_cols['low'][0]],
                close=filtered_df[ohlc_cols['close'][0]]))
        fig.update_layout(xaxis_title=date_col, yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Pie":
        pie_label = st.selectbox("Pie labels (categorical)", axis_x_cand)
        pie_value = st.selectbox("Pie values (numeric)", axis_y_cand)
        fig = px.pie(filtered_df, names=pie_label, values=pie_value)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type in ["Bar", "Line", "Scatter"]:
        x_axis = st.selectbox("X-axis", axis_x_cand)
        y_axis = st.selectbox("Y-axis", axis_y_cand)
        if chart_type == "Bar":
            fig = px.bar(filtered_df, x=x_axis, y=y_axis)
        elif chart_type == "Line":
            fig = px.line(filtered_df, x=x_axis, y=y_axis)
        elif chart_type == "Scatter":
            fig = px.scatter(filtered_df, x=x_axis, y=y_axis)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Upload a CSV file to see the dashboard features.")

# Save as: universal_dashboard.py
# Run with: streamlit run universal_dashboard.py

