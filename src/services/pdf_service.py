"""
PDF Service - Simple Version
"""
import sys
from pathlib import Path
import hashlib

from utils.logger import get_logger
from utils.helpers import ensure_dir
from core.document_processor import DocumentProcessor
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager

logger = get_logger(__name__)


class PDFService:
    """PDF service with simple text extraction"""
    
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        ensure_dir(self.upload_dir)
        
        self.processor = DocumentProcessor()
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        
        logger.info("PDFService initialized (simple mode)")
    
    def upload_pdf(self, file_bytes: bytes, filename: str) -> str:
        """Upload PDF"""
        try:
            file_hash = hashlib.md5(file_bytes).hexdigest()[:8]
            safe_filename = f"{file_hash}_{filename}"
            file_path = self.upload_dir / safe_filename
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            logger.info(f"Uploaded: {filename} -> {file_path}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise
    
    def process_and_index_pdf(self, file_path: str, filename: str) -> bool:
        """Process and index PDF"""
        try:
            logger.info(f"=" * 60)
            logger.info(f"PROCESSING AND INDEXING: {filename}")
            logger.info(f"=" * 60)
            
            # Step 1: Extract text
            logger.info("Step 1: Extracting text from PDF...")
            result = self.processor.process_pdf(file_path, filename)
            
            if not result.success:
                logger.error(f"❌ Text extraction failed: {result.error}")
                return False
            
            if not result.elements:
                logger.error("❌ No content extracted")
                return False
            
            logger.info(f"✅ Extracted text from {len(result.elements)} page(s)")
            
            # Step 2: Create chunks
            logger.info("Step 2: Creating chunks...")
            chunks = []
            payloads = []
            chunk_size = 800
            chunk_overlap = 150
            
            for element in result.elements:
                content = element.content
                
                # Split into overlapping chunks
                for i in range(0, len(content), chunk_size - chunk_overlap):
                    chunk = content[i:i + chunk_size].strip()
                    if chunk and len(chunk) > 50:  # At least 50 chars
                        chunks.append(chunk)
                        payloads.append({
                            "filename": filename,
                            "page_number": element.page_number,
                            "content_type": "text",
                            "content": chunk
                        })
            
            if not chunks:
                logger.error("❌ No chunks created")
                return False
            
            logger.info(f"✅ Created {len(chunks)} chunks")
            
            # Step 3: Generate embeddings
            logger.info("Step 3: Generating embeddings...")
            embeddings = self.embedding_gen.generate_embeddings_batch(chunks)
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            
            # Step 4: Index in vector store
            logger.info("Step 4: Indexing in Qdrant...")
            self.vector_store.add_points(embeddings, payloads)
            logger.info(f"✅ Indexed {len(embeddings)} vectors")
            
            logger.info(f"=" * 60)
            logger.info(f"✅ SUCCESS: {filename} fully processed!")
            logger.info(f"=" * 60)
            
            return True
        
        except Exception as e:
            logger.error(f"=" * 60)
            logger.error(f"❌ ERROR: {str(e)}")
            logger.error(f"=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            return False
