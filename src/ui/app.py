"""
Main Streamlit Application
Entry point for iPDF
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.config_loader import get_config
from services.pdf_service import PDFService
from services.chat_service import ChatService
from services.model_manager import ModelManager
from ui.components.sidebar import render_sidebar
from ui.components.pdf_viewer import render_pdf_viewer
from ui.components.chat_interface import render_chat_interface

logger = get_logger(__name__)

# Page Configuration
st.set_page_config(
    page_title="iPDF - Chat with PDFs",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Sidebar */
    .css-1d391kg {
        padding: 1rem 1rem;
    }
    
    /* Chat messages */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* PDF viewer container */
    .pdf-container {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #f8f9fa;
    }
    
    /* Copy button */
    .copy-button {
        float: right;
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'pdf_service' not in st.session_state:
        st.session_state.pdf_service = PDFService()
    
    if 'chat_service' not in st.session_state:
        st.session_state.chat_service = ChatService()
    
    if 'model_manager' not in st.session_state:
        st.session_state.model_manager = ModelManager()
    
    if 'uploaded_pdfs' not in st.session_state:
        st.session_state.uploaded_pdfs = {}
    
    if 'current_pdf' not in st.session_state:
        st.session_state.current_pdf = None
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False


def main():
    """Main application"""
    # Initialize
    initialize_session_state()
    
    # Title
    st.title("📄 iPDF - Chat with Your PDFs")
    st.markdown("**100% FREE** • Powered by Ollama + Qdrant")
    
    # Sidebar
    render_sidebar()
    
    # Main content area - Split view
    if st.session_state.processing_complete and st.session_state.uploaded_pdfs:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📄 PDF Viewer")
            render_pdf_viewer()
        
        with col2:
            st.subheader("💬 Chat Interface")
            render_chat_interface()
    else:
        # Welcome screen
        st.info("👋 Welcome! Upload PDFs in the sidebar to get started.")
        
        st.markdown("""
        ### How to use:
        1. **Upload PDFs** - Click "Browse files" in the sidebar
        2. **Process** - Click "🚀 Process Documents"
        3. **Chat** - Ask questions about your documents
        4. **View** - Click PDF names to view them on the left
        
        ### Features:
        - ✅ Chat with multiple PDFs simultaneously
        - ✅ Semantic search across all documents
        - ✅ Extract and display tables
        - ✅ Copy responses easily
        - ✅ 100% FREE (no API costs!)
        """)


if __name__ == "__main__":
    main()
