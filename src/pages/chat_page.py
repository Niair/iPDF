# src/pages/chat_page.py
import streamlit as st
import time
from src.components.message_renderer import render_message_with_copy
from src.config.logger import logger

def render_chat_page():
    if "conversation" in st.session_state:
        for idx, (user_query, bot_response) in enumerate(st.session_state.chat_history):
            render_message_with_copy(user_query, "user", idx * 2)
            render_message_with_copy(bot_response, "assistant", idx * 2 + 1)

        query = st.chat_input("Ask about your documents...", key="chat_input")
        if query:
            with st.spinner("Generating response..."):
                start_time = time.time()
                try:
                    result = st.session_state.conversation({"question": query})
                    response_time = time.time() - start_time
                    formatted_response = result["answer"].replace("[FORMULA]", "**").replace("[/FORMULA]", "**")
                    st.session_state.chat_history.append((query, formatted_response))
                    st.caption(f"Response generated in {response_time:.1f}s")
                    st.rerun()
                except Exception as e:
                    logger.exception("Error generating chat response")
                    st.error(f"Failed to generate response: {e}")
    else:
        st.info("👆 Upload and process documents to start chatting")
