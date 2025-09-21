import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

st.set_page_config(page_title="Universal Data Dashboard", layout="wide")
st.title("📊 Universal Data Dashboard")

def percent_change(start, end):
    if start == 0 or pd.isnull(start) or pd.isnull(end):
        return None
    return 100 * (end - start) / abs(start)

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # --- Date/time detection ---
    date_columns = [col for col in df.columns if any(key in col.lower() for key in ["date", "time"])]
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    date_col = date_columns[0] if date_columns else None

    st.subheader("Preview (first 10 rows)")
    st.dataframe(df.head(10))

    # --- Filter by date if detected ---
    if date_col:
        # Drop rows with missing or invalid dates
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col)
        min_date, max_date = df[date_col].min(), df[date_col].max()

        st.write("**Date range in data:** {} to {} | Rows: {}".format(min_date.date(), max_date.date(), len(df)))
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

    # --- Numeric & categorical columns ---
    numeric_cols = list(filtered_df.select_dtypes(include='number').columns)
    obj_cols = [col for col in filtered_df.columns if col not in numeric_cols and filtered_df[col].dtype=='object']

    # --- Key Stats for all numeric columns ---
    if numeric_cols:
        st.subheader(":bar_chart: Key Stats (Numeric Columns)")
        for col in numeric_cols:
            stat1, stat2, stat3 = st.columns(3)
            ser = filtered_df[col].dropna()
            if len(ser) == 0:
                stat1.metric(f"{col}", "No data")
                continue
            minv, maxv = float(ser.min()), float(ser.max())
            meanv, medv, stdv, sumv = float(ser.mean()), float(ser.median()), float(ser.std()), float(ser.sum())
            recval, firstval = float(ser.iloc[-1]), float(ser.iloc[0])
            pc = percent_change(firstval, recval)
            stat1.metric(f"{col} (Latest)", f"{recval:,.2f}")
            stat1.metric(f"Min", f"{minv:,.2f}")
            stat2.metric(f"Mean", f"{meanv:,.2f}")
            stat2.metric(f"Std Dev", f"{stdv:,.2f}")
            stat3.metric(f"Sum", f"{sumv:,.2f}")
            if pc is not None:
                stat3.metric("% Change", f"{pc:.2f}%")

    # --- Custom Stat Box ---
    if numeric_cols:
        st.subheader("🔎 Custom Stat Box")
        col_custom = st.selectbox("Show stats for column:", numeric_cols, key="customstats")
        ser = filtered_df[col_custom].dropna()
        if len(ser):
            col1, col2, col3 = st.columns(3)
            col1.metric("Latest", f"{float(ser.iloc[-1]):,.2f}")
            col1.metric("First", f"{float(ser.iloc[0]):,.2f}")
            col2.metric("Min", f"{ser.min():,.2f}")
            col2.metric("Max", f"{ser.max():,.2f}")
            col3.metric("Mean", f"{ser.mean():,.2f}")
            col3.metric("Std Dev", f"{ser.std():,.2f}")
            col1.metric("Sum", f"{ser.sum():,.2f}")
            pc = percent_change(float(ser.iloc[0]), float(ser.iloc[-1])) if len(ser)>1 else None
            col2.metric("% Change", f"{pc:.2f}%" if pc is not None else "-")
        else:
            st.write("No data.")

    # --- Top categories (if categorical column has <20 unique values) ---
    cat_cols = [col for col in obj_cols if filtered_df[col].nunique() < 20]
    if cat_cols:
        st.subheader(":1234: Top categories")
        for col in cat_cols:
            st.write(f"**{col}:**")
            st.dataframe(filtered_df[col].value_counts().to_frame('count'))

    # --- Chart section ---
    st.subheader("📈 Visualization")
    chart_types = ["Bar", "Line", "Pie", "Scatter"]
    # Candlestick if OHLC present
    ohlc_cols = dict(
        open=[c for c in numeric_cols if "open" in c.lower()],
        high=[c for c in numeric_cols if "high" in c.lower()],
        low=[c for c in numeric_cols if "low" in c.lower()],
        close=[c for c in numeric_cols if "close" in c.lower()]
    )
    if date_col and all(ohlc_cols.values()):
        chart_types.insert(0, "Candlestick")
    chart_type = st.selectbox("Chart type", chart_types)

    axis_x_cand = ([date_col] if date_col else []) + [c for c in obj_cols]
    axis_y_cand = numeric_cols

    if chart_type == "Candlestick" and date_col and all(ohlc_cols.values()):
        fig = go.Figure(
            go.Candlestick(
                x=filtered_df[date_col],
                open=filtered_df[ohlc_cols['open'][0]],
                high=filtered_df[ohlc_cols['high'][0]],
                low=filtered_df[ohlc_cols['low'][0]],
                close=filtered_df[ohlc_cols['close'][0]]))
        fig.update_layout(xaxis_title=date_col, yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Pie" and axis_x_cand and axis_y_cand:
        pie_label = st.selectbox("Pie labels (categorical)", axis_x_cand)
        pie_value = st.selectbox("Pie values (numeric)", axis_y_cand)
        fig = px.pie(filtered_df, names=pie_label, values=pie_value)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type in ["Bar", "Line", "Scatter"] and axis_x_cand and axis_y_cand:
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
        st.info("Choose chart axes and upload compatible data for this chart.")

else:
    st.info("Upload a CSV file to see the dashboard features.")

# Save as: universal_dashboard.py
# Run with: streamlit run universal_dashboard.py
