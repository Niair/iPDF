"""
Model Selector Component
Dropdown for selecting LLM models
"""
import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)


def render_model_selector():
    """Render model selection dropdown"""
    if 'model_manager' not in st.session_state:
        return None
    
    model_manager = st.session_state.model_manager
    available_models = model_manager.get_available_models()
    
    selected_model = st.selectbox(
        "Select Model",
        options=available_models,
        index=0,
        help="Choose the LLM model for responses"
    )
    
    # Update chat service when model changes
    if selected_model != st.session_state.get('current_model'):
        st.session_state.current_model = selected_model
        model_id = model_manager.get_model_id(selected_model)
        
        # Update LLM handler
        from core.llm_handler import LLMHandler
        st.session_state.chat_service.llm = LLMHandler(model=model_id)
        
        logger.info(f"Model changed to: {selected_model}")
    
    return selected_model
