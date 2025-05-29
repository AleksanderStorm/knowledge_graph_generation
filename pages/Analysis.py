# pages/Analysis.py
import streamlit as st
import spacy # Uncomment if you want to use NLP features
from spacy import displacy
from utils.nlp_utils import extract_entity_pairs,extract_relation  # Assuming you have a utility function to load your NLP model
nlp = spacy.load("en_core_web_sm")  # Uncomment if you want to use NLP features

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
            doc = nlp(user_text)
            st.subheader("NLP Analysis Results:")
            
            for id, sent in enumerate(doc.sents):
                entity_pair = extract_entity_pairs(sent)
                st.write(f'Triple {id+1}: ({entity_pair[0]}, {extract_relation(sent)}, {entity_pair[1]})')
        else:
            st.warning("Please enter some text to analyze.")

    st.write("---")
    st.info("You can replace this with more sophisticated NLP models or data processing tasks.")

if __name__ in ("__main__", "__page__"):
    main()