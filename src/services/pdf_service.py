"""
PDF Service - Multimodal Support
"""
import sys
from pathlib import Path
import hashlib

from utils.logger import get_logger
from utils.helpers import ensure_dir
from core.multimodal_processor import MultimodalProcessor
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager

logger = get_logger(__name__)


class PDFService:
    """PDF service with multimodal support"""
    
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        ensure_dir(self.upload_dir)
        
        self.processor = MultimodalProcessor()
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        
        logger.info("PDFService initialized (multimodal mode)")
    
    def upload_pdf(self, file_bytes: bytes, filename: str) -> str:
        """Upload PDF"""
        try:
            file_hash = hashlib.md5(file_bytes).hexdigest()[:8]
            safe_filename = f"{file_hash}_{filename}"
            file_path = self.upload_dir / safe_filename
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            logger.info(f"Uploaded: {filename}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise
    
    def process_and_index_pdf(self, file_path: str, filename: str) -> bool:
        """Process PDF with multimodal support"""
        try:
            logger.info(f"Processing: {filename}")
            
            # Process with multimodal processor
            result = self.processor.process_pdf(file_path, filename)
            
            if not result.success:
                logger.error(f"Processing failed: {result.error}")
                return False
            
            # Create chunks
            chunks = []
            payloads = []
            
            for element in result.elements:
                content = element.content
                
                # Split into chunks
                chunk_size = 800
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size].strip()
                    if chunk:
                        chunks.append(chunk)
                        payloads.append({
                            "filename": filename,
                            "page_number": element.page_number,
                            "content_type": element.content_type,  # "text", "image", "table"
                            "content": chunk
                        })
            
            if not chunks:
                logger.error("No chunks created")
                return False
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Generate embeddings
            embeddings = self.embedding_gen.generate_embeddings_batch(chunks)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Index
            self.vector_store.add_points(embeddings, payloads)
            logger.info(f"✅ Indexed {len(embeddings)} vectors")
            
            return True
        
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False
