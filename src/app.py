# src/app.py
import streamlit as st
from src.config.settings import init_environment, settings
from src.components.sidebar import render_sidebar
from src.pages.chat_page import render_chat_page
from src.pages.summary_page import render_summary_page
from src.config.logger import logger

st.set_page_config(page_title="⚡ iPDF - Chat with PDFs", layout="wide")
init_environment()

st.title("⚡ Chat with iPDF")

try:
    render_sidebar()
    tab1, tab2 = st.tabs(["💬 Chat", "📋 Summaries"])
    with tab1:
        render_chat_page()
    with tab2:
        render_summary_page()
except Exception as e:
    logger.exception("Unhandled exception in main app")
    st.error("An unexpected error occurred. Check logs for details.")
