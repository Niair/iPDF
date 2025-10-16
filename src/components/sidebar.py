# src/components/sidebar.py
import streamlit as st
import hashlib
from src.services.document_manager import process_documents
from src.config.logger import logger

def render_sidebar():
    st.sidebar.header("📁 Upload PDFs")
    pdf_docs = st.sidebar.file_uploader("Upload files", accept_multiple_files=True, type=["pdf"],
                                        help="For best performance, upload text-based PDFs under 50 pages.")
    st.sidebar.header("⚙️ Processing Options")
    llm_choice = st.sidebar.radio("Language Model:", ["Groq (fast)", "Ollama (local)"], index=0, horizontal=True)
    use_ollama = llm_choice == "Ollama (local)"
    ocr_option = st.sidebar.checkbox("Enable OCR fallback", True)
    st.sidebar.divider()

    if st.sidebar.button("🚀 Process Documents", type="primary") and pdf_docs:
        filenames = [pdf.name for pdf in pdf_docs]
        cache_key = hashlib.sha256(str(filenames).encode()).hexdigest()
        if cache_key != st.session_state.get("processed_key", ""):
            with st.spinner("Processing documents..."):
                try:
                    process_documents(pdf_docs, use_ollama=use_ollama, enable_ocr=ocr_option)
                except Exception as e:
                    logger.exception("Processing documents failed")
                    st.error(f"Processing failed: {e}")
        else:
            st.info("✅ Using cached results")

    if "raw_texts" in st.session_state and st.sidebar.button("📄 Generate Summaries"):
        from src.services.summarizer_service import generate_summaries  # local import to avoid cycles
        with st.spinner("Creating comprehensive summaries..."):
            try:
                summary = generate_summaries(st.session_state.raw_texts, use_ollama=st.session_state.get("use_ollama", False))
                st.session_state.pdf_summary = summary
                st.success("✅ Summaries created")
            except Exception as e:
                logger.exception("Summary generation failed")
                st.error(f"Summary generation failed: {e}")
