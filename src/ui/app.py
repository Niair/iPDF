"""
iPDF - Main Streamlit Application
Simplified, bug-free version
"""
import streamlit as st
import sys
import os
from pathlib import Path
import time
from io import BytesIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page config MUST be first
st.set_page_config(
    page_title="iPDF - Chat with PDFs",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import after page config
from utils.logger import get_logger
from services.pdf_service import PDFService
from services.chat_service import ChatService
from core.llm_handler import LLMHandler
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager
import fitz  # PyMuPDF

logger = get_logger(__name__)

# Custom CSS
st.markdown("""
<style>
    .main {padding: 1rem;}
    .stButton button {width: 100%;}
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)


# ==================== INITIALIZE SESSION STATE ====================
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'initialized': False,
        'pdf_service': None,
        'chat_service': None,
        'uploaded_files': {},
        'processed_files': [],
        'current_pdf': None,
        'chat_history': [],
        'services_ready': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialize services once
    if not st.session_state.initialized:
        try:
            st.session_state.pdf_service = PDFService()
            st.session_state.chat_service = ChatService()
            st.session_state.initialized = True
            st.session_state.services_ready = True
        except Exception as e:
            st.error(f"❌ Failed to initialize services: {str(e)}")
            st.session_state.services_ready = False


# ==================== PDF RENDERING ====================
def render_pdf_page(pdf_path: str, page_num: int = 0):
    """Render a single PDF page as image"""
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        
        # Render page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
        img_bytes = pix.tobytes("png")
        
        doc.close()
        return img_bytes
    except Exception as e:
        logger.error(f"Error rendering PDF page: {str(e)}")
        return None


def get_pdf_page_count(pdf_path: str) -> int:
    """Get total pages in PDF"""
    try:
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except:
        return 0


# ==================== SIDEBAR ====================
def render_sidebar():
    """Render sidebar with upload and controls"""
    with st.sidebar:
        st.header("📁 Upload PDFs")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")
        
        # Process button
        if st.button("🚀 Process Documents", type="primary", disabled=not uploaded_files):
            if uploaded_files:
                process_pdfs(uploaded_files)
        
        st.divider()
        
        # Show processed files
        if st.session_state.processed_files:
            st.subheader("📚 Processed Documents")
            for filename in st.session_state.processed_files:
                if st.button(f"📄 {filename}", key=f"view_{filename}"):
                    st.session_state.current_pdf = filename
                    st.rerun()
        
        st.divider()
        
        # Clear button
        if st.button("🗑️ Clear All"):
            clear_all()
        
        # Status
        st.divider()
        st.subheader("📊 Status")
        
        # Check services
        ollama_ok = check_ollama()
        qdrant_ok = check_qdrant()
        
        st.text(f"{'✅' if ollama_ok else '❌'} Ollama")
        st.text(f"{'✅' if qdrant_ok else '❌'} Qdrant")
        st.text(f"📄 {len(st.session_state.processed_files)} docs")


def check_ollama() -> bool:
    """Check if Ollama is running"""
    try:
        from core.llm_handler import LLMHandler
        llm = LLMHandler()
        return llm.test_connection()
    except:
        return False


def check_qdrant() -> bool:
    """Check if Qdrant is connected"""
    try:
        from core.vectorstore import VectorStoreManager
        vs = VectorStoreManager()
        return vs.test_connection()
    except:
        return False


# ==================== PDF PROCESSING ====================
def process_pdfs(uploaded_files):
    """Process uploaded PDF files"""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Save file
            file_bytes = uploaded_file.read()
            file_path = st.session_state.pdf_service.upload_pdf(
                file_bytes, 
                uploaded_file.name
            )
            
            # Store file
            st.session_state.uploaded_files[uploaded_file.name] = file_path
            
            # Process and index
            success = st.session_state.pdf_service.process_and_index_pdf(
                file_path,
                uploaded_file.name
            )
            
            if success:
                if uploaded_file.name not in st.session_state.processed_files:
                    st.session_state.processed_files.append(uploaded_file.name)
            
            # Update progress
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
        
        status_text.empty()
        progress_bar.empty()
        st.success(f"✅ Processed {len(uploaded_files)} document(s)!")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        logger.error(f"Processing error: {str(e)}")


def clear_all():
    """Clear all data"""
    st.session_state.uploaded_files = {}
    st.session_state.processed_files = []
    st.session_state.current_pdf = None
    st.session_state.chat_history = []
    st.success("✅ Cleared!")
    time.sleep(0.5)
    st.rerun()


# ==================== PDF VIEWER ====================
def render_pdf_viewer():
    """Render PDF viewer with navigation"""
    if not st.session_state.current_pdf:
        st.info("👈 Select a PDF from the sidebar to view")
        return
    
    filename = st.session_state.current_pdf
    
    if filename not in st.session_state.uploaded_files:
        st.error("❌ PDF file not found")
        return
    
    file_path = st.session_state.uploaded_files[filename]
    
    # Header
    st.markdown(f"### 📄 {filename}")
    
    # Get page count
    page_count = get_pdf_page_count(file_path)
    
    if page_count == 0:
        st.error("❌ Could not load PDF")
        return
    
    # Initialize page number in session state
    page_key = f"page_num_{filename}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    
    # Navigation controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=(st.session_state[page_key] <= 1)):
            st.session_state[page_key] = max(1, st.session_state[page_key] - 1)
            st.rerun()
    
    with col2:
        st.markdown(f"<div style='text-align: center;'><b>Page {st.session_state[page_key]} of {page_count}</b></div>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next ➡️", disabled=(st.session_state[page_key] >= page_count)):
            st.session_state[page_key] = min(page_count, st.session_state[page_key] + 1)
            st.rerun()
    
    # Page selector (only if more than 1 page)
    if page_count > 1:
        page_num = st.slider(
            "Jump to page",
            min_value=1,
            max_value=page_count,
            value=st.session_state[page_key],
            key=f"page_slider_{filename}"
        )
        if page_num != st.session_state[page_key]:
            st.session_state[page_key] = page_num
            st.rerun()
    
    # Render current page
    with st.spinner("Loading page..."):
        img_bytes = render_pdf_page(file_path, st.session_state[page_key] - 1)
        
        if img_bytes:
            st.image(img_bytes, use_column_width=True)
        else:
            st.error("❌ Failed to render page")


# ==================== CHAT INTERFACE ====================
def render_chat_interface():
    """Render improved chat interface"""
    st.markdown("### 💬 Chat")
    
    if not st.session_state.processed_files:
        st.info("👈 Upload and process PDFs first")
        return
    
    # Show currently loaded documents
    st.caption(f"📚 Loaded documents: {', '.join(st.session_state.processed_files)}")
    
    # Chat container
    chat_container = st.container(height=450)
    
    with chat_container:
        if not st.session_state.chat_history:
            st.info("""💬 **Ask me anything about your documents!**
            
            Examples:
            • "What is this document about?"
            • "Summarize the main points"
            • "Who is Nihal Kumar?"
            • "Tell me about the projects mentioned"
            """)
        else:
            for idx, msg in enumerate(st.session_state.chat_history):
                if msg['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(msg['content'])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(msg['content'])
                        
                        # Show processing time
                        if 'processing_time' in msg:
                            st.caption(f"⏱️ {msg['processing_time']:.2f}s")
                        
                        # Copy button
                        if st.button("📋 Copy", key=f"copy_{idx}"):
                            st.code(msg['content'], language=None)
                        
                        # Show sources with relevance scores
                        if 'sources' in msg and msg['sources']:
                            with st.expander(f"📚 {len(msg['sources'])} Sources"):
                                for src in msg['sources']:
                                    relevance = src['score']
                                    relevance_color = "🟢" if relevance > 0.7 else "🟡" if relevance > 0.5 else "🟠"
                                    st.text(
                                        f"{relevance_color} {src['filename']} (Page {src['page']}) "
                                        f"- Relevance: {relevance:.1%}"
                                    )
    
    st.divider()
    
    # Input area with helpful placeholder
    user_query = st.chat_input(
        "Ask about your documents... (e.g., 'What are the key points?')",
        key="chat_input"
    )
    
    if user_query:
        handle_chat(user_query)


def handle_chat(query: str):
    """Handle chat query with better error handling"""
    try:
        # Add user message
        st.session_state.chat_history.append({
            'role': 'user',
            'content': query
        })
        
        # Show thinking indicator
        with st.spinner("🤔 Analyzing documents..."):
            response = st.session_state.chat_service.chat(
                query=query,
                filename=None,
                use_rag=True
            )
        
        # Add assistant message
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response.answer,
            'sources': response.sources,
            'processing_time': response.processing_time
        })
        
        st.rerun()
        
    except Exception as e:
        error_msg = f"❌ **Error:** {str(e)}\n\nPlease try rephrasing your question or check if the documents are properly processed."
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': error_msg,
            'sources': []
        })
        logger.error(f"Chat error: {str(e)}")
        st.rerun()

# ==================== MAIN APP ====================
def main():
    """Main application"""
    # Initialize
    initialize_session_state()
    
    if not st.session_state.services_ready:
        st.error("❌ Services not initialized. Check your configuration.")
        return
    
    # Title
    st.title("📄 iPDF - Chat with Your PDFs")
    st.markdown("**100% FREE** • Powered by Ollama + Qdrant")
    
    # Sidebar
    render_sidebar()
    
    # Main content
    if st.session_state.processed_files:
        # Two columns: PDF viewer + Chat
        col1, col2 = st.columns([1, 1])
        
        with col1:
            render_pdf_viewer()
        
        with col2:
            render_chat_interface()
    else:
        # Welcome screen
        st.info("👋 Welcome! Upload PDFs in the sidebar to get started.")
        
        st.markdown("""
        ### 🚀 Quick Start:
        1. **Upload PDFs** - Click "Browse files" in sidebar
        2. **Process** - Click "🚀 Process Documents"
        3. **Chat** - Ask questions about your documents
        4. **View** - Click PDF names to view them
        
        ### ✨ Features:
        - ✅ Chat with multiple PDFs
        - ✅ View PDFs page by page
        - ✅ Semantic search
        - ✅ Source citations
        - ✅ 100% FREE!
        """)
        
        # Service status
        st.markdown("### 📊 Service Status")
        col1, col2 = st.columns(2)
        
        with col1:
            ollama_ok = check_ollama()
            if ollama_ok:
                st.success("✅ Ollama Connected")
            else:
                st.error("❌ Ollama Not Running")
                st.code("ollama serve")
        
        with col2:
            qdrant_ok = check_qdrant()
            if qdrant_ok:
                st.success("✅ Qdrant Connected")
            else:
                st.error("❌ Qdrant Not Connected")
                st.info("Check .env file")


if __name__ == "__main__":
    main()
