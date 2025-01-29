import os
import streamlit as st
import openai
import json
from graphviz import Digraph


# Set your OpenAI API key
openai.api_key = st.secrets["key"]
# Function to get tool suggestions from GPT
def get_tool_suggestions(data_sources, refresh_details):
    messages = [
        {
            "role": "system",
            "content": "You are a cloud architecture expert. Provide low-cost, high-performance tool recommendations for ingestion, transformation, and visualization tasks from the following list only: Domo, Power BI, Sigma, dbt, Snowflake, Databricks, ADF, Tableau."
        },
        {
            "role": "user",
            "content": f"""
        Based on the following data sources and refresh configuration, suggest one tool for each task (ingestion, transformation, visualization) strictly from this list:
        [Domo, Power BI, Sigma, dbt, Snowflake, Databricks, ADF, Tableau].
        The output must follow this JSON structure:

        {{
            "ingestion": {{"tool": "ToolName"}},
            "transformation": {{"tool": "ToolName"}},
            "visualization": {{"tool": "ToolName"}}
        }}

        Data Sources: {", ".join(data_sources)}
        Refresh Configuration:
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

    return response.choices[0].message['content']

# Function to generate the flowchart and JSON
def generate_flowchart_and_json(data_sources, refresh_details):
    gpt_response = get_tool_suggestions(data_sources, refresh_details)

    try:
        tool_suggestions = json.loads(gpt_response)
    except json.JSONDecodeError:
        return "Error parsing GPT response. Please try again.", None

    # Create the flowchart using Graphviz
    flowchart = Digraph(format='png', graph_attr={'rankdir': 'LR', 'fontsize': '10'}, node_attr={'shape': 'box', 'fontsize': '10'})

    # Combine all data sources into a single node
    data_sources_text = "\n".join(data_sources)
    flowchart.node("Data Sources", f"Data Sources:\n{data_sources_text}")

    # Add nodes based on GPT suggestions
    flowchart.node("Ingestion", f"{tool_suggestions['ingestion']['tool']} (Ingestion)")
    flowchart.node("Transformation", f"{tool_suggestions['transformation']['tool']} (Transformation)")
    flowchart.node("Visualization", f"{tool_suggestions['visualization']['tool']} (Visualization)")

    # Add Edges
    flowchart.edge("Data Sources", "Ingestion")
    flowchart.edge("Ingestion", "Transformation")
    flowchart.edge("Transformation", "Visualization")

    #output_path = '/mnt/data/data_architecture_flowchart'
    #flowchart.render(output_path, view=False)

    #return json.dumps(tool_suggestions, indent=4), f"{output_path}.png"

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

        if "Error" in json_response:
            st.error(json_response)
        else:
            st.success("Flowchart and JSON generated successfully!")
            st.subheader("Tool Suggestions (JSON):")
            st.code(json_response, language="json")

            st.subheader("Flowchart:")
            st.image(flowchart_image_path)


#streamlit run app.py
