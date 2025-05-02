import streamlit as st
import openai
import graphviz

# Set your OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]  # Safer for deployment. Or directly paste if testing.

# Title
st.title("🛠️ Data Architecture Designer")

# Sidebar for user inputs
st.sidebar.header("Choose Components")

data_sources = st.sidebar.multiselect(
    "Select Data Sources",
    ["MySQL", "PostgreSQL", "Kafka", "S3", "Google Pub/Sub", "Third-party API"]
)

ingestion_tools = st.sidebar.multiselect(
    "Select Ingestion Tools",
    ["Fivetran", "Kafka Connect", "AWS DMS", "Custom SDK", "StreamSets"]
)

transformation_tools = st.sidebar.multiselect(
    "Select Transformation Tools",
    ["DBT", "Apache Spark", "Apache Flink", "Airflow", "AWS Glue"]
)

storage_tools = st.sidebar.multiselect(
    "Select Storage Options",
    ["AWS S3", "Azure Blob Storage", "Snowflake", "Amazon Redshift", "BigQuery"]
)

visualization_tools = st.sidebar.multiselect(
    "Select Visualization Tools",
    ["Power BI", "Tableau", "Looker", "Superset"]
)

if st.sidebar.button("Generate Architecture"):
    # Create a simple JSON-like structure
    architecture_json = {
        "data_sources": data_sources,
        "ingestion_tools": ingestion_tools,
        "transformation_tools": transformation_tools,
        "storage_tools": storage_tools,
        "visualization_tools": visualization_tools,
    }

    st.subheader("📄 Architecture JSON")
    st.json(architecture_json)

    st.subheader("🔵 Complex Data Architecture Flowchart")

    # Create a complex flowchart
    def generate_complex_flowchart(architecture):
        dot = graphviz.Digraph(comment="Complex Data Architecture", format="png")

        # Sources
        for source in architecture["data_sources"]:
            dot.node(source, source, shape='box')

        # Ingestion Tools
        for ingestion in architecture["ingestion_tools"]:
            dot.node(ingestion, ingestion, shape='parallelogram')

        # Transformation Tools
        for transform in architecture["transformation_tools"]:
            dot.node(transform, transform, shape='ellipse')

        # Storage
        for storage in architecture["storage_tools"]:
            dot.node(storage, storage, shape='cylinder')

        # Visualization
        for viz in architecture["visualization_tools"]:
            dot.node(viz, viz, shape='box3d')

        # Monitoring
        dot.node("Monitoring", "Monitoring System", shape='octagon')
        
        # Zones
        dot.node("Batch Zone", "Batch Processing Zone", shape="rectangle", style="dashed")
        dot.node("Streaming Zone", "Real-time Processing Zone", shape="rectangle", style="dashed")

        # Edges: Data Sources → Ingestion
        for source in architecture["data_sources"]:
            for ingestion in architecture["ingestion_tools"]:
                dot.edge(source, ingestion)

        # Ingestion → Batch or Streaming
        for ingestion in architecture["ingestion_tools"]:
            dot.edge(ingestion, "Batch Zone")
            dot.edge(ingestion, "Streaming Zone")

        # Batch Zone → Storage → Transformation → Storage
        for storage in architecture["storage_tools"]:
            for transform in architecture["transformation_tools"]:
                dot.edge("Batch Zone", storage)
                dot.edge(storage, transform)
                dot.edge(transform, storage)

        # Streaming Zone → Transformation → Storage
        for transform in architecture["transformation_tools"]:
            for storage in architecture["storage_tools"]:
                dot.edge("Streaming Zone", transform)
                dot.edge(transform, storage)

        # Storage → Visualization
        for storage in architecture["storage_tools"]:
            for viz in architecture["visualization_tools"]:
                dot.edge(storage, viz)

        # Monitoring connects to everything
        for ingestion in architecture["ingestion_tools"]:
            dot.edge(ingestion, "Monitoring", style="dotted")
        for transform in architecture["transformation_tools"]:
            dot.edge(transform, "Monitoring", style="dotted")
        for storage in architecture["storage_tools"]:
            dot.edge(storage, "Monitoring", style="dotted")
        for viz in architecture["visualization_tools"]:
            dot.edge(viz, "Monitoring", style="dotted")

        return dot

    # Generate and render
    flowchart = generate_complex_flowchart(architecture_json)
    st.graphviz_chart(flowchart)

    # Cost estimate
    st.subheader("💰 Rough Cost Estimation")
    est_cost = (
        len(data_sources) * 10
        + len(ingestion_tools) * 20
        + len(transformation_tools) * 30
        + len(storage_tools) * 40
        + len(visualization_tools) * 15
    )
    st.info(f"Estimated Monthly Infrastructure Cost: **~${est_cost}K**")
