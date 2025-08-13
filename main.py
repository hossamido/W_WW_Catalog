import streamlit as st
import pandas as pd
import ast
from pyvis.network import Network
import streamlit.components.v1 as components

# Define paths for the datasets
WATER_DATA_PATH = '/home/hossamido/Downloads/water partners/Water_Utilities-focused_partnerships.csv'
ALL_DATA_PATH = '/home/hossamido/Downloads/water partners/ot_partnerships_relations.csv'

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

def create_partnership_graph(df, central_node_name, filter_type):
    """Generates an interactive network graph of partnerships."""
    # Initialize the graph with a light background
    net = Network(height='600px', width='100%', bgcolor='#f0f2f6', font_color='black', notebook=True, cdn_resources='in_line')

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

# --- Streamlit App ---

st.set_page_config(layout="wide", page_title="OT Security Partnerships Explorer")

# --- Sidebar ---
st.sidebar.title("Data Source")
dataset_choice = st.sidebar.radio(
    "Select a dataset to explore:",
    ('Comprehensive View', 'Water Utilities Focus')
)

# Load data and set title based on choice
if dataset_choice == 'Water Utilities Focus':
    df = load_data(WATER_DATA_PATH, is_water_data=True)
    st.title("Water Utilities OT Security Partnerships Explorer")
    st.markdown("This view shows partnerships with a specific focus on or relevance to the water and wastewater sector.")
else: # 'Comprehensive View'
    df = load_data(ALL_DATA_PATH, is_water_data=False)
    st.title("Comprehensive OT Security Partnerships Explorer")
    st.markdown("This view shows all known partnerships between major automation vendors and OT security providers.")

st.sidebar.header("Filter Options")

# --- Sidebar Filters ---
filter_by = st.sidebar.radio(
    "Filter by:",
    ('Security Provider', 'Automation Company'),
    key='filter_type' # Add a key to avoid state issues
)

filtered_df = pd.DataFrame() # Initialize an empty dataframe
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

# --- Display Results ---
if filtered_df.empty or not central_node:
    st.info("Select a filter from the sidebar to see partnership details.")
else:
    for _, row in filtered_df.iterrows():
        with st.expander(f"**{row['automation_company']} & {row['security_provider']}**"):
            st.markdown(f"#### {row['marketed_solution']}")
            st.markdown(f"**Partnership Type:** {row['partnership_type']}")
            st.markdown(f"**Services Offered:** {row['services_offered']}")
            st.markdown(f"**Relevant Sectors:** {row['sectors']}")
            
            # Conditionally display service tags if the column exists and has data
            if 'service_tags' in df.columns and isinstance(row['service_tags'], list) and row['service_tags']:
                st.markdown(f"**Service Tags:** `{'`, `'.join(row['service_tags'])}`")

            st.markdown(f"**Source:** [Link]({row['sources']})")

    # --- Display Network Graph ---
    st.subheader("Partnership Network Graph")
    st.markdown("An interactive graph showing the selected company and its direct partners. Hover over an edge for details, and drag nodes to rearrange the layout.")
    
    graph_html = create_partnership_graph(filtered_df, central_node, filter_by)
    if graph_html:
        components.html(graph_html, height=620)
