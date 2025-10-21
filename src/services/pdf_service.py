"""
PDF Service - Multimodal with Memory Management
"""
import sys
from pathlib import Path
import hashlib
from typing import List, Dict, Any  # ← ADD THIS LINE!

from utils.logger import get_logger
from utils.helpers import ensure_dir
from core.multimodal_extractor import MultimodalExtractor
from core.embeddings import EmbeddingGenerator
from core.vectorstore import VectorStoreManager

logger = get_logger(__name__)


class PDFService:
    """PDF service with memory management and chunking"""
    
    # Memory limits
    MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10MB per text element
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 150
    
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        ensure_dir(self.upload_dir)
        
        self.extractor = MultimodalExtractor()
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        
        logger.info("PDFService initialized (multimodal + memory management)")
    
    def upload_pdf(self, file_bytes: bytes, filename: str) -> str:
        """Upload PDF file"""
        try:
            file_hash = hashlib.md5(file_bytes).hexdigest()[:8]
            safe_filename = f"{file_hash}_{filename}"
            file_path = self.upload_dir / safe_filename
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            logger.info(f"Uploaded: {filename} → {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise
    
    def _process_text_chunk(
        self,
        text: str,
        page_number: int,
        filename: str,
        chunks: List[str],
        payloads: List[Dict]
    ):
        """Process text with chunking and memory limits"""
        text_size = len(text.encode('utf-8'))
        
        if text_size > self.MAX_TEXT_SIZE:
            logger.warning(f"Text size {text_size:,} bytes exceeds limit, processing in chunks")
        
        # Chunk the text
        for i in range(0, len(text), self.CHUNK_SIZE - self.CHUNK_OVERLAP):
            chunk = text[i:i+self.CHUNK_SIZE].strip()
            
            if len(chunk) > 50:  # Minimum chunk size
                chunks.append(chunk)
                payloads.append({
                    "filename": filename,
                    "page_number": page_number,
                    "content_type": "text",
                    "content": chunk
                })
    
    def process_and_index_pdf(self, file_path: str, filename: str) -> bool:
        """Process PDF with memory-efficient chunking"""
        try:
            logger.info("="*60)
            logger.info(f"PROCESSING & INDEXING: {filename}")
            logger.info("="*60)
            
            # STEP 1: Extract
            logger.info("Step 1: Multimodal extraction...")
            result = self.extractor.process_pdf(file_path, filename)
            
            if not result.success:
                logger.error(f"❌ Extraction failed: {result.error}")
                return False
            
            logger.info(f"✅ Extracted {len(result.elements)} elements")
            
            # STEP 2: Prepare chunks with memory management
            logger.info("Step 2: Creating chunks (memory-efficient)...")
            chunks = []
            payloads = []
            
            for element in result.elements:
                if element.content_type == "text":
                    # Use helper method for text chunking
                    self._process_text_chunk(
                        element.content,
                        element.page_number,
                        filename,
                        chunks,
                        payloads
                    )
                
                elif element.content_type == "image":
                    # Store searchable image reference
                    chunks.append(
                        f"Page {element.page_number} visual content tables figures charts diagrams from {filename}"
                    )
                    payloads.append({
                        "filename": filename,
                        "page_number": element.page_number,
                        "content_type": "image",
                        "content": element.content,
                        "image_base64": element.image_base64
                    })
            
            if not chunks:
                logger.error("❌ No chunks created")
                return False
            
            logger.info(f"✅ Created {len(chunks)} chunks")
            
            # STEP 3: Generate embeddings (optimized batching)
            logger.info("Step 3: Generating embeddings (batched)...")
            embeddings = self.embedding_gen.generate_embeddings_batch(
                chunks,
                batch_size=32,
                show_progress=True
            )
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            
            # STEP 4: Index
            logger.info("Step 4: Indexing in Qdrant...")
            self.vector_store.add_multimodal_points(embeddings, payloads)
            logger.info(f"✅ Indexed {len(embeddings)} vectors")
            
            logger.info("="*60)
            logger.info(f"✅ SUCCESS: {filename} fully processed!")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
