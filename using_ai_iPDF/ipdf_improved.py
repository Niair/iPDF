import os
import re
import concurrent.futures
import hashlib
import time
import streamlit as st
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
import pytesseract
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama
from streamlit.components.v1 import html
import base64
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="iPDF Pro - Intelligent PDF Assistant",
    page_icon="ðŸ“„",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stChat {
        height: 500px;
        overflow-y: auto;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .assistant-message {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .confidence-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-left: 10px;
    }
    .confidence-high { background-color: #4caf50; color: white; }
    .confidence-medium { background-color: #ff9800; color: white; }
    .confidence-low { background-color: #f44336; color: white; }
    .source-doc { font-size: 12px; color: #666; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

@dataclass
class ProcessingResult:
    """Data class for processing results"""
    success: bool
    text: str
    metadata: Dict
    error: Optional[str] = None
    confidence: float = 0.0

class PDFProcessor:
    """Enhanced PDF processing with OCR fallback and quality validation"""
    
    def __init__(self):
        self.tesseract_cmd = os.getenv("TESSERACT_PATH", "/usr/bin/tesseract")
        if os.path.exists(self.tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        
    def extract_text_with_pdfplumber(self, pdf_bytes: bytes) -> Tuple[str, Dict]:
        """Extract text using pdfplumber with enhanced error handling"""
        text = ""
        metadata = {}
        
        try:
            with pdfplumber.open(pdf_bytes) as pdf_reader:
                # Extract metadata
                metadata = {
                    'pages': len(pdf_reader.pages),
                    'title': getattr(pdf_reader.metadata, 'title', 'Unknown'),
                    'author': getattr(pdf_reader.metadata, 'author', 'Unknown'),
                    'subject': getattr(pdf_reader.metadata, 'subject', ''),
                    'creator': getattr(pdf_reader.metadata, 'creator', ''),
                    'producer': getattr(pdf_reader.metadata, 'producer', ''),
                    'creation_date': getattr(pdf_reader.metadata, 'creation_date', None),
                    'modified_date': getattr(pdf_reader.metadata, 'mod_date', None)
                }
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text() or ""
                    
                    # Extract tables
                    tables = page.extract_tables()
                    table_text = ""
                    for table in tables:
                        if table:
                            table_text += "\n[TABLE_START]\n"
                            for row in table:
                                table_text += "\t".join([cell or "" for cell in row]) + "\n"
                            table_text += "[TABLE_END]\n"
                    
                    # Combine page text and tables
                    if page_text.strip() or table_text.strip():
                        text += f"\n[PAGE_{page_num}]\n"
                        text += page_text + "\n"
                        text += table_text
                
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {str(e)}")
            return "", {}
        
        return text, metadata
    
    def extract_text_with_ocr(self, pdf_bytes: bytes) -> str:
        """Extract text using OCR as fallback"""
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
            ocr_text = ""
            
            with st.spinner("Performing OCR on scanned document..."):
                for i, image in enumerate(images):
                    try:
                        page_text = pytesseract.image_to_string(image)
                        if page_text.strip():
                            ocr_text += f"\n[PAGE_{i+1}]\n"
                            ocr_text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"OCR failed for page {i+1}: {str(e)}")
                        continue
            
            return ocr_text
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return ""
    
    def calculate_confidence(self, text: str, method: str) -> float:
        """Calculate confidence score based on text quality"""
        if not text.strip():
            return 0.0
        
        # Basic quality metrics
        word_count = len(text.split())
        char_count = len(text)
        
        # Check for meaningful content
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1)
        
        # Calculate confidence based on multiple factors
        confidence = 0.0
        
        # Text length factor (0-40%)
        if word_count > 100:
            confidence += min(40, word_count / 50)
        
        # Sentence structure factor (0-30%)
        if 5 <= avg_sentence_length <= 25:
            confidence += 30
        
        # Content quality factor (0-30%)
        if re.search(r'[A-Z][a-z]+.*[.!?]', text):
            confidence += 20
        if re.search(r'\b(the|and|or|but|with|from|this|that)\b', text, re.IGNORECASE):
            confidence += 10
        
        # OCR-specific adjustments
        if method == "ocr":
            # Check for common OCR errors
            if re.search(r'[0-9lI]{5,}', text):  # Too many numbers or similar characters
                confidence *= 0.8
            if re.search(r'[@#$%^&*]{3,}', text):  # Too many special characters
                confidence *= 0.7
        
        return min(confidence, 100.0)
    
    def process_pdf(self, pdf_bytes: bytes, filename: str) -> ProcessingResult:
        """Process a single PDF with multiple extraction methods"""
        try:
            # Try pdfplumber first
            text, metadata = self.extract_text_with_pdfplumber(pdf_bytes)
            confidence = self.calculate_confidence(text, "pdfplumber")
            
            # Fallback to OCR if pdfplumber fails or confidence is low
            if not text.strip() or confidence < 30:
                logger.info(f"Falling back to OCR for {filename}")
                ocr_text = self.extract_text_with_ocr(pdf_bytes)
                ocr_confidence = self.calculate_confidence(ocr_text, "ocr")
                
                if ocr_confidence > confidence:
                    text = ocr_text
                    confidence = ocr_confidence
                    metadata['extraction_method'] = 'ocr'
                else:
                    metadata['extraction_method'] = 'pdfplumber'
            else:
                metadata['extraction_method'] = 'pdfplumber'
            
            metadata['confidence'] = confidence
            metadata['filename'] = filename
            metadata['word_count'] = len(text.split())
            metadata['page_count'] = len(re.findall(r'\[PAGE_\d+\]', text))
            
            return ProcessingResult(
                success=bool(text.strip()),
                text=text,
                metadata=metadata,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {str(e)}")
            return ProcessingResult(
                success=False,
                text="",
                metadata={'filename': filename},
                error=str(e),
                confidence=0.0
            )

class TextProcessor:
    """Enhanced text processing with intelligent chunking"""
    
    def __init__(self):
        self.chunk_size = 1500
        self.chunk_overlap = 250
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Missing spaces
        text = re.sub(r'(\w+)\s+-\s+(\w+)', r'\1\2', text)  # Hyphenated words
        
        # Preserve important markers
        text = re.sub(r'\[PAGE_(\d+)\]', r'\n\n[PAGE_\1]\n\n', text)
        text = re.sub(r'\[TABLE_START\](.*?)\[TABLE_END\]', r'\n\n[TABLE_START]\1[TABLE_END]\n\n', text, flags=re.DOTALL)
        
        return text.strip()
    
    def extract_structured_content(self, text: str) -> Dict[str, List[str]]:
        """Extract structured content types"""
        structured = {
            'pages': [],
            'tables': [],
            'formulas': [],
            'references': []
        }
        
        # Extract page content
        page_pattern = r'\[PAGE_(\d+)\](.*?)\[PAGE_\d+\]|$'
        pages = re.findall(page_pattern, text, re.DOTALL)
        for page_num, page_content in pages:
            if page_content.strip():
                structured['pages'].append(page_content.strip())
        
        # Extract tables
        tables = re.findall(r'\[TABLE_START\](.*?)\[TABLE_END\]', text, re.DOTALL)
        structured['tables'] = [table.strip() for table in tables]
        
        # Extract formulas (simple pattern)
        formulas = re.findall(r'([a-zA-Z]\s*=\s*[^=\n]+|\\[.*?\\])', text)
        structured['formulas'] = [f.strip() for f in formulas if f.strip()]
        
        # Extract references
        references = re.findall(r'\b\d+\.\s+[^.]+\.(?:\s+\d+\(\d+\):\s*\d+-\d+)?', text)
        structured['references'] = [ref.strip() for ref in references]
        
        return structured
    
    def create_chunks(self, text: str, metadata: Dict) -> List[str]:
        """Create intelligent text chunks with metadata"""
        cleaned_text = self.clean_text(text)
        structured = self.extract_structured_content(cleaned_text)
        
        chunks = []
        
        # Add metadata chunk
        meta_chunk = f"[METADATA]\n"
        meta_chunk += f"Filename: {metadata.get('filename', 'Unknown')}\n"
        meta_chunk += f"Title: {metadata.get('title', 'Unknown')}\n"
        meta_chunk += f"Author: {metadata.get('author', 'Unknown')}\n"
        meta_chunk += f"Pages: {metadata.get('pages', 0)}\n"
        meta_chunk += f"Extraction Method: {metadata.get('extraction_method', 'Unknown')}\n"
        meta_chunk += f"Confidence: {metadata.get('confidence', 0):.1f}%\n"
        meta_chunk += "[/METADATA]\n"
        chunks.append(meta_chunk)
        
        # Process structured content
        if structured['tables']:
            for i, table in enumerate(structured['tables']):
                table_chunk = f"[TABLE_{i+1}]\n{table}\n[/TABLE_{i+1}]\n"
                if len(table_chunk) < self.chunk_size:
                    chunks.append(table_chunk)
        
        if structured['formulas']:
            for i, formula in enumerate(structured['formulas']):
                formula_chunk = f"[FORMULA_{i+1}]\n{formula}\n[/FORMULA_{i+1}]\n"
                chunks.append(formula_chunk)
        
        # Split remaining content
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
        )
        
        # Add page-based chunks
        for page_content in structured['pages']:
            if page_content:
                page_chunks = splitter.split_text(page_content)
                chunks.extend(page_chunks)
        
        # If no page content, split the entire text
        if not structured['pages'] and cleaned_text:
            chunks.extend(splitter.split_text(cleaned_text))
        
        # Filter out very small chunks
        chunks = [chunk for chunk in chunks if len(chunk.strip()) > 100]
        
        return chunks

class RAGEngine:
    """Enhanced RAG engine with better retrieval and response generation"""
    
    def __init__(self, use_ollama: bool = False):
        self.use_ollama = use_ollama
        self.embeddings = None
        self.vectorstore = None
        self.conversation_chain = None
        self.setup_embeddings()
        
    def setup_embeddings(self):
        """Setup embeddings with better models"""
        try:
            if self.use_ollama:
                # Use Ollama embeddings (if available)
                from langchain_community.embeddings import OllamaEmbeddings
                self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
            else:
                # Use HuggingFace embeddings
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
                )
        except Exception as e:
            logger.error(f"Failed to setup embeddings: {str(e)}")
            # Fallback to basic embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    def create_vectorstore(self, chunks: List[str]) -> FAISS:
        """Create vectorstore from chunks"""
        try:
            # Create vectorstore with progress tracking
            progress_bar = st.progress(0)
            total_chunks = len(chunks)
            
            # Process in batches for better performance
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, total_chunks, batch_size):
                batch = chunks[i:i+batch_size]
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                progress_bar.progress(min((i + batch_size) / total_chunks, 1.0))
            
            progress_bar.empty()
            
            # Create FAISS vectorstore
            self.vectorstore = FAISS.from_embeddings(
                text_embeddings=zip(chunks, all_embeddings),
                embedding=self.embeddings
            )
            
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"Failed to create vectorstore: {str(e)}")
            raise
    
    def create_conversation_chain(self, vectorstore: FAISS):
        """Create enhanced conversation chain"""
        try:
            # Setup LLM
            if self.use_ollama:
                llm = Ollama(
                    model="llama3.2",
                    temperature=0.1,
                    top_p=0.9,
                    num_ctx=4096
                )
            else:
                llm = ChatGroq(
                    model="llama3-70b-8192",
                    temperature=0.1,
                    max_tokens=4096,
                    api_key=os.getenv("GROQ_API_KEY")
                )
            
            # Enhanced memory with summarization
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key='answer',
                k=10  # Keep last 10 messages
            )
            
            # Enhanced prompt template
            custom_prompt = PromptTemplate(
                input_variables=["context", "question", "chat_history"],
                template="""You are an expert academic assistant analyzing research documents. 
                Use the following context to answer the question accurately and comprehensively.
                
                Context from documents:
                {context}
                
                Previous conversation:
                {chat_history}
                
                Current question: {question}
                
                Instructions:
                1. Provide detailed, accurate answers based ONLY on the given context
                2. Include relevant quotes and page references when available
                3. If information is not in the context, clearly state that
                4. Use proper academic formatting with clear structure
                5. Add confidence level (High/Medium/Low) based on source quality
                6. Format mathematical formulas with LaTeX when appropriate
                
                Answer:"""
            )
            
            # Create retrieval chain with enhanced parameters
            self.conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vectorstore.as_retriever(
                    search_kwargs={
                        "k": 6,  # Retrieve more documents
                        "score_threshold": 0.7,  # Minimum relevance score
                        "fetch_k": 20  # Fetch more candidates initially
                    }
                ),
                memory=memory,
                chain_type="stuff",
                combine_docs_chain_kwargs={"prompt": custom_prompt},
                return_source_documents=True,
                verbose=False
            )
            
            return self.conversation_chain
            
        except Exception as e:
            logger.error(f"Failed to create conversation chain: {str(e)}")
            raise
    
    def process_query(self, query: str) -> Dict:
        """Process query and return enhanced response"""
        try:
            start_time = time.time()
            
            # Get response from chain
            result = self.conversation_chain({"question": query})
            
            # Calculate confidence based on source documents
            confidence = self.calculate_response_confidence(
                result.get('source_documents', []),
                result['answer']
            )
            
            # Format response with sources
            formatted_response = {
                'answer': result['answer'],
                'sources': self.format_sources(result.get('source_documents', [])),
                'confidence': confidence,
                'response_time': time.time() - start_time,
                'chat_history': result.get('chat_history', [])
            }
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            return {
                'answer': f"I apologize, but I encountered an error processing your question: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'response_time': 0.0,
                'chat_history': []
            }
    
    def calculate_response_confidence(self, source_docs: List, answer: str) -> str:
        """Calculate confidence level based on source quality and answer completeness"""
        if not source_docs:
            return "Low"
        
        # Check source relevance scores
        avg_score = sum(getattr(doc, 'score', 0.5) for doc in source_docs) / len(source_docs)
        
        # Check answer quality
        answer_length = len(answer.split())
        has_specific_info = any(pattern in answer.lower() for pattern in [
            'according to', 'page', 'section', 'table', 'figure', 'shows'
        ])
        
        if avg_score > 0.8 and answer_length > 50 and has_specific_info:
            return "High"
        elif avg_score > 0.6 and answer_length > 30:
            return "Medium"
        else:
            return "Low"
    
    def format_sources(self, source_docs: List) -> List[Dict]:
        """Format source documents for display"""
        sources = []
        for doc in source_docs:
            # Extract metadata from document content
            content = doc.page_content
            metadata = doc.metadata
            
            # Try to extract page information
            page_match = re.search(r'\[PAGE_(\d+)\]', content)
            page_num = page_match.group(1) if page_match else "Unknown"
            
            # Clean content for display
            clean_content = re.sub(r'\[.*?\]', '', content)[:200] + "..."
            
            sources.append({
                'content': clean_content,
                'page': page_num,
                'score': getattr(doc, 'score', 0.0),
                'metadata': metadata
            })
        
        return sources

class SummaryGenerator:
    """Enhanced summary generation with better prompts"""
    
    def __init__(self, use_ollama: bool = False):
        self.use_ollama = use_ollama
        
    def generate_summary(self, text: str, filename: str, metadata: Dict) -> str:
        """Generate comprehensive academic summary"""
        try:
            # Trim text to reasonable size
            max_chars = 15000
            if len(text) > max_chars:
                text = text[:max_chars] + "... [TRUNCATED]"
            
            # Enhanced prompt for better summaries
            prompt = f"""Create a comprehensive academic summary for the document "{filename}".
            
            Document metadata:
            - Title: {metadata.get('title', 'Unknown')}
            - Author: {metadata.get('author', 'Unknown')}
            - Pages: {metadata.get('pages', 'Unknown')}
            - Extraction confidence: {metadata.get('confidence', 0):.1f}%
            
            Content to summarize:
            {text}
            
            Please provide a structured summary with the following sections:
            
            # Document Summary: {filename}
            
            ## ðŸ“‹ Document Overview
            [Brief description of the document type, subject area, and main purpose]
            
            ## ðŸ‘¥ Authors & Affiliations
            [Detailed author information and institutional affiliations if available]
            
            ## ðŸŽ¯ Key Objectives
            [Main research questions, objectives, or purposes of the document]
            
            ## ðŸ”¬ Methodology
            [Research methods, approaches, or analytical frameworks used]
            
            ## ðŸ“Š Key Findings
            [Major findings, results, or conclusions with specific details]
            
            ## ðŸ’¡ Main Contributions
            [Novel contributions, innovations, or insights provided]
            
            ## ðŸ“š References & Citations
            [Key references, citations, or related work mentioned]
            
            ## âš ï¸ Limitations & Future Work
            [Acknowledged limitations and suggested future research directions]
            
            ## ðŸ”— Technical Details
            [Important technical specifications, datasets, or implementation details]
            
            Format the response with proper Markdown, including:
            - Clear section headers
            - Bullet points for lists
            - Bold for emphasis
            - Tables for structured data
            - Code blocks for technical content
            """
            
            # Generate summary using appropriate LLM
            if self.use_ollama:
                llm = Ollama(model="llama3.2", temperature=0.3)
                summary = llm.invoke(prompt)
            else:
                llm = ChatGroq(
                    model="llama3-70b-8192",
                    temperature=0.3,
                    max_tokens=4096,
                    api_key=os.getenv("GROQ_API_KEY")
                )
                summary = llm.invoke(prompt).content
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return f"Error generating summary: {str(e)}"

# Initialize components
@st.cache_resource
def init_processors():
    """Initialize processing components"""
    return {
        'pdf_processor': PDFProcessor(),
        'text_processor': TextProcessor(),
        'rag_engine': None,
        'summary_generator': None
    }

# Main application
def main():
    st.title("ðŸ“„ iPDF Pro - Intelligent PDF Assistant")
    st.markdown("""
    **Advanced PDF analysis with AI-powered insights, summaries, and intelligent Q&A.**
    Upload your PDF documents and get comprehensive analysis with confidence scores.
    """)
    
    # Initialize components
    processors = init_processors()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("ðŸ“ Document Upload")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            accept_multiple_files=True,
            type=['pdf'],
            help="Upload multiple PDF files for analysis"
        )
        
        st.header("âš™ï¸ Processing Options")
        
        # LLM selection
        llm_option = st.selectbox(
            "Language Model",
            ["Groq (Fast Cloud)", "Ollama (Local)"],
            help="Choose between cloud-based Groq or local Ollama"
        )
        use_ollama = llm_option == "Ollama (Local)"
        
        # OCR option
        enable_ocr = st.checkbox(
            "Enable OCR Fallback",
            value=True,
            help="Use OCR when text extraction fails"
        )
        
        # Processing button
        process_button = st.button(
            "ðŸš€ Process Documents",
            type="primary",
            disabled=not uploaded_files
        )
        
        # Summary generation button
        generate_summary_button = st.button(
            "ðŸ“‹ Generate Summaries",
            disabled=not st.session_state.get('processed', False)
        )
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["ðŸ’¬ Chat", "ðŸ“Š Analysis", "â„¹ï¸ About"])
    
    # Process documents
    if process_button and uploaded_files:
        with st.spinner("Processing documents..."):
            process_documents(uploaded_files, processors, enable_ollama=use_ollama)
    
    # Generate summaries
    if generate_summary_button and st.session_state.get('processed', False):
        with st.spinner("Generating comprehensive summaries..."):
            generate_summaries(processors, enable_ollama=use_ollama)
    
    # Chat tab
    with tab1:
        if st.session_state.get('rag_engine') is not None:
            handle_chat_interface()
        else:
            st.info("ðŸ‘ˆ Upload and process documents to start chatting")
    
    # Analysis tab
    with tab2:
        if st.session_state.get('processed', False):
            show_document_analysis()
        else:
            st.info("ðŸ‘ˆ Process documents to view analysis")
    
    # About tab
    with tab3:
        show_about_info()

def process_documents(files, processors, enable_ollama=False):
    """Process uploaded documents"""
    try:
        results = {}
        progress_bar = st.progress(0)
        
        for i, file in enumerate(files):
            st.write(f"Processing: {file.name}")
            
            # Process PDF
            file_bytes = file.getvalue()
            result = processors['pdf_processor'].process_pdf(file_bytes, file.name)
            
            if result.success and result.text.strip():
                # Create chunks
                chunks = processors['text_processor'].create_chunks(result.text, result.metadata)
                
                results[file.name] = {
                    'text': result.text,
                    'chunks': chunks,
                    'metadata': result.metadata,
                    'confidence': result.confidence
                }
                
                st.success(f"âœ… {file.name} processed (confidence: {result.confidence:.1f}%)")
            else:
                st.error(f"âŒ Failed to process {file.name}: {result.error}")
            
            progress_bar.progress((i + 1) / len(files))
        
        # Create vectorstore from all chunks
        if results:
            all_chunks = []
            for file_data in results.values():
                all_chunks.extend(file_data['chunks'])
            
            if all_chunks:
                # Initialize RAG engine
                processors['rag_engine'] = RAGEngine(use_ollama=enable_ollama)
                
                # Create vectorstore
                vectorstore = processors['rag_engine'].create_vectorstore(all_chunks)
                
                # Create conversation chain
                conversation_chain = processors['rag_engine'].create_conversation_chain(vectorstore)
                
                # Store in session state
                st.session_state['rag_engine'] = processors['rag_engine']
                st.session_state['processed_results'] = results
                st.session_state['processed'] = True
                st.session_state['chat_history'] = []
                
                st.success("ðŸŽ‰ Documents processed successfully! Ready for Q&A.")
            else:
                st.error("No text content extracted from documents.")
        
        progress_bar.empty()
        
    except Exception as e:
        st.error(f"Error processing documents: {str(e)}")
        logger.error(f"Document processing failed: {str(e)}")

def generate_summaries(processors, enable_ollama=False):
    """Generate summaries for processed documents"""
    try:
        if 'summary_generator' not in processors or processors['summary_generator'] is None:
            processors['summary_generator'] = SummaryGenerator(use_ollama=enable_ollama)
        
        results = st.session_state['processed_results']
        summaries = {}
        
        progress_bar = st.progress(0)
        
        for i, (filename, data) in enumerate(results.items()):
            summary = processors['summary_generator'].generate_summary(
                data['text'], 
                filename, 
                data['metadata']
            )
            summaries[filename] = summary
            progress_bar.progress((i + 1) / len(results))
        
        st.session_state['summaries'] = summaries
        progress_bar.empty()
        
        st.success("ðŸ“‹ Summaries generated successfully!")
        
    except Exception as e:
        st.error(f"Error generating summaries: {str(e)}")

def handle_chat_interface():
    """Handle the chat interface"""
    # Display chat history
    for idx, message in enumerate(st.session_state.get('chat_history', [])):
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                st.write(message['content'])
                
                # Show confidence and sources
                col1, col2 = st.columns(2)
                with col1:
                    confidence = message.get('confidence', 'Unknown')
                    confidence_class = f"confidence-{confidence.lower()}"
                    st.markdown(f"<span class='confidence-badge {confidence_class}'>{confidence} Confidence</span>", unsafe_allow_html=True)
                
                with col2:
                    if message.get('sources'):
                        with st.expander("ðŸ“š View Sources"):
                            for source in message['sources']:
                                st.write(f"**Page {source['page']}** (Score: {source['score']:.2f})")
                                st.caption(source['content'])
    
    # Chat input
    if query := st.chat_input("Ask about your documents..."):
        # Add user message
        st.session_state['chat_history'].append({
            'role': 'user',
            'content': query
        })
        
        # Get response
        with st.spinner("Generating response..."):
            response = st.session_state['rag_engine'].process_query(query)
        
        # Add assistant message
        st.session_state['chat_history'].append({
            'role': 'assistant',
            'content': response['answer'],
            'confidence': response['confidence'],
            'sources': response['sources'],
            'response_time': response['response_time']
        })
        
        # Show response info
        st.caption(f"Response generated in {response['response_time']:.1f} seconds")
        
        # Rerun to update UI
        st.rerun()

def show_document_analysis():
    """Show document analysis and statistics"""
    if 'processed_results' not in st.session_state:
        st.info("No documents processed yet.")
        return
    
    results = st.session_state['processed_results']
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents", len(results))
    
    with col2:
        total_words = sum(data['metadata'].get('word_count', 0) for data in results.values())
        st.metric("Total Words", f"{total_words:,}")
    
    with col3:
        avg_confidence = sum(data['confidence'] for data in results.values()) / len(results)
        st.metric("Avg Confidence", f"{avg_confidence:.1f}%")
    
    with col4:
        total_chunks = sum(len(data['chunks']) for data in results.values())
        st.metric("Text Chunks", total_chunks)
    
    # Document details
    st.header("ðŸ“„ Document Details")
    
    for filename, data in results.items():
        with st.expander(f"ðŸ“„ {filename}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Metadata:**")
                for key, value in data['metadata'].items():
                    if key != 'confidence':
                        st.write(f"- {key.replace('_', ' ').title()}: {value}")
            
            with col2:
                st.write("**Processing Info:**")
                st.write(f"- Confidence: {data['confidence']:.1f}%")
                st.write(f"- Text Chunks: {len(data['chunks'])}")
                st.write(f"- Word Count: {data['metadata'].get('word_count', 0):,}")
            
            # Show summary if available
            if 'summaries' in st.session_state and filename in st.session_state['summaries']:
                st.write("**Summary:**")
                st.markdown(st.session_state['summaries'][filename])
    
    # Show summaries section
    if 'summaries' in st.session_state:
        st.header("ðŸ“‹ Document Summaries")
        for filename, summary in st.session_state['summaries'].items():
            with st.expander(f"Summary: {filename}"):
                st.markdown(summary)

def show_about_info():
    """Show about information"""
    st.header("About iPDF Pro")
    
    st.markdown("""
    iPDF Pro is an advanced PDF analysis tool that combines multiple AI technologies to provide:
    
    ## âœ¨ Key Features
    
    - **ðŸ“„ Multi-PDF Processing**: Handle multiple PDF documents simultaneously
    - **ðŸ” Intelligent Text Extraction**: Advanced OCR fallback for scanned documents  
    - **ðŸ§  Enhanced RAG System**: Better retrieval and response generation
    - **ðŸ“Š Confidence Scoring**: Quality assessment for extracted content
    - **ðŸ’¬ Smart Q&A**: Context-aware answers with source attribution
    - **ðŸ“ Automatic Summaries**: Comprehensive document analysis
    
    ## ðŸ› ï¸ Technology Stack
    
    - **LLM**: Groq (Llama 3.1 70B) or Ollama (local)
    - **Embeddings**: Sentence Transformers / Ollama Embeddings
    - **Vector Store**: FAISS for fast similarity search
    - **PDF Processing**: pdfplumber + pytesseract OCR
    - **UI**: Streamlit with custom components
    
    ## ðŸ“ˆ Improvements Over Original
    
    - Better error handling and user feedback
    - Enhanced text extraction with OCR fallback
    - Improved chunking and retrieval strategies
    - Confidence scoring for answer quality
    - Comprehensive document summaries
    - Better source attribution and formatting
    
    ## ðŸ”§ Configuration
    
    Ensure you have the following environment variables set:
    - `GROQ_API_KEY`: For Groq LLM access
    - `TESSERACT_PATH`: Path to tesseract executable (optional)
    
    For Ollama users:
    - Install Ollama and pull `llama3.2` and `nomic-embed-text` models
    """)

if __name__ == "__main__":
    main()