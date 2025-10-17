"""PDF Service - Simplified"""
import sys
from pathlib import Path
from typing import List, Dict

from utils.logger import get_logger
from utils.exception import DocumentProcessingError
from utils.helpers import ensure_dir, get_file_hash, format_file_size
from core.document_processor import DocumentProcessor
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager

logger = get_logger(__name__)


class PDFService:
    """Service for PDF document management"""
    
    def __init__(self, upload_dir: str = "data/uploads"):
        """Initialize PDF service"""
        self.upload_dir = Path(upload_dir)
        ensure_dir(self.upload_dir)
        
        self.processor = DocumentProcessor()
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        
        logger.info("PDFService initialized")
    
    def upload_pdf(self, file_bytes: bytes, filename: str) -> str:
        """Upload and save PDF"""
        try:
            file_hash = get_file_hash(file_bytes)
            safe_filename = f"{file_hash}_{filename}"
            file_path = self.upload_dir / safe_filename
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            logger.info(f"Uploaded: {filename}")
            return str(file_path)
        
        except Exception as e:
            raise DocumentProcessingError(f"Upload failed: {str(e)}", sys)
    
    def process_and_index_pdf(self, file_path: str, filename: str) -> bool:
        """Process PDF and index in vector store"""
        try:
            logger.info(f"Processing: {filename}")
            
            # Process PDF
            result = self.processor.process_pdf(file_path, filename)
            
            if not result.success:
                raise DocumentProcessingError(f"Processing failed: {result.error}")
            
            # Get text elements
            text_elements = [e for e in result.elements if e.content_type.value == "text"]
            
            if not text_elements:
                logger.warning(f"No text found in {filename}")
                return False
            
            # Create chunks
            chunks = []
            payloads = []
            
            for elem in text_elements:
                chunk_size = 1000
                content = elem.content
                
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    if chunk.strip():
                        chunks.append(chunk)
                        payloads.append({
                            "filename": filename,
                            "page_number": elem.page_number,
                            "content_type": "text",
                            "content": chunk
                        })
            
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            embeddings = self.embedding_gen.generate_embeddings_batch(chunks)
            
            logger.info(f"Indexing {len(embeddings)} vectors...")
            self.vector_store.add_points(embeddings, payloads)
            
            logger.info(f"✅ Processed: {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise DocumentProcessingError(str(e), sys)
