import streamlit as st
import neo4j_graphrag
from pathlib import Path
from neo4j_graphrag.experimental.components.pdf_loader import PdfLoader

def main():
    st.file_uploader(
        "Upload a PDF file",
        type=["pdf"],
        on_change=load_pdf,
        key="pdf_uploader"
    )
    
    if st.session_state['pdf_uploader'] is not None:
        pdf_path = Path(st.session_state['pdf_uploader'].name)
        loader = PdfLoader()
        text=loader.run(filepath=pdf_path)
        st.write(text)  

def load_pdf():
    uploaded_file = st.session_state.get("pdf_uploader")
    if uploaded_file is not None:
        pdf_path = Path(uploaded_file.name)
        
if __name__ in ("__main__", "__page__"):
    main()