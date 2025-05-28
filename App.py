# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "neo4j-graphrag",
#     "rdflib",
#     "requests",
#     "rich",
#     "ruff",
#     "streamlit",
# ]
# ///
# app.py
import streamlit as st


# Set page configuration (only in the main app file)
st.set_page_config(
    page_title="Organized Multi-Page App Demo",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Define your pages using st.Page
# Pass the imported module directly. Streamlit will look for the
# entry point (e.g., 'main' function) within that module.
pages = {
    "General": [
        st.Page('pages/Home.py', title="Home", icon="🏠"),
        st.Page('pages/Dashboard.py', title="Dashboard", icon="📈"),
        st.Page('pages/Analysis.py', title="Analysis", icon="📊")
    ]
}

# Run the navigation
pg = st.navigation(pages)
pg.run()
