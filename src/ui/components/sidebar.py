"""
Sidebar Component
Handles file uploads and settings
"""
import streamlit as st
import os
from pathlib import Path

from utils.logger import get_logger
from utils.helpers import format_file_size

logger = get_logger(__name__)


def render_sidebar():
    """Render sidebar with upload and settings"""
    with st.sidebar:
        st.header("📁 Upload PDFs")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more PDF files"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")
            
            # Show file info
            for file in uploaded_files:
                size = format_file_size(file.size)
                st.text(f"📄 {file.name} ({size})")
        
        st.divider()
        
        # Process button
        if st.button("🚀 Process Documents", type="primary", use_container_width=True):
            if not uploaded_files:
                st.error("⚠️ Please upload at least one PDF file")
            else:
                process_documents(uploaded_files)
        
        st.divider()
        
        # Settings
        st.header("⚙️ Settings")
        
        # Model selection
        available_models = st.session_state.model_manager.get_available_models()
        selected_model = st.selectbox(
            "LLM Model",
            options=available_models,
            index=0,
            help="Select the language model to use"
        )
        st.session_state.selected_model = selected_model
        
        # OCR toggle
        enable_ocr = st.checkbox(
            "Enable OCR",
            value=True,
            help="Use OCR for scanned PDFs"
        )
        st.session_state.enable_ocr = enable_ocr
        
        st.divider()
        
        # Clear button
        if st.button("🗑️ Clear All", use_container_width=True):
            clear_all_data()
        
        # System status
        st.header("📊 System Status")
        render_system_status()


def process_documents(uploaded_files):
    """Process uploaded PDF files"""
    try:
        with st.spinner("Processing documents..."):
            progress_bar = st.progress(0)
            
            pdf_service = st.session_state.pdf_service
            
            for idx, uploaded_file in enumerate(uploaded_files):
                # Upload file
                file_bytes = uploaded_file.read()
                file_path = pdf_service.upload_pdf(file_bytes, uploaded_file.name)
                
                # Process and index
                success = pdf_service.process_and_index_pdf(file_path, uploaded_file.name)
                
                if success:
                    st.session_state.uploaded_pdfs[uploaded_file.name] = file_path
                
                # Update progress
                progress = (idx + 1) / len(uploaded_files)
                progress_bar.progress(progress)
            
            st.session_state.processing_complete = True
            st.success(f"✅ Successfully processed {len(uploaded_files)} document(s)!")
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error processing documents: {str(e)}")
        logger.error(f"Document processing error: {str(e)}")


def clear_all_data():
    """Clear all uploaded data"""
    st.session_state.uploaded_pdfs = {}
    st.session_state.current_pdf = None
    st.session_state.chat_history = []
    st.session_state.processing_complete = False
    st.success("✅ All data cleared!")
    st.rerun()


def render_system_status():
    """Render system status indicators"""
    # Check Ollama
    try:
        from core.llm_handler import LLMHandler
        llm = LLMHandler()
        ollama_status = llm.test_connection()
    except:
        ollama_status = False
    
    # Check Qdrant
    try:
        from core.vectorstore import VectorStoreManager
        vs = VectorStoreManager()
        qdrant_status = vs.test_connection()
    except:
        qdrant_status = False
    
    # Display status
    ollama_icon = "✅" if ollama_status else "❌"
    qdrant_icon = "✅" if qdrant_status else "❌"
    
    st.text(f"{ollama_icon} Ollama LLM")
    st.text(f"{qdrant_icon} Qdrant DB")
    
    # Document count
    doc_count = len(st.session_state.uploaded_pdfs)
    st.text(f"📄 {doc_count} document(s)")
