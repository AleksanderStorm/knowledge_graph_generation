# pages/Dashboard.py
import streamlit as st
import pandas as pd
import numpy as np

def main():
    st.write("This page shows some illustrative data and a simple chart.")

    # Create some mock data
    data = {
        'Category': ['A', 'B', 'C', 'D', 'E'],
        'Value': np.random.randint(10, 100, 5),
        'Growth': np.random.rand(5) * 10
    }
    df = pd.DataFrame(data)

    st.subheader("Overview Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sales", "$1,200K", "12%")
    with col2:
        st.metric("New Users", "5,000", "-8%")
    with col3:
        st.metric("Conversion Rate", "3.5%", "0.5%")

    st.subheader("Data Table")
    st.dataframe(df)

    st.subheader("Value Distribution Chart")
    st.bar_chart(df.set_index('Category')['Value'])

    st.write("---")
    st.info("This is a placeholder dashboard. You can integrate real data and more complex visualizations here.")

if __name__ in ("__main__", "__page__"):
    main()