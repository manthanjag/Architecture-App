import os
import streamlit as st
import openai
import json
import graphviz
import re
import pandas as pd
from graphviz import Digraph

# Set OpenAI API key
openai.api_key = st.secrets["key"]

# Function to parse human-readable numbers
def parse_number_input(input_text):
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
    return None

# Tool cost estimates
TOOL_COSTS = {
    "Domo": {"Small": 500, "Medium": 2000, "Large": 5000},
    "Power BI": {"Small": 200, "Medium": 1000, "Large": 3000},
    "Sigma": {"Small": 300, "Medium": 1500, "Large": 4000},
    "dbt": {"Small": 100, "Medium": 500, "Large": 2000},
    "Snowflake": {"Small": 300, "Medium": 2000, "Large": 8000},
    "Databricks": {"Small": 500, "Medium": 2500, "Large": 9000},
    "ADF": {"Small": 100, "Medium": 800, "Large": 2500},
    "Tableau": {"Small": 300, "Medium": 1500, "Large": 4500},
    "Kafka": {"Small": 400, "Medium": 1500, "Large": 5000},
    "Fivetran": {"Small": 300, "Medium": 1200, "Large": 4000},
    "Airbyte": {"Small": 200, "Medium": 800, "Large": 3000},
}

# GPT prompt
def get_tool_suggestions(data_sources, refresh_details, custom_requirement):
    user_message = f"""
You are a cloud architecture expert. Based on the following data, suggest the best ingestion, transformation, and visualization tools.

You are free to recommend any tools that best fit the use case (no restriction to any list). Prioritize tools that are scalable, industry-standard, and cost-effective.

Dataset Details:
- Data Sources: {", ".join(data_sources)}
- Historical Load: {refresh_details['historical_load']}
- Monthly Increase: {refresh_details['monthly_increase']}
- Number of Datasets: {refresh_details['datasets']}
- Dataset Refresh Rates:
  - {refresh_details['daily_refresh']} datasets refresh daily
  - {refresh_details['three_hour_refresh']} datasets refresh every 3 hours
  - {refresh_details['hourly_refresh']} datasets refresh hourly
  - {refresh_details['real_time_refresh']} datasets refresh every 15 minutes

Custom Requirement:
{custom_requirement}

Respond ONLY in this JSON format:
{{
    "ingestion": {{"tool": "ToolName"}},
    "transformation": {{"tool": "ToolName"}},
    "visualization": {{"tool": "ToolName"}}
}}
"""
    messages = [
        {"role": "system", "content": "You are a cloud architecture expert. Provide cost-effective, high-performance tool recommendations."},
        {"role": "user", "content": user_message}
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
        st.error("❌ GPT returned an invalid response.")
        return None

# Generate complex flowchart
def generate_complex_flowchart(data_sources, tool_suggestions):
    flowchart = Digraph(format='png', graph_attr={'rankdir': 'LR'}, node_attr={'shape': 'box', 'style': 'rounded,filled', 'fillcolor': 'lightgrey'})

    # Define Tools
    ingestion_tool = tool_suggestions.get('ingestion', {}).get('tool', 'Unknown')
    transformation_tool = tool_suggestions.get('transformation', {}).get('tool', 'Unknown')
    visualization_tool = tool_suggestions.get('visualization', {}).get('tool', 'Unknown')

    # Data Sources
    for source in data_sources:
        flowchart.node(f"source_{source}", source, fillcolor='lightblue')

    # Layers
    flowchart.node("Ingestion Layer", f"{ingestion_tool}\n(Ingestion)", fillcolor='lightpink')
    flowchart.node("Landing Zone", "Landing Zone\n(S3 / Blob Storage)", fillcolor='lightyellow')
    flowchart.node("Data Warehouse", "Data Warehouse\n(Redshift / Snowflake)", fillcolor='lightyellow')
    flowchart.node("Streaming Layer", "Streaming Layer\n(Kafka / Flink / KSQL)", fillcolor='lightyellow')
    flowchart.node("Transformation Layer", f"{transformation_tool}\n(Transformation)", fillcolor='lightgreen')
    flowchart.node("Feature Store", "Feature Store\n(ML Features)", fillcolor='lightyellow')
    flowchart.node("BI Layer", f"{visualization_tool}\n(BI Visualization)", fillcolor='lightpink')
    flowchart.node("Analytics/ML", "Analytics Layer\n(Data Science & ML)", fillcolor='lightgreen')
    flowchart.node("Monitoring", "Monitoring & Alerts\n(Elastic / Kibana / Grafana)", fillcolor='orange')

    # Flow from sources
    for source in data_sources:
        flowchart.edge(f"source_{source}", "Ingestion Layer")

    # Connections
    flowchart.edge("Ingestion Layer", "Landing Zone")
    flowchart.edge("Ingestion Layer", "Streaming Layer")
    flowchart.edge("Landing Zone", "Data Warehouse")
    flowchart.edge("Streaming Layer", "Transformation Layer")
    flowchart.edge("Data Warehouse", "Transformation Layer")
    flowchart.edge("Transformation Layer", "Feature Store")
    flowchart.edge("Transformation Layer", "BI Layer")
    flowchart.edge("Feature Store", "Analytics/ML")
    flowchart.edge("Analytics/ML", "BI Layer")
    flowchart.edge("Streaming Layer", "Monitoring")
    flowchart.edge("Transformation Layer", "Monitoring")
    flowchart.edge("Landing Zone", "Monitoring")

    return flowchart

# Streamlit App
st.title("🔧 Data Architecture Tool Suggestion App")

with st.form("input_form"):
    st.header("Step 1: Select Data Sources")
    data_sources = st.multiselect(
        "Select Data Sources:",
        options=[
            "Google Ads", "Google Analytics", "SQL Database", "Excel Files", "Social Media",
            "AWS S3", "Salesforce", "Shopify", "PostgreSQL", "MongoDB", "Kafka Stream", "IoT Devices"
        ],
    )

    st.header("Step 2: Describe Custom Requirement")
    custom_requirement = st.text_area(
        "Describe your custom requirement:",
        placeholder="Example: Need a scalable solution for real-time data ingestion and visualization.",
        height=150
    )

    st.header("Step 3: Input Dataset Configuration")
    historical_load_input = st.text_input("Historical Load (e.g., '20 million'):")
    monthly_increase_input = st.text_input("Monthly Increase (e.g., '50 thousand'):")
    datasets_input = st.text_input("Number of Datasets:")
    daily_refresh_input = st.text_input("Daily Refresh Datasets:")
    three_hour_refresh_input = st.text_input("3-Hour Refresh Datasets:")
    hourly_refresh_input = st.text_input("Hourly Refresh Datasets:")
    real_time_refresh_input = st.text_input("15-Min Refresh Datasets:")

    submit_button = st.form_submit_button("🚀 Generate Flowchart")

# Form submission handling
if submit_button:
    if not data_sources:
        st.error("❌ Please select at least one data source.")
    elif not custom_requirement.strip():
        st.error("❌ Please describe your custom requirement.")
    elif not (historical_load_input and monthly_increase_input and datasets_input and daily_refresh_input and three_hour_refresh_input and hourly_refresh_input and real_time_refresh_input):
        st.error("❌ Please fill out all dataset configuration fields.")
    else:
        historical_load = parse_number_input(historical_load_input) or 0
        monthly_increase = parse_number_input(monthly_increase_input) or 0
        datasets = parse_number_input(datasets_input) or 0
        daily_refresh = parse_number_input(daily_refresh_input) or 0
        three_hour_refresh = parse_number_input(three_hour_refresh_input) or 0
        hourly_refresh = parse_number_input(hourly_refresh_input) or 0
        real_time_refresh = parse_number_input(real_time_refresh_input) or 0

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
            tool_suggestions = get_tool_suggestions(data_sources, refresh_details, custom_requirement)

            if tool_suggestions:
                st.success("✅ Tool suggestions generated successfully!")

                flowchart = generate_complex_flowchart(data_sources, tool_suggestions)

                # Commented out: JSON response
                # json_response = json.dumps(tool_suggestions, indent=4)
                # st.subheader("Tool Suggestions (JSON):")
                # st.code(json_response, language="json")

                st.subheader("Architecture Flowchart:")
                st.graphviz_chart(flowchart.source)

                # Commented out: Cost estimation
                # st.subheader("Estimated Monthly Costs:")
                # cost_df = estimate_tool_costs(tool_suggestions)
                # st.table(cost_df)

            else:
                st.error("❌ Failed to generate tool suggestions.")
