import streamlit as st
import pandas as pd

# Set the path to the comprehensive partnership data file
DATA_PATH = '/home/hossamido/Downloads/water partners/ot_partnerships_relations.csv'

@st.cache_data
def load_data():
    """
    Loads and caches the partnership data from the CSV file.
    """
    try:
        # This CSV does not have a dedicated index column, so we don't use index_col
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        st.error(f"Error: The file was not found at {DATA_PATH}")
        st.stop()
    # Fill any potential missing values with a placeholder for cleaner display
    df.fillna('Not specified', inplace=True)
    return df

# --- Streamlit App ---

st.set_page_config(layout="wide", page_title="All OT Security Partnerships Explorer")

st.title("Comprehensive OT Security Partnerships Explorer")
st.markdown("Use the filters in the sidebar to explore the full range of partnerships between automation companies and OT security providers.")

df = load_data()

st.sidebar.header("Filter Options")

# --- Sidebar Filters ---
filter_by = st.sidebar.radio(
    "Filter by:",
    ('Security Provider', 'Automation Company')
)

filtered_df = pd.DataFrame() # Initialize an empty dataframe

if filter_by == 'Security Provider':
    # Get a sorted, unique list of providers
    providers = sorted(df['security_provider'].unique())
    selected_provider = st.sidebar.selectbox("Select a Security Provider", providers)
    st.header(f"Automation companies partnering with: {selected_provider}")
    filtered_df = df[df['security_provider'] == selected_provider]

elif filter_by == 'Automation Company':
    # Get a sorted, unique list of companies
    companies = sorted(df['automation_company'].unique())
    selected_company = st.sidebar.selectbox("Select an Automation Company", companies)
    st.header(f"Security providers partnering with: {selected_company}")
    filtered_df = df[df['automation_company'] == selected_company]

# --- Display Results ---
if filtered_df.empty:
    st.info("Select a filter from the sidebar to see partnership details.")
else:
    # Use iterrows() to display each partnership in the filtered set
    for _, row in filtered_df.iterrows():
        with st.expander(f"**{row['automation_company']} & {row['security_provider']}**"):
            st.markdown(f"#### {row['marketed_solution']}")
            st.markdown(f"**Partnership Type:** {row['partnership_type']}")
            st.markdown(f"**Services Offered:** {row['services_offered']}")
            st.markdown(f"**Relevant Sectors:** {row['sectors']}")
            st.markdown(f"**Source:** [Link]({row['sources']})")
