# src/pages/summary_page.py
import streamlit as st
from src.components.summary_display import display_summary

def render_summary_page():
    if "pdf_summary" in st.session_state:
        st.subheader("Document Summaries")
        display_summary(st.session_state.pdf_summary)
    else:
        st.info("👆 Generate summaries using the sidebar button")
