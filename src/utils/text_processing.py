# src/utils/text_processing.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from typing import List

def get_text_chunks(text: str, chunk_size: int = 1500, chunk_overlap: int = 250) -> List[str]:
    metadata_match = re.search(r'\[METADATA_START\](.*?)\[METADATA_END\]', text, re.DOTALL)
    metadata_chunk = [metadata_match.group(1)] if metadata_match else []
    cleaned_text = re.sub(r'\[METADATA_START\].*?\[METADATA_END\]', '', text, flags=re.DOTALL)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "\.\s+", "•", " ", ""]
    )
    content_chunks = splitter.split_text(cleaned_text)
    return metadata_chunk + content_chunks
