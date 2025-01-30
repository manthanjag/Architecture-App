import os
import streamlit as st
import openai
import json
from graphviz import Digraph

# Set OpenAI API key from secrets
openai.api_key = st.secrets["key"]

# Function to get tool suggestions
def get_tool_suggestions(data_sources, refresh_details):
    messages = [
        {
            "role": "system",
            "content": "You are a cloud architecture expert. Provide low-cost, high-performance tool recommendations for ingestion, transformation, and visualization tasks."
        },
        {
            "role": "user",
            "content": f"""
        Based on the following data sources and refresh configuration, suggest one tool for each task (ingestion, transformation, visualization) strictly from this list:
        [Domo, Power BI, Sigma, dbt, Snowflake, Databricks, ADF, Tableau].
        
        Expected JSON format:
        {{
            "ingestion": {{"tool": "ToolName"}},
            "transformation": {{"tool": "ToolName"}},
            "visualization": {{"tool": "ToolName"}}
        }}

        Data Sources: {", ".join(data_sources)}
        Refresh Config:
        - Historical Load: {refresh_details['historical_load']}
        - Monthly Increase: {refresh_details['monthly_increase']}
        - Number of Datasets: {refresh_details['datasets']}
        - Dataset Refresh Rates:
          - {refresh_details['daily_refresh']} datasets refresh daily
          - {refresh_details['three_hour_refresh']} datasets refresh every 3 hours
          - {refresh_details['hourly_refresh']} datasets refresh every hour
          - {refresh_details['real_time_refresh']} datasets refresh every 15 minutes
        """
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=500
    )

    response_text = response.choices[0].message['content']
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        st.error("❌ GPT returned an invalid response. Try again.")
        return None

# Function to generate the flowchart and JSON
def generate_flowchart_and_json(data_sources, refresh_details):
    tool_suggestions = get_tool_suggestions(data_sources, refresh_details)

    if not tool_suggestions:
        return None, None  # Prevents unpacking error

    # Graphviz flowchart
    flowchart = Digraph(format='png', graph_attr={'rankdir': 'LR'}, node_attr={'shape': 'box'})

    # Data Sources Node
    flowchart.node("Data Sources", "\n".join(data_sources))

    # Extract tools
    ingestion_tool = tool_suggestions.get('ingestion', {}).get('tool', 'Unknown')
    transformation_tool = tool_suggestions.get('transformation', {}).get('tool', 'Unknown')
    visualization_tool = tool_suggestions.get('visualization', {}).get('tool', 'Unknown')

    flowchart.node("Ingestion", f"{ingestion_tool} (Ingestion)")
    flowchart.node("Transformation", f"{transformation_tool} (Transformation)")
    flowchart.node("Visualization", f"{visualization_tool} (Visualization)")

    flowchart.edge("Data Sources", "Ingestion")
    flowchart.edge("Ingestion", "Transformation")
    flowchart.edge("Transformation", "Visualization")

    output_path = "data_architecture_flowchart"
    try:
        flowchart.render(output_path, format="png", view=False)
        return json.dumps(tool_suggestions, indent=4), f"{output_path}.png"
    except Exception as e:
        st.error(f"❌ Flowchart generation failed: {e}")
        return json.dumps(tool_suggestions, indent=4), None

# Streamlit UI
st.title("Data Architecture Tool Suggestion")

# Input Section
st.header("Input Configuration")

data_sources = st.multiselect(
    "Select Data Sources:",
    options=["Google Ads", "Google Analytics", "SQL Database", "Excel Files", "Social Media"],
    default=["Google Ads", "Google Analytics"]
)

if data_sources:
    st.subheader("Dataset Configuration")
    historical_load = st.number_input("Historical Load (rows):", min_value=1, value=20000000)
    monthly_increase = st.number_input("Monthly Increase (rows):", min_value=1, value=50000)
    datasets = st.number_input("Number of Datasets:", min_value=1, value=20)
    daily_refresh = st.number_input("Daily Refresh Datasets:", min_value=0, value=10)
    three_hour_refresh = st.number_input("3-Hour Refresh Datasets:", min_value=0, value=5)
    hourly_refresh = st.number_input("Hourly Refresh Datasets:", min_value=0, value=3)
    real_time_refresh = st.number_input("15-Min Refresh Datasets:", min_value=0, value=2)

    if st.button("Generate Flowchart and JSON"):
        refresh_details = {
            "historical_load": historical_load,
            "monthly_increase": monthly_increase,
            "datasets": datasets,
            "daily_refresh": daily_refresh,
            "three_hour_refresh": three_hour_refresh,
            "hourly_refresh": hourly_refresh,
            "real_time_refresh": real_time_refresh
        }

        with st.spinner("Generating suggestions and flowchart..."):
            json_response, flowchart_image_path = generate_flowchart_and_json(data_sources, refresh_details)

        if not json_response or "Error" in json_response:
            st.error("❌ Failed to generate JSON response.")
        else:
            st.success("✅ Flowchart and JSON generated successfully!")
            st.subheader("Tool Suggestions (JSON):")
            st.code(json_response, language="json")

            if flowchart_image_path and os.path.exists(flowchart_image_path):
                st.subheader("Flowchart:")
                st.image(flowchart_image_path)
            else:
                st.warning("⚠️ Flowchart image not found. Check graphviz installation.")
