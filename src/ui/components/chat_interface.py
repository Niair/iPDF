"""
Chat Interface Component
Handle chat interactions on right side
"""
import streamlit as st
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


def render_chat_interface():
    """Render chat interface"""
    # Chat history display
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.chat_history:
            st.info("💬 Ask a question about your documents!")
        else:
            # Display chat messages
            for idx, message in enumerate(st.session_state.chat_history):
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(message['content'])
                        
                        # Copy button
                        if st.button("📋 Copy", key=f"copy_{idx}"):
                            st.code(message['content'], language=None)
                        
                        # Show sources if available
                        if 'sources' in message and message['sources']:
                            with st.expander("📚 Sources"):
                                for source in message['sources']:
                                    st.text(
                                        f"📄 {source['filename']} (Page {source['page']}) "
                                        f"- Score: {source['score']:.3f}"
                                    )
    
    st.divider()
    
    # Model selector and input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_query = st.chat_input("Ask a question about your documents...")
    
    with col2:
        # Filter by current PDF toggle
        filter_current = st.checkbox(
            "Current PDF only",
            value=False,
            help="Search only in the currently viewed PDF"
        )
    
    # Process query
    if user_query:
        process_chat_query(user_query, filter_current)


def process_chat_query(query: str, filter_current_pdf: bool):
    """Process user chat query"""
    try:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': query,
            'timestamp': datetime.now()
        })
        
        # Get filename filter
        filename = None
        if filter_current_pdf and st.session_state.current_pdf:
            filename = st.session_state.current_pdf
        
        # Generate response
        with st.spinner("🤔 Thinking..."):
            chat_service = st.session_state.chat_service
            response = chat_service.chat(
                query=query,
                filename=filename,
                use_rag=True
            )
        
        # Add assistant message to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response.answer,
            'sources': response.sources,
            'timestamp': datetime.now(),
            'processing_time': response.processing_time
        })
        
        # Rerun to update chat
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error processing query: {str(e)}")
        logger.error(f"Chat error: {str(e)}")
