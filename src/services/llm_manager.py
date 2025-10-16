# src/services/llm_manager.py
import os
from src.config.logger import logger
from src.config.exception import CustomException
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama

def get_llm(use_ollama: bool = False, groq_api_key: str = None, model_name: str = None):
    try:
        if use_ollama:
            model = model_name or "llama3"
            logger.info(f"Using Ollama LLM: {model}")
            return Ollama(model=model)
        else:
            model = model_name or "llama3-70b-8192"
            api_key = groq_api_key or os.getenv("GROQ_API_KEY")
            logger.info(f"Using Groq LLM: {model}")
            return ChatGroq(model=model, temperature=0.1, api_key=api_key)
    except Exception as e:
        logger.exception("Failed to initialize LLM")
        raise CustomException(e, __import__("sys"))
