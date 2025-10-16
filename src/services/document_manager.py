# src/services/document_manager.py
from src.utils.pdf_extractor import get_pdf_text
from src.utils.text_processing import get_text_chunks
from src.services.vectorstore_service import build_vectorstore
from src.utils.conversation_chain import get_conversation_chain
from src.config.logger import logger
from src.config.utils import save_object, hash_bytes
import streamlit as st

def process_documents(pdf_files, use_ollama=False, enable_ocr=True):
    """
    - Extract text from uploaded PDFs
    - Chunk and build vectorstore
    - Setup conversation chain and store in session_state
    """
    raw_texts = get_pdf_text(pdf_files, enable_ocr=enable_ocr)
    if not any(txt.strip() for txt in raw_texts.values()):
        raise ValueError("No text extracted from documents. Try enabling OCR.")

    # build chunks
    all_chunks = []
    for name, txt in raw_texts.items():
        chunks = get_text_chunks(txt)
        all_chunks.extend(chunks)

    vectorstore = build_vectorstore(all_chunks)
    conversation = get_conversation_chain(vectorstore, use_ollama=use_ollama)

    # store in streamlit session_state
    st.session_state.raw_texts = raw_texts
    st.session_state.conversation = conversation
    st.session_state.chat_history = []
    st.session_state.processed_files = [p.name for p in pdf_files]
    st.session_state.processed_key = hash_bytes("".join(st.session_state.processed_files).encode())

    logger.info("Documents processed and conversation chain created")
    return True
# src/services/document_manager.py
from src.utils.pdf_extractor import get_pdf_text
from src.utils.text_processing import get_text_chunks
from src.services.vectorstore_service import build_vectorstore
from src.utils.conversation_chain import get_conversation_chain
from src.config.logger import logger
from src.config.utils import save_object, hash_bytes
import streamlit as st

def process_documents(pdf_files, use_ollama=False, enable_ocr=True):
    """
    - Extract text from uploaded PDFs
    - Chunk and build vectorstore
    - Setup conversation chain and store in session_state
    """
    raw_texts = get_pdf_text(pdf_files, enable_ocr=enable_ocr)
    if not any(txt.strip() for txt in raw_texts.values()):
        raise ValueError("No text extracted from documents. Try enabling OCR.")

    # build chunks
    all_chunks = []
    for name, txt in raw_texts.items():
        chunks = get_text_chunks(txt)
        all_chunks.extend(chunks)

    vectorstore = build_vectorstore(all_chunks)
    conversation = get_conversation_chain(vectorstore, use_ollama=use_ollama)

    # store in streamlit session_state
    st.session_state.raw_texts = raw_texts
    st.session_state.conversation = conversation
    st.session_state.chat_history = []
    st.session_state.processed_files = [p.name for p in pdf_files]
    st.session_state.processed_key = hash_bytes("".join(st.session_state.processed_files).encode())

    logger.info("Documents processed and conversation chain created")
    return True
# src/services/document_manager.py
from src.utils.pdf_extractor import get_pdf_text
from src.utils.text_processing import get_text_chunks
from src.services.vectorstore_service import build_vectorstore
from src.utils.conversation_chain import get_conversation_chain
from src.config.logger import logger
from src.config.utils import save_object, hash_bytes
import streamlit as st

def process_documents(pdf_files, use_ollama=False, enable_ocr=True):
    """
    - Extract text from uploaded PDFs
    - Chunk and build vectorstore
    - Setup conversation chain and store in session_state
    """
    raw_texts = get_pdf_text(pdf_files, enable_ocr=enable_ocr)
    if not any(txt.strip() for txt in raw_texts.values()):
        raise ValueError("No text extracted from documents. Try enabling OCR.")

    # build chunks
    all_chunks = []
    for name, txt in raw_texts.items():
        chunks = get_text_chunks(txt)
        all_chunks.extend(chunks)

    vectorstore = build_vectorstore(all_chunks)
    conversation = get_conversation_chain(vectorstore, use_ollama=use_ollama)

    # store in streamlit session_state
    st.session_state.raw_texts = raw_texts
    st.session_state.conversation = conversation
    st.session_state.chat_history = []
    st.session_state.processed_files = [p.name for p in pdf_files]
    st.session_state.processed_key = hash_bytes("".join(st.session_state.processed_files).encode())

    logger.info("Documents processed and conversation chain created")
    return True
