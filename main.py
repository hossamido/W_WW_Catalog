import streamlit as st
import pandas as pd
import ast
from pyvis.network import Network
import streamlit.components.v1 as components

# Define paths for the datasets
WATER_DATA_PATH = 'Water_Utilities-focused_partnerships.csv'
ALL_DATA_PATH = 'ot_partnerships_relations.csv'
SERVICE_DATA_PATH = 'service_to_pera_and_regs.csv'

@st.cache_data
def load_data(file_path, is_water_data=False):
    """
    Loads and caches partnership data from a given CSV file.
    - Handles specific parsing for the water-focused dataset.
    """
    try:
        if is_water_data:
            # The water-focused CSV has an unnamed index column
            df = pd.read_csv(file_path, index_col=0)
        else:
            df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Error: The file was not found at {file_path}")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        st.stop()

    if is_water_data:
        # Safely parse the string representation of a list in the 'service_tags' column
        def parse_tags(tags_str):
            if pd.isna(tags_str):
                return []
            try:
                return ast.literal_eval(tags_str)
            except (ValueError, SyntaxError):
                return [] # Return an empty list for malformed strings
        df['service_tags'] = df['service_tags'].apply(parse_tags)
    else:
        # The comprehensive dataset might have missing values
        df.fillna('Not specified', inplace=True)

    return df

@st.cache_data
def load_service_data(file_path):
    """
    Loads and caches the security services data from the CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        df.fillna('Not specified', inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: The file was not found at {file_path}")
        st.stop()
    return None

def create_partnership_graph(df, central_node_name, filter_type):
    """Generates an interactive network graph of partnerships."""
    # Initialize the graph with a light background
    net = Network(height='450px', width='100%', bgcolor='#f0f2f6', font_color='black', notebook=True, cdn_resources='in_line')

    # Set physics layout for a more spread-out, readable graph
    net.set_options("""
    var options = {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -30000,
          "centralGravity": 0.3,
          "springLength": 150
        },
        "minVelocity": 0.75
      }
    }
    """)

    # Add the central node with distinct styling
    net.add_node(central_node_name, label=central_node_name, color='#ff4b4b', size=30, font={'size': 20})

    # Determine the column for partner companies
    partner_col = 'automation_company' if filter_type == 'Security Provider' else 'security_provider'

    # Add partner nodes and edges
    for _, row in df.iterrows():
        partner_name = row[partner_col]
        # Add partner node (pyvis handles duplicates automatically)
        net.add_node(partner_name, label=partner_name, size=20)
        # Add an edge with a descriptive tooltip
        edge_title = f"Solution: {row['marketed_solution']}<br>Type: {row['partnership_type']}"
        net.add_edge(central_node_name, partner_name, title=edge_title)

    # Generate and return the HTML source code for the graph
    try:
        # Save to a temporary file and read it back for embedding
        path = '/tmp'
        file_name = f'{path}/partnership_graph.html'
        net.save_graph(file_name)
        with open(file_name, 'r', encoding='utf-8') as html_file:
            return html_file.read()
    except Exception as e:
        st.error(f"Could not generate graph: {e}")
        return None

def create_full_bipartite_graph(df):
    """Generates an interactive bipartite-style network graph for the entire dataset."""
    net = Network(height='300px', width='400px', bgcolor='#f0f2f6', font_color='black', notebook=True, cdn_resources='in_line', directed=False)

    # Set physics for a force-directed layout which works well for bipartite graphs
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -100,
          "centralGravity": 0.01,
          "springLength": 200,
          "springConstant": 0.08,
          "avoidOverlap": 1
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      }
    }
    """)

    # Get unique nodes for each partition
    automation_nodes = df['automation_company'].unique()
    security_nodes = df['security_provider'].unique()

    # Add nodes with distinct styles
    for node in automation_nodes:
        net.add_node(node, label=node, color='#1f77b4', shape='box', size=25, title='Automation Company')
    for node in security_nodes:
        net.add_node(node, label=node, color='#2ca02c', shape='dot', size=25, title='Security Provider')

    # Add edges from the dataframe
    for _, row in df.iterrows():
        edge_title = f"Solution: {row['marketed_solution']}<br>Type: {row['partnership_type']}"
        net.add_edge(row['automation_company'], row['security_provider'], title=edge_title)

    try:
        file_name = '/tmp/full_partnership_graph.html'
        net.save_graph(file_name)
        with open(file_name, 'r', encoding='utf-8') as html_file:
            return html_file.read()
    except Exception as e:
        st.error(f"Could not generate full graph: {e}")
        return None

# --- Streamlit App ---

st.set_page_config(layout="wide", page_title="OT Security Partnerships Explorer")

# --- Main Sidebar Selection ---
st.sidebar.title("OT Security Catalog")
st.sidebar.markdown("Created by: **Ahmed Hemida**")
st.sidebar.markdown("On Aug 13, 2025")
explorer_choice = st.sidebar.radio(
    "Select an explorer:",
    ('Partnerships', 'Security Services')
)

if explorer_choice == 'Partnerships':
    # --- Partnership Explorer Logic ---
    st.sidebar.header("Partnership View Options")
    dataset_choice = st.sidebar.radio(
        "Select a dataset to explore:",
        ('Comprehensive View', 'Water Utilities Focus')
    )

    if dataset_choice == 'Water Utilities Focus':
        df = load_data(WATER_DATA_PATH, is_water_data=True)
        st.title("Water Utilities OT Security Partnerships Explorer")
        st.markdown("This view shows partnerships with a specific focus on or relevance to the water and wastewater sector.")
    else: # 'Comprehensive View'
        df = load_data(ALL_DATA_PATH, is_water_data=False)
        st.title("Comprehensive OT Security Partnerships Explorer")
        st.markdown("This view shows all known partnerships between major automation vendors and OT security providers.")

    view_mode = "By Company"
    if dataset_choice == 'Water Utilities Focus':
        view_mode = st.sidebar.radio("View Mode", ("By Company", "Full Network"), key='water_view_mode')

    if view_mode == "Full Network":
        st.header("Full Partnership Network (Water & Wastewater Focus)")
        st.markdown("This graph shows all automation companies (boxes) and security providers (circles) with partnerships relevant to the water sector. Hover over an edge to see details, and drag nodes to rearrange the layout.")
        graph_html = create_full_bipartite_graph(df)
        if graph_html:
            components.html(graph_html, height=620)
    else:
        st.sidebar.header("Filter Options")
        filter_by = st.sidebar.radio("Filter by:", ('Security Provider', 'Automation Company'), key='filter_type')

        filtered_df = pd.DataFrame()
        central_node = None

        if filter_by == 'Security Provider':
            providers = sorted(df['security_provider'].unique())
            selected_provider = st.sidebar.selectbox("Select a Security Provider", providers, key='provider_select')
            central_node = selected_provider
            st.header(f"Automation companies partnering with: {central_node}")
            filtered_df = df[df['security_provider'] == central_node]

        elif filter_by == 'Automation Company':
            companies = sorted(df['automation_company'].unique())
            selected_company = st.sidebar.selectbox("Select an Automation Company", companies, key='company_select')
            central_node = selected_company
            st.header(f"Security providers partnering with: {central_node}")
            filtered_df = df[df['automation_company'] == central_node]

        if filtered_df.empty or not central_node:
            st.info("Select a filter from the sidebar to see partnership details.")
        else:
            for _, row in filtered_df.iterrows():
                with st.expander(f"**{row['automation_company']} & {row['security_provider']}**"):
                    st.markdown(f"#### {row['marketed_solution']}")
                    st.markdown(f"**Partnership Type:** {row['partnership_type']}")
                    st.markdown(f"**Services Offered:** {row['services_offered']}")
                    st.markdown(f"**Relevant Sectors:** {row['sectors']}")
                    if 'service_tags' in df.columns and isinstance(row['service_tags'], list) and row['service_tags']:
                        st.markdown(f"**Service Tags:** `{'`, `'.join(row['service_tags'])}`")
                    st.markdown(f"**Source:** [Link]({row['sources']})")

            st.subheader("Partnership Network Graph")
            st.markdown("An interactive graph showing the selected company and its direct partners. Hover over an edge for details, and drag nodes to rearrange the layout.")
            graph_html = create_partnership_graph(filtered_df, central_node, filter_by)
            if graph_html:
                components.html(graph_html, height=470)

elif explorer_choice == 'Security Services':
    # --- Security Services Explorer Logic ---
    st.title("Security Services Explorer")
    st.markdown("Explore security services, the companies that provide them, and their alignment with industry standards.")
    
    service_df = load_service_data(SERVICE_DATA_PATH)
    
    st.sidebar.header("Service View Options")
    services = sorted(service_df['Security service'].unique())
    selected_service = st.sidebar.selectbox("Select a Security Service", services)
    
    # Display details for the selected service
    if selected_service:
        service_details = service_df[service_df['Security service'] == selected_service].iloc[0]
        
        st.header(f"Details for: {selected_service}")
        
        with st.container(border=True):
            st.subheader("Who provides it?")
            providers_list = [p.strip() for p in service_details['Who provides it'].split(',')]
            for provider in providers_list:
                st.markdown(f"- {provider}")

        with st.container(border=True):
            st.subheader("Relevant PERA Layer(s)")
            st.markdown(service_details['PERA layer(s)'])

        with st.container(border=True):
            st.subheader("Regulation / Guidance Alignment")
            st.markdown(service_details['Regulation / guidance alignment'])
