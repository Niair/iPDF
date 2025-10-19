"""
iPDF - WITH DEBUGGING
"""
import streamlit as st
import sys
import os
from pathlib import Path
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="iPDF - Chat with PDFs",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.logger import get_logger
from services.pdf_service import PDFService
from services.chat_service import ChatService
from core.llm_handler import LLMHandler
from core.vectorstore import VectorStoreManager
import fitz

logger = get_logger(__name__)


# ==================== SESSION STATE ====================
def initialize_session_state():
    """Initialize session state"""
    defaults = {
        'initialized': False,
        'pdf_service': None,
        'chat_service': None,
        'uploaded_files': {},
        'processed_files': [],
        'current_pdf': None,
        'chat_history': [],
        'services_ready': False,
        'llm_provider': 'groq',
        'processing_log': []  # NEW: Store processing logs
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    if not st.session_state.initialized:
        try:
            st.session_state.pdf_service = PDFService()
            st.session_state.chat_service = ChatService(
                llm_provider=st.session_state.llm_provider
            )
            st.session_state.initialized = True
            st.session_state.services_ready = True
            logger.info("Services initialized")
        except Exception as e:
            logger.error(f"Init failed: {str(e)}")
            st.session_state.services_ready = False


# ==================== PDF FUNCTIONS ====================
def render_pdf_page(pdf_path: str, page_num: int = 0):
    """Render PDF page"""
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        doc.close()
        return img_bytes
    except Exception as e:
        logger.error(f"PDF render error: {str(e)}")
        return None


def get_pdf_page_count(pdf_path: str) -> int:
    """Get page count"""
    try:
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except:
        return 0


# ==================== SIDEBAR ====================
def render_sidebar():
    """Render sidebar with model switcher"""
    with st.sidebar:
        st.header("📁 Upload PDFs")
        
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")
        
        if st.button("🚀 Process Documents", type="primary", disabled=not uploaded_files):
            if uploaded_files:
                process_pdfs(uploaded_files)
        
        st.divider()
        
        # MODEL SELECTOR - NEW!
        st.subheader("🤖 AI Model")
        
        selected_model = st.selectbox(
            "Choose AI Model for Answers",
            options=["google", "groq"],
            format_func=lambda x: "🔵 Google Gemini (Recommended)" if x == "google" else "🟢 Groq Llama",
            key="model_selector"
        )
        
        # Update chat service if model changed
        if selected_model != st.session_state.get('current_model', 'google'):
            st.session_state.current_model = selected_model
            try:
                st.session_state.chat_service = ChatService(llm_provider=selected_model)
                st.success(f"✅ Now using {selected_model.upper()}")
            except Exception as e:
                st.error(f"❌ Failed to switch: {str(e)}")
        
        # Show current model
        st.caption(f"Currently using: **{st.session_state.get('current_model', 'google').upper()}**")
        
        st.divider()
        
        # Settings
        st.subheader("⚙️ Settings")
        provider = st.selectbox(
            "AI Provider",
            options=["groq", "gemini"],
            index=0
        )
        
        if provider != st.session_state.llm_provider:
            st.session_state.llm_provider = provider
            try:
                st.session_state.chat_service = ChatService(llm_provider=provider)
                st.success(f"✅ Switched to {provider.upper()}")
            except Exception as e:
                st.error(f"Failed: {str(e)}")
        
        st.divider()
        
        # Document list
        if st.session_state.processed_files:
            st.subheader("📚 Documents")
            st.caption(f"{len(st.session_state.processed_files)} loaded")
            
            for filename in st.session_state.processed_files:
                short_name = filename[:25] + "..." if len(filename) > 25 else filename
                if st.button(f"📄 {short_name}", key=f"doc_{filename}", use_container_width=True):
                    st.session_state.current_pdf = filename
                    st.rerun()
        else:
            st.info("No documents loaded yet")
        
        st.divider()
        
        if st.button("🗑️ Clear All", use_container_width=True):
            clear_all()
        
        st.divider()
        
        # Status
        st.subheader("📊 Status")
        
        try:
            llm = LLMHandler(provider="groq")
            if llm.test_connection():
                st.success("✅ Groq API")
            else:
                st.error("❌ Groq API")
        except:
            st.error("❌ Groq API")
        
        try:
            vs = VectorStoreManager()
            if vs.test_connection():
                st.success("✅ Qdrant DB")
            else:
                st.error("❌ Qdrant DB")
        except:
            st.error("❌ Qdrant DB")
        
        st.info(f"📄 {len(st.session_state.processed_files)} documents")


# ==================== PDF PROCESSING WITH DETAILED FEEDBACK ====================
def process_pdfs(uploaded_files):
    """Process PDFs with detailed feedback"""
    if not uploaded_files:
        st.warning("No files selected")
        return
    
    try:
        # Create expandable section for logs
        log_expander = st.expander("📋 Processing Logs", expanded=True)
        
        progress_bar = st.progress(0)
        status_container = st.container()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            with status_container:
                st.info(f"⚙️ Processing: **{uploaded_file.name}**")
            
            with log_expander:
                st.text(f"📄 File: {uploaded_file.name}")
                st.text(f"📦 Size: {uploaded_file.size / 1024:.1f} KB")
            
            try:
                # Upload
                file_bytes = uploaded_file.read()
                file_path = st.session_state.pdf_service.upload_pdf(
                    file_bytes,
                    uploaded_file.name
                )
                
                with log_expander:
                    st.text(f"✅ Uploaded to: {file_path}")
                
                # Store path
                st.session_state.uploaded_files[uploaded_file.name] = file_path
                
                # Process and index
                with log_expander:
                    st.text("🔄 Extracting text...")
                
                success = st.session_state.pdf_service.process_and_index_pdf(
                    file_path,
                    uploaded_file.name
                )
                
                if success:
                    if uploaded_file.name not in st.session_state.processed_files:
                        st.session_state.processed_files.append(uploaded_file.name)
                    
                    with log_expander:
                        st.success(f"✅ Successfully processed: {uploaded_file.name}")
                else:
                    with log_expander:
                        st.error(f"❌ Failed to process: {uploaded_file.name}")
            
            except Exception as e:
                with log_expander:
                    st.error(f"❌ Error: {str(e)}")
                logger.error(f"Processing error: {str(e)}")
            
            # Update progress
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        # Final status
        progress_bar.empty()
        
        if st.session_state.processed_files:
            st.success(f"✅ Processed {len(st.session_state.processed_files)} document(s)!")
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ No documents were processed successfully")
    
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        logger.error(f"Processing error: {str(e)}")


def clear_all():
    """Clear all"""
    st.session_state.uploaded_files = {}
    st.session_state.processed_files = []
    st.session_state.current_pdf = None
    st.session_state.chat_history = []
    st.success("✅ Cleared!")
    time.sleep(0.5)
    st.rerun()


# ==================== PDF VIEWER ====================
def render_pdf_viewer():
    """Render PDF viewer"""
    if not st.session_state.current_pdf:
        st.info("👈 Select a PDF from sidebar")
        return
    
    filename = st.session_state.current_pdf
    
    if filename not in st.session_state.uploaded_files:
        st.error("❌ PDF not found")
        return
    
    file_path = st.session_state.uploaded_files[filename]
    
    st.markdown(f"### 📄 {filename}")
    
    page_count = get_pdf_page_count(file_path)
    
    if page_count == 0:
        st.error("❌ Could not load PDF")
        return
    
    if page_count == 1:
        st.caption("Page 1 of 1")
        page_num = 1
    else:
        page_num = st.slider("Page", 1, page_count, 1, key=f"slider_{filename}")
        st.caption(f"Page {page_num} of {page_count}")
    
    with st.spinner("Loading..."):
        img_bytes = render_pdf_page(file_path, page_num - 1)
        
        if img_bytes:
            st.image(img_bytes, use_column_width=True)
        else:
            st.error("❌ Failed to render")


# ==================== CHAT INTERFACE ====================
def render_chat_interface():
    """Render chat with multimodal support"""
    st.markdown("### 💬 Chat")
    
    if not st.session_state.processed_files:
        st.info("👈 Upload and process PDFs")
        return
    
    st.caption(f"**Documents:** {', '.join(st.session_state.processed_files)}")
    
    # Show multimodal stats
    with st.expander("📊 Content Types"):
        st.caption("Your documents contain:")
        st.text("📝 Text content")
        st.text("🖼️ Images (with AI descriptions)")
        st.text("📊 Tables (with AI summaries)")
    
    # Chat history
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.chat_history:
            st.info("""💬 **Ask me anything!**

**Examples:**
• "Summarize this document"
• "What are the key points?"
• "Who is mentioned?"
            """)
        else:
            for idx, msg in enumerate(st.session_state.chat_history):
                if msg['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(msg['content'])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(msg['content'])
                        
                        if 'processing_time' in msg:
                            st.caption(f"⏱️ {msg['processing_time']:.2f}s")
                        
                        if st.button("📋 Copy", key=f"copy_{idx}"):
                            st.code(msg['content'])
                        
                        if 'sources' in msg and msg['sources']:
                            with st.expander(f"📚 {len(msg['sources'])} Sources"):
                                for src in msg['sources']:
                                    st.text(f"📄 {src['filename']} (Page {src['page']}) - {src['score']:.0%}")
    
    st.divider()
    
    # Quick actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Summarize", use_container_width=True):
            handle_chat("Provide a comprehensive summary")
    
    with col2:
        if st.button("🎯 Key Points", use_container_width=True):
            handle_chat("What are the key points?")
    
    with col3:
        if st.button("📊 Topics", use_container_width=True):
            handle_chat("What are the main topics?")
    
    with col4:
        if st.button("🔍 Details", use_container_width=True):
            handle_chat("Give detailed information")
    
    # Chat input
    user_query = st.chat_input("Ask about your documents...")
    
    if user_query:
        handle_chat(user_query)


def handle_chat(query: str):
    """Handle chat"""
    try:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': query
        })
        
        with st.spinner("Thinking..."):
            response = st.session_state.chat_service.chat(
                query=query,
                filename=None,
                use_rag=True
            )
        
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response.answer,
            'sources': response.sources,
            'processing_time': response.processing_time
        })
        
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


# ==================== MAIN ====================
def main():
    """Main"""
    initialize_session_state()
    
    if not st.session_state.services_ready:
        st.error("❌ Services not ready")
        return
    
    st.title("📄 iPDF - Chat with Your PDFs")
    st.markdown("**100% FREE** • Powered by Groq & Qdrant")
    
    render_sidebar()
    
    if st.session_state.processed_files:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            render_pdf_viewer()
        
        with col2:
            render_chat_interface()
    else:
        st.info("👋 Welcome! Upload PDFs in the sidebar")
        
        st.markdown("""
### 🚀 Quick Start:
1. Upload PDFs
2. Click "Process Documents"
3. Chat with your PDFs!
        """)


if __name__ == "__main__":
    main()
