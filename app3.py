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
}

# GPT prompt based on inputs
def get_tool_suggestions(data_sources, refresh_details, custom_requirement):
    user_message = f"""
You are a cloud architecture expert. Based on the following data, suggest the best ingestion, transformation, and visualization tools.

Strictly choose tools from: [Domo, Power BI, Sigma, dbt, Snowflake, Databricks, ADF, Tableau].

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
        {"role": "system", "content": "You are a cloud architecture expert. Provide low-cost, high-performance tool recommendations."},
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

# Estimate tool costs
def estimate_tool_costs(tool_suggestions, usage_tier):
    cost_data = []
    for category, tool_info in tool_suggestions.items():
        tool_name = tool_info.get("tool")
        if tool_name in TOOL_COSTS:
            cost = TOOL_COSTS[tool_name].get(usage_tier, "N/A")
        else:
            cost = "N/A"
        cost_data.append({
            "Tool": tool_name,
            "Category": category.capitalize(),
            "Estimated Monthly Cost ($)": cost
        })
    return pd.DataFrame(cost_data)

# Generate flowchart
def generate_flowchart_and_json(data_sources, refresh_details, custom_requirement):
    tool_suggestions = get_tool_suggestions(data_sources, refresh_details, custom_requirement)
    if not tool_suggestions:
        return None, None, None

    flowchart = Digraph(format='png', graph_attr={'rankdir': 'LR'}, node_attr={'shape': 'box'})
    flowchart.node("Data Sources", "\n".join(data_sources))

    ingestion_tool = tool_suggestions.get('ingestion', {}).get('tool', 'Unknown')
    transformation_tool = tool_suggestions.get('transformation', {}).get('tool', 'Unknown')
    visualization_tool = tool_suggestions.get('visualization', {}).get('tool', 'Unknown')

    flowchart.node("Ingestion", f"{ingestion_tool} (Ingestion)")
    flowchart.node("Transformation", f"{transformation_tool} (Transformation)")
    flowchart.node("Visualization", f"{visualization_tool} (Visualization)")

    flowchart.edge("Data Sources", "Ingestion")
    flowchart.edge("Ingestion", "Transformation")
    flowchart.edge("Transformation", "Visualization")

    return json.dumps(tool_suggestions, indent=4), flowchart.source, tool_suggestions

# Streamlit UI
st.title("🔧 Data Architecture Tool Suggestion")

st.header("Step 1: Input Data Sources")
data_sources = st.multiselect(
    "Select Data Sources:",
    options=["Google Ads", "Google Analytics", "SQL Database", "Excel Files", "Social Media"],
    default=[]
)

st.header("Step 2: Input Dataset Configuration")

historical_load_input = st.text_input("Historical Load (e.g., '20 million'):")
monthly_increase_input = st.text_input("Monthly Increase (e.g., '50 thousand'):")
datasets_input = st.text_input("Number of Datasets:")
daily_refresh_input = st.text_input("Daily Refresh Datasets:")
three_hour_refresh_input = st.text_input("3-Hour Refresh Datasets:")
hourly_refresh_input = st.text_input("Hourly Refresh Datasets:")
real_time_refresh_input = st.text_input("15-Min Refresh Datasets:")

historical_load = parse_number_input(historical_load_input) or 0
monthly_increase = parse_number_input(monthly_increase_input) or 0
datasets = parse_number_input(datasets_input) or 0
daily_refresh = parse_number_input(daily_refresh_input) or 0
three_hour_refresh = parse_number_input(three_hour_refresh_input) or 0
hourly_refresh = parse_number_input(hourly_refresh_input) or 0
real_time_refresh = parse_number_input(real_time_refresh_input) or 0

st.header("Step 3: Select Usage Tier")
usage_tier = st.selectbox("Select Usage Tier:", ["Small", "Medium", "Large"], index=1)

st.header("Step 4: Describe Custom Requirement")
custom_requirement = st.text_area(
    "Describe your custom requirement:",
    placeholder="Example: Need a scalable solution for real-time data ingestion and visualization.",
    height=150
)

if st.button("🚀 Generate Flowchart and Cost Estimate"):
    # Check mandatory fields
    if not data_sources:
        st.error("❌ Please select at least one data source.")
    elif not (historical_load and monthly_increase and datasets):
        st.error("❌ Please fill out all dataset configuration fields.")
    elif not custom_requirement.strip():
        st.error("❌ Please describe your custom requirement.")
    else:
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
            json_response, graphviz_code, tool_suggestions = generate_flowchart_and_json(data_sources, refresh_details, custom_requirement)

        if not json_response or "Error" in str(json_response):
            st.error("❌ Failed to generate JSON response.")
        else:
            st.success("✅ Flowchart and JSON generated successfully!")

            st.subheader("Tool Suggestions (JSON):")
            st.code(json_response, language="json")

            if graphviz_code:
                st.subheader("Flowchart:")
                st.graphviz_chart(graphviz_code)
            else:
                st.warning("⚠️ Flowchart generation failed.")

            st.subheader(f"Estimated Monthly Cost ({usage_tier} Tier):")
            cost_df = estimate_tool_costs(tool_suggestions, usage_tier)
            st.table(cost_df)
