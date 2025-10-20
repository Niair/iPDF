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

# ============== GLOBAL STYLES ==============
def inject_global_styles():
    """Load and inject custom CSS for the app."""
    try:
        styles_path = Path(__file__).parent / "styles" / "custom.css"
        if styles_path.exists():
            css = styles_path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        else:
            logger.warning(f"Custom CSS not found at: {styles_path}")
    except Exception as e:
        logger.warning(f"Failed to inject CSS: {str(e)}")


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
                    # Set the first successfully processed file as current if none selected
                    if not st.session_state.current_pdf:
                        st.session_state.current_pdf = uploaded_file.name
                    
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
                                    st.markdown(
                                        f"<span class='source-chip'><span class='dot'></span>"
                                        f"{src['filename']} — p.{src['page']} · {int(src['score']*100)}%</span>",
                                        unsafe_allow_html=True
                                    )
    
    st.divider()
    
    # Quick actions
    st.markdown("#### 🎯 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Summarize", use_container_width=True):
            enhanced_query = """Create a comprehensive summary of the document including:
    1. Main topics and themes discussed
    2. Key findings, arguments, or claims
    3. Important data, examples, or evidence presented
    4. Main conclusions or recommendations

    Organize your summary with clear headers and bullet points. Cite page numbers."""
            handle_chat(enhanced_query)

    with col2:
        if st.button("🎯 Key Points", use_container_width=True):
            enhanced_query = """Extract and list the most important key points from the document.

    For each key point:
    • State the point clearly
    • Provide brief explanation or context
    • Include the page number where it's found

    Format as a numbered or bulleted list."""
            handle_chat(enhanced_query)

    with col3:
        if st.button("📊 Topics", use_container_width=True):
            enhanced_query = """Identify and describe the main topics covered in this document.

    For each topic provide:
    • Topic name/title
    • Brief description (2-3 sentences)
    • Key points or subtopics
    • Relevant page numbers

    Use clear headers for each topic."""
            handle_chat(enhanced_query)

    with col4:
        if st.button("🔍 Details", use_container_width=True):
            enhanced_query = """Provide detailed information from the document covering:

    • Methodologies or approaches used
    • Specific data, statistics, or measurements
    • Technical details or specifications 
    • Examples, case studies, or applications
    • Formulas, equations, or models (if any)

    Organize by topic with clear headers. Include page references."""
            handle_chat(enhanced_query)

    
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
            # Scope retrieval to the currently selected PDF to avoid cross-document mixing
            current_filename = st.session_state.get('current_pdf')
            response = st.session_state.chat_service.chat(
                query=query,
                filename=current_filename,
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
    # Inject CSS once at app start
    inject_global_styles()
    initialize_session_state()
    
    if not st.session_state.services_ready:
        st.error("❌ Services not ready")
        return
    
    st.title("📄 iPDF - Chat with Your PDFs")
    st.markdown(
        """
<div style="padding: 10px 14px; border: 1px solid var(--chip-border); border-radius: 14px; background: linear-gradient(180deg,#0f1628,#0c1322); box-shadow: var(--shadow);">
  <div style="display:flex; align-items:center; gap:12px;">
    <div style="font-size:22px; font-weight:600;">Chat with Your PDFs</div>
    <div style="padding:4px 10px; border:1px solid var(--chip-border); border-radius:999px; background:var(--chip); color:var(--text); font-size:12px;">100% Free</div>
    <div style="padding:4px 10px; border:1px solid var(--chip-border); border-radius:999px; background:var(--chip); color:var(--text); font-size:12px;">Groq + Qdrant</div>
  </div>
  <div style="color: var(--muted); margin-top:4px;">
    Upload PDFs, process them, and ask questions with source-cited answers.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    
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
