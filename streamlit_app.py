import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Instant CSV Dashboard", layout="wide")
st.title("📊 Instant CSV Dashboard")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("Preview")
    st.dataframe(df)

    st.subheader("Summary Statistics")
    st.write(df.describe())

    columns = df.columns.tolist()
    chart_type = st.selectbox(
        "Select chart type",
        ["Bar", "Line", "Pie", "Scatter"]
    )
    x_axis = st.selectbox("X-axis", columns)
    y_axis = st.selectbox("Y-axis (for Bar/Line/Scatter)", columns, index=1 if len(columns) > 1 else 0)

    if chart_type == "Bar":
        fig = px.bar(df, x=x_axis, y=y_axis)
    elif chart_type == "Line":
        fig = px.line(df, x=x_axis, y=y_axis)
    elif chart_type == "Pie":
        fig = px.pie(df, names=x_axis, values=y_axis)
    elif chart_type == "Scatter":
        fig = px.scatter(df, x=x_axis, y=y_axis)

    st.subheader(f"{chart_type} Chart")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Upload a CSV file to see the dashboard features.")
