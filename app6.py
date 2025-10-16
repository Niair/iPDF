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

# Basic Config
st.set_page_config(page_title="PDF Chat Pro", layout="wide", )
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
load_dotenv()

st.title("⚡ Chat with iPDF")

# Load icons
def load_icon_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

copy_icon_b64 = load_icon_base64("copy_icon.png")
copied_icon_b64 = load_icon_base64("copied_icon.png")

# cache expensive operations
@st.cache_data(show_spinner=False, hash_funcs={bytes: lambda x: hashlib.sha256(x).hexdigest()})
def get_single_pdf_text(pdf_bytes, filename, enable_ocr=True):
    """Process a single PDF with caching"""
    text = ""
    try:
        with pdfplumber.open(pdf_bytes) as pdf_reader:
            # Extract metadata from first page
            first_page = pdf_reader.pages[0]
            metadata = first_page.extract_text()[:1000] if first_page.extract_text() else ""
            
            # Process pages in bulk
            pages = pdf_reader.pages
            for page in pages:
                page_text = page.extract_text() or ""
                
                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        table_text = "\n".join(["\t".join(cell or "" for cell in row) for row in table])
                        text += f"\n[Table]\n{table_text}\n[/Table]\n"
                
                # Preserve formulas
                page_text = re.sub(r'(\w+)\s*=\s*([^\.\n]+)', r'\1 = \2 [FORMULA]', page_text)
                text += page_text + "\n"
            
            # Add metadata marker
            if metadata:
                text = f"[METADATA_START]\n{metadata}\n[METADATA_END]\n" + text
        
    except Exception as e:
        # Error will be handled by caller
        pass
    
    # Fallback to OCR if no text extracted and OCR enabled
    if not text.strip() and enable_ocr:
        try:
            images = convert_from_bytes(pdf_bytes, dpi=100)  # Lower DPI for speed
            with concurrent.futures.ThreadPoolExecutor() as executor:
                ocr_results = list(executor.map(pytesseract.image_to_string, images))
            text = "\n".join(ocr_results)
        except Exception as ocr_error:
            # OCR failed, return empty string
            pass
            
    return text

def get_pdf_text(pdf_docs, enable_ocr=True):
    """Process multiple PDFs in parallel"""
    texts = {}
    empty_files = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {}
        for pdf in pdf_docs:
            content = pdf.getvalue()
            futures[executor.submit(get_single_pdf_text, content, pdf.name, enable_ocr)] = pdf.name
        
        progress_bar = st.progress(0)
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            pdf_name = futures[future]
            try:
                result = future.result()
                texts[pdf_name] = result
                if not result.strip():
                    empty_files.append(pdf_name)
            except Exception as e:
                st.warning(f"⚠️ Error processing {pdf_name}: {e}")
                texts[pdf_name] = ""
                empty_files.append(pdf_name)
            progress_bar.progress((i + 1) / len(futures))
        progress_bar.empty()
    
    # show warnings for empty files
    if empty_files:
        st.warning(f"⚠️ No text extracted from: {', '.join(empty_files)}")
    
    st.info(f"📊 Processed {len(pdf_docs)} PDFs in {time.time() - start_time:.1f} seconds")
    return texts

# text chunks
def get_text_chunks(text):

    metadata_match = re.search(r'\[METADATA_START\](.*?)\[METADATA_END\]', text, re.DOTALL)
    metadata_chunk = [metadata_match.group(1)] if metadata_match else []
    
    cleaned_text = re.sub(r'\[METADATA_START\].*?\[METADATA_END\]', '', text, flags=re.DOTALL)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=250,
        separators=["\n\n", "\n", "\.\s+", "•", " ", ""]
    )
    content_chunks = splitter.split_text(cleaned_text)
    
    return metadata_chunk + content_chunks

# embeddings with caching
@st.cache_resource(show_spinner=False)
def get_vectorstore(text_chunks):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",  # Faster model
        model_kwargs={'device': 'cpu'},  # Explicitly use CPU
        encode_kwargs={'normalize_embeddings': False}
    )
    return FAISS.from_texts(texts=text_chunks, embedding=embeddings)

# conversation
def get_conversation_chain(vectorstore, use_ollama=False):
    llm = Ollama(model="llama3") if use_ollama else ChatGroq(
        model="llama3-70b-8192",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key='answer'
    )
    
    # Efficient prompt template
    custom_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
        As an academic assistant, answer the question using ONLY the provided context.
        Guidelines:
        1. Preserve original notation for formulas
        2. Cite section numbers when possible
        3. For author queries, check metadata first
        4. Format with Markdown: headings, bullet points, tables
        5. Be concise but thorough
        
        Context: {context}
        
        Question: {question}
        
        Answer:
        """
    )
    
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),  # Fewer results for speed
        memory=memory,
        chain_type="stuff",
        combine_docs_chain_kwargs={"prompt": custom_prompt},
        return_source_documents=True,
        get_chat_history=lambda h: h
    )

# summary generation with better prompt
def get_summary(raw_texts, use_ollama=False):
    llm_model = "llama3-70b-8192"
    if use_ollama:
        llm_model = "llama3"
    
    def generate_summary(args):
        filename, text_content = args

        trimmed_text = text_content[:12000]  
        
        prompt = f"""
        Create a comprehensive academic summary for "{filename}" in well-structured markdown format:

        ## Document Information
        **File Name:** {filename}  
        
        ## Title 
        [The title of the document]
        
        ## Authors & Affiliations
        [List all authors with their affiliations in the format:  
        - **Author Name** (Affiliation 1; Affiliation 2)  
        - **Author Name** (Affiliation 3)]
        
        ## Abstract
        [A concise abstract of the document]
        
        ## Key Contributions
        [Bullet points of the main contributions:  
        - **Contribution 1** with brief explanation  
        - **Contribution 2** with brief explanation  
        - **Contribution 3** with brief explanation]
        
        ## Methodology Highlights
        [Detailed description of methods used:  
        - **Method 1**: Explanation  
        - **Method 2**: Explanation]
        
        ## Main Findings
        [Detailed findings with quantitative results:  
        - **Finding 1**: Explanation with supporting data (e.g., 95% accuracy)  
        - **Finding 2**: Explanation with supporting data]
        
        ## References
        [List at least 5 key references from the document in APA format:  
        1. Author, A. A., Author, B. B., & Author, C. C. (Year). *Title of article*. Journal Name, Volume(Issue), Page-Page. DOI/URL  
        2. Author, D. D., & Author, E. E. (Year). *Title of book*. Publisher.  
        ...]
        
        ## Additional Notes
        [Any other important information:  
        - Datasets used  
        - Limitations  
        - Future work directions]
        
        Preserve technical terms, formulas, and important notations. Use proper markdown formatting throughout.
        
        Content:
        {trimmed_text}
        """
        
        if use_ollama:
            llm = Ollama(model=llm_model)
            return llm.invoke(prompt).content.strip()
        else:
            llm = ChatGroq(model=llm_model, temperature=0.1, api_key=os.getenv("GROQ_API_KEY"))
            return llm.invoke(prompt).content.strip()
    
    # parallel processing summary
    all_summaries = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(generate_summary, (fn, txt)): fn 
                   for fn, txt in raw_texts.items()}
        
        progress_bar = st.progress(0)
        completed = 0
        total = len(futures)
        
        for future in concurrent.futures.as_completed(futures):
            filename = futures[future]
            try:
                all_summaries.append(future.result())
            except Exception as e:
                st.warning(f"⚠️ Error summarizing {filename}: {e}")
                all_summaries.append(f"### Summary for {filename} failed\nError: {str(e)}")
            
            completed += 1
            progress_bar.progress(completed / total)
        progress_bar.empty()
    
    return "\n\n---\n\n".join(all_summaries)

# summary display
def display_summary(content):
    """Displays summary with proper formatting and copy button"""
    sections = re.split(r'\n## ', content)
    formatted_content = ""
    
    for section in sections:
        if not section.strip():
            continue
            
        # extracting title and content
        if '\n' in section:
            title, body = section.split('\n', 1)
        else:
            title, body = section, ""
            
        # formatting the body
        body = re.sub(r'^- (.*?)$', r'- \1', body, flags=re.MULTILINE)
        
        body = re.sub(r'^- \*\*(.*?)\*\*', r'- **\1**', body, flags=re.MULTILINE)
        
        body = re.sub(r'^(\d+)\.', r'\1. ', body, flags=re.MULTILINE)
        
        formatted_content += f"## {title}\n{body}\n\n"
    
    st.markdown(formatted_content, unsafe_allow_html=True)
    
    unique_key = f"summary-{hash(content) & 0xFFFFFFFF}"
    html_code = f"""
    <div style="text-align: right; margin-top: 20px;">
        <button id="copy-summary-btn" style="border: none; background: none; cursor: pointer;">
            <img id="copy-summary-icon" src="data:image/png;base64,{copy_icon_b64}" width="24" height="24"/>
            <span style="vertical-align: middle; margin-left: 5px;">Copy Summary</span>
        </button>
    </div>
    <script>
        document.getElementById("copy-summary-btn").addEventListener('click', function() {{
            const content = `{content.replace('`', '\\`').replace('\\', '\\\\')}`;
            navigator.clipboard.writeText(content).then(function() {{
                const icon = document.getElementById("copy-summary-icon");
                icon.src = "data:image/png;base64,{copied_icon_b64}";
                setTimeout(function() {{
                    icon.src = "data:image/png;base64,{copy_icon_b64}";
                }}, 1000);
            }});
        }});
    </script>
    """
    st.components.v1.html(html_code, height=50)

# for better chat response
def render_message_with_copy(text, role, idx):
    if role == "assistant":
        st.chat_message(role).markdown(text)
    else:
        st.chat_message(role).write(text)
    
    # copy button
    html(f"""
    <div style="margin-top: -10px; margin-bottom: 20px; display: flex; align-items: center; height: 24px;">
        <button onclick="copyText{idx}()" style="border: none; background: none; cursor: pointer; padding: 0;">
            <img id="copy-icon-{idx}" src="data:image/png;base64,{copy_icon_b64}" width="16" height="16"/>
        </button>
    </div>
    <script>
    function copyText{idx}() {{
        const text = `{text.replace("`", "\\`").replace("\\", "\\\\")}`;
        navigator.clipboard.writeText(text).then(function() {{
            const icon = document.getElementById("copy-icon-{idx}");
            icon.src = "data:image/png;base64,{copied_icon_b64}";
            setTimeout(function() {{
                icon.src = "data:image/png;base64,{copy_icon_b64}";
            }}, 1000);
        }});
    }}
    </script>
    """, height=30)

# sidebar
with st.sidebar:
    st.header("📁 Upload PDFs")
    pdf_docs = st.file_uploader("Upload files", accept_multiple_files=True, type=["pdf"], 
                               help="For best performance, upload text-based PDFs under 50 pages")
    
    st.header("⚙️ Processing Options")
    llm_choice = st.radio("Language Model:", ["Groq (fast)", "Ollama (local)"], index=0, horizontal=True)
    use_ollama = llm_choice == "Ollama (local)"
    
    ocr_option = st.checkbox("Enable OCR fallback", True, 
                            help="Use OCR when text extraction fails (slower)")
    
    st.divider()
    
    if st.button("🚀 Process Documents", type="primary") and pdf_docs:
        filenames = [pdf.name for pdf in pdf_docs]
        cache_key = hashlib.sha256(str(filenames).encode()).hexdigest()
        
        if cache_key != st.session_state.get("processed_key", ""):
            with st.spinner("Processing documents..."):
                # Store texts by filename
                raw_texts = get_pdf_text(pdf_docs, ocr_option)
                
                # Check if any text was extracted
                if not any(text.strip() for text in raw_texts.values()):
                    st.error("❗ No text extracted from any document. Enable OCR or check files.")
                    st.stop()
                
                # Build list of all chunks from all documents
                all_chunks = []
                for name, text in raw_texts.items():
                    chunks = get_text_chunks(text)
                    all_chunks.extend(chunks)
                
                vectorstore = get_vectorstore(all_chunks)
                st.session_state.raw_texts = raw_texts
                st.session_state.conversation = get_conversation_chain(vectorstore, use_ollama)
                st.session_state.chat_history = []
                st.session_state.processed_files = filenames
                st.session_state.processed_key = cache_key
            st.success("✅ Ready! Start chatting below.")
        else:
            st.info("❗ Using cached processing results")

    if "raw_texts" in st.session_state and st.button("📄 Generate Summaries"):
        with st.spinner("Creating comprehensive summaries..."):
            summary = get_summary(st.session_state.raw_texts, use_ollama)
        st.session_state.pdf_summary = summary

# Main content area
tab1, tab2 = st.tabs(["💬 Chat", "📋 Summaries"])

with tab1:
    if "conversation" in st.session_state:
        # For chat history
        for idx, (user_query, bot_response) in enumerate(st.session_state.chat_history):
            render_message_with_copy(user_query, "user", idx*2)
            render_message_with_copy(bot_response, "assistant", idx*2+1)
            
        # Chat input
        query = st.chat_input("Ask about your documents...", key="chat_input")
        if query:
            with st.spinner("Generating response..."):
                start_time = time.time()
                result = st.session_state.conversation({"question": query})
                response_time = time.time() - start_time
                
                formatted_response = result["answer"].replace("[FORMULA]", "**").replace("[/FORMULA]", "**")
                st.session_state.chat_history.append((query, formatted_response))
                
                st.caption(f"Response generated in {response_time:.1f}s")
                st.rerun()
    else:
        st.info("👆 Upload and process documents to start chatting")

with tab2:
    if "pdf_summary" in st.session_state:
        st.subheader("Document Summaries")
        display_summary(st.session_state.pdf_summary)
    else:
        st.info("👆 Generate summaries using the sidebar button")