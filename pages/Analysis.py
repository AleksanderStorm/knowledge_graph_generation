# pages/Analysis.py
import streamlit as st

def main():
    st.write("This page allows for some basic text input and analysis.")

    st.subheader("Text Input Example")
    user_text = st.text_area("Enter some text for analysis:", "Type your thoughts here...")

    if st.button("Analyze Text"):
        if user_text:
            word_count = len(user_text.split())
            char_count = len(user_text)
            st.success("Text analysis complete!")
            st.write(f"**Word Count:** {word_count}")
            st.write(f"**Character Count (including spaces):** {char_count}")
            st.write("---")
            st.subheader("Your Input:")
            st.code(user_text)
        else:
            st.warning("Please enter some text to analyze.")

    st.write("---")
    st.info("You can replace this with more sophisticated NLP models or data processing tasks.")

if __name__ in ("__main__", "__page__"):
    main()