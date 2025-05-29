# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb",
# ]
# ///

# pages/Home.py
import streamlit as st

def main():
    st.title("Welcome to the Organized Multi-Page App! 👋")

    st.markdown(
        """
        This demo showcases a multi-page Streamlit app where:
        - All page content files are in the `pages/` directory.
        - `app.py` uses `st.navigation` and `st.Page` for explicit control.
        - Each page file has an `if __name__ in ("__main__", "__page__"): main()` block.

        **👈 Select a page from the sidebar** to explore.

        ### What's inside?
        - **Home Page (`Home.py`):** This page you're currently viewing.
        - **Dashboard Page (`Dashboard.py`):** A simple page with a chart and some metrics.
        - **Analysis Page (`Analysis.py`):** A page demonstrating text input and display.
        """
    )

    st.write("---")
    st.subheader("Why this setup?")
    st.info(
        """
        This structure provides a great balance:
        - **Organization:** All pages are neatly grouped in `pages/`.
        - **Control:** `app.py` dictates the order, titles, and icons.
        - **Modularity:** Each page can be run independently for testing.
        """
    )

    st.markdown(
        """
        Feel free to explore and adapt this structure for your own Streamlit projects!
        """
    )

if __name__ in ("__main__", "__page__"):
    main()