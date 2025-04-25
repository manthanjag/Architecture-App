import os
import streamlit as st
import openai
import json
import graphviz
import re
from graphviz import Digraph

# Set OpenAI API key from secrets
openai.api_key = st.secrets["key"]

# Function to parse human-readable number inputs (e.g., "20 million" → 20000000)
def parse_number_input(input_text):
    """
    Converts human-readable numbers (e.g., '20 million', '50 thousand') into integers.
    """
    input_text = input_text.lower().replace(",", "").strip()
    number_map = {
        "k": 1_000, "thousand": 1_000,
        "m": 1_000_000, "million": 1_000_000,
        "b": 1_000_000_000, "billion": 1_000_000_000
    }

    match = re.match(r"(\d+(?:\.\d+)?)\s*([a-z]+)?", input_text)
    if match:
        num, unit = match.groups()
        num = float(num)
        multiplier = number_map.get(unit, 1)
        return int(num * multiplier)
    
    return None  # Invalid input

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
        return json.dumps(tool_suggestions, indent=4), flowchart  # <-- CHANGED THIS FROM NONE TO flowchart
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

    # Replace the number inputs with text inputs for human-readable format
    historical_load_input = st.text_input("Historical Load (e.g., '20 million'):", "20 million")
    monthly_increase_input = st.text_input("Monthly Increase (e.g., '50 thousand'):", "50 thousand")
    datasets_input = st.text_input("Number of Datasets:", "20")
    daily_refresh_input = st.text_input("Daily Refresh Datasets:", "10")
    three_hour_refresh_input = st.text_input("3-Hour Refresh Datasets:", "5")
    hourly_refresh_input = st.text_input("Hourly Refresh Datasets:", "3")
    real_time_refresh_input = st.text_input("15-Min Refresh Datasets:", "2")

    # Convert user-friendly inputs into integers
    historical_load = parse_number_input(historical_load_input) or 0
    monthly_increase = parse_number_input(monthly_increase_input) or 0
    datasets = parse_number_input(datasets_input) or 0
    daily_refresh = parse_number_input(daily_refresh_input) or 0
    three_hour_refresh = parse_number_input(three_hour_refresh_input) or 0
    hourly_refresh = parse_number_input(hourly_refresh_input) or 0
    real_time_refresh = parse_number_input(real_time_refresh_input) or 0

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
            json_response, flowchart_object = generate_flowchart_and_json(data_sources, refresh_details)

        if not json_response or "Error" in json_response:
            st.error("❌ Failed to generate JSON response.")
        else:
            st.success("✅ Flowchart and JSON generated successfully!")
            st.subheader("Tool Suggestions (JSON):")
            st.code(json_response, language="json")

            if flowchart_object:
                st.subheader("Flowchart:")
                st.graphviz_chart(flowchart_object.source)
            else:
                st.warning("⚠️ Flowchart could not be generated.")
