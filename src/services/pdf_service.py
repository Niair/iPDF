"""
PDF Service - Manage PDF uploads and processing
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
import uuid

from utils.logger import get_logger
from utils.exception import DocumentProcessingError
from utils.helpers import ensure_dir, get_file_hash, format_file_size
from core.document_processor import DocumentProcessor
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager
from models.document import ProcessingResult

logger = get_logger(__name__)


class PDFService:
    """Service for PDF document management"""
    
    def __init__(self, upload_dir: str = "data/uploads"):
        """
        Initialize PDF service
        
        Args:
            upload_dir: Directory to store uploaded PDFs
        """
        self.upload_dir = Path(upload_dir)
        ensure_dir(self.upload_dir)
        
        self.processor = DocumentProcessor()
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        
        self.processed_docs: Dict[str, ProcessingResult] = {}
        
        logger.info("PDFService initialized")
    
    def upload_pdf(self, file_bytes: bytes, filename: str) -> str:
        """
        Upload and save PDF file
        
        Args:
            file_bytes: PDF file bytes
            filename: Original filename
            
        Returns:
            File path of saved PDF
        """
        try:
            # Generate unique ID
            file_hash = get_file_hash(file_bytes)
            safe_filename = f"{file_hash}_{filename}"
            file_path = self.upload_dir / safe_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            file_size = format_file_size(len(file_bytes))
            logger.info(f"✅ Uploaded PDF: {filename} ({file_size})")
            
            return str(file_path)
        
        except Exception as e:
            raise DocumentProcessingError(f"Failed to upload PDF: {str(e)}", sys)
    
    def process_and_index_pdf(self, file_path: str, filename: str) -> bool:
        """
        Process PDF and index in vector store
        
        Args:
            file_path: Path to PDF file
            filename: Original filename
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Processing and indexing: {filename}")
            
            # Step 1: Process PDF
            result = self.processor.process_pdf(file_path, filename)
            
            if not result.success:
                raise DocumentProcessingError(f"Processing failed: {result.error}")
            
            # Step 2: Generate embeddings for text elements
            text_elements = [
                elem for elem in result.elements 
                if elem.content_type.value == "text"
            ]
            
            if not text_elements:
                logger.warning(f"No text elements found in {filename}")
                return False
            
            # Chunk text elements
            chunks = []
            payloads = []
            
            for elem in text_elements:
                # Split long content into chunks
                chunk_size = 1000
                content = elem.content
                
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    chunks.append(chunk)
                    
                    payloads.append({
                        "filename": filename,
                        "page_number": elem.page_number,
                        "content_type": "text",
                        "content": chunk,
                        "element_id": elem.element_id
                    })
            
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            embeddings = self.embedding_gen.generate_embeddings_batch(chunks)
            
            # Step 3: Index in Qdrant
            logger.info(f"Indexing {len(embeddings)} vectors in Qdrant...")
            self.vector_store.add_points(embeddings, payloads)
            
            # Store processed result
            self.processed_docs[filename] = result
            
            logger.info(f"✅ Successfully processed and indexed: {filename}")
            return True
        
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to process and index PDF: {str(e)}", sys
            )
    
    def get_processed_filenames(self) -> List[str]:
        """Get list of processed filenames"""
        return list(self.processed_docs.keys())
    
    def delete_document(self, filename: str) -> bool:
        """
        Delete document from vector store
        
        Args:
            filename: Filename to delete
            
        Returns:
            True if successful
        """
        try:
            self.vector_store.delete_by_filename(filename)
            
            if filename in self.processed_docs:
                del self.processed_docs[filename]
            
            logger.info(f"✅ Deleted document: {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}")
            return False
