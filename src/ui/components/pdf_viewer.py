"""
PDF Viewer Component
Display PDF on left side of screen
"""
import streamlit as st
from pathlib import Path

from utils.logger import get_logger
from utils.pdf_renderer import PDFRenderer

logger = get_logger(__name__)


def render_pdf_viewer():
    """Render PDF viewer with navigation"""
    uploaded_pdfs = st.session_state.uploaded_pdfs
    
    if not uploaded_pdfs:
        st.info("📄 No PDFs loaded yet")
        return
    
    # PDF selection buttons
    st.markdown("**Select PDF to view:**")
    
    if len(uploaded_pdfs) == 1:
        # Single PDF - show directly
        filename = list(uploaded_pdfs.keys())
        st.session_state.current_pdf = filename
    else:
        # Multiple PDFs - show buttons
        cols = st.columns(min(len(uploaded_pdfs), 3))
        for idx, filename in enumerate(uploaded_pdfs.keys()):
            col_idx = idx % 3
            with cols[col_idx]:
                if st.button(
                    f"📄 {filename[:20]}...",
                    key=f"pdf_btn_{idx}",
                    use_container_width=True
                ):
                    st.session_state.current_pdf = filename
    
    # Display current PDF
    if st.session_state.current_pdf:
        display_pdf(st.session_state.current_pdf)
    else:
        st.info("👆 Click a PDF name to view")


def display_pdf(filename: str):
    """Display PDF pages as images"""
    try:
        file_path = st.session_state.uploaded_pdfs[filename]
        
        st.markdown(f"**Viewing:** `{filename}`")
        
        # Back button if multiple PDFs
        if len(st.session_state.uploaded_pdfs) > 1:
            if st.button("⬅️ Back to PDF list"):
                st.session_state.current_pdf = None
                st.rerun()
        
        st.divider()
        
        # Render PDF
        renderer = PDFRenderer(dpi=150)
        page_count = renderer.get_page_count(file_path)
        
        if page_count == 0:
            st.error("❌ Unable to load PDF")
            return
        
        # Page selector
        page_number = st.slider(
            "Page",
            min_value=1,
            max_value=page_count,
            value=1,
            key="pdf_page_slider"
        )
        
        st.text(f"Page {page_number} of {page_count}")
        
        # Render page
        with st.spinner(f"Loading page {page_number}..."):
            page_image = renderer.render_page(file_path, page_number - 1)
            
            if page_image:
                st.image(page_image, use_column_width=True)
            else:
                st.error("❌ Failed to render page")
    
    except Exception as e:
        st.error(f"❌ Error displaying PDF: {str(e)}")
        logger.error(f"PDF display error: {str(e)}")
