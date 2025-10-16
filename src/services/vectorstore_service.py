# src/services/vectorstore_service.py
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from src.config.settings import settings
from src.config.logger import logger
from src.config.exception import CustomException
import os

def build_vectorstore(text_chunks, embedding_model: str = None):
    try:
        model_name = embedding_model or settings.DEFAULT_EMBEDDING_MODEL
        device = "cuda" if settings.USE_GPU else "cpu"
        embeddings = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={"device": device})
        logger.info("Creating FAISS vectorstore")
        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
        return vectorstore
    except Exception as e:
        logger.exception("Failed to build vectorstore")
        raise CustomException(e, __import__("sys"))
