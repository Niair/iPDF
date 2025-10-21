"""
Multimodal Document Extractor - PyMuPDF Based (No poppler needed!)
Extracts Text + Images from PDFs
"""
import sys
import os
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF
from PIL import Image

from utils.logger import get_logger
from utils.exception import DocumentProcessingError

logger = get_logger(__name__)


class MultimodalElement:
    """Element containing text and/or image"""
    def __init__(
        self,
        content: str,
        content_type: str,  # "text", "image", "text_with_image"
        page_number: int,
        metadata: Dict[str, Any],
        image_base64: Optional[str] = None
    ):
        self.content = content
        self.content_type = content_type
        self.page_number = page_number
        self.metadata = metadata
        self.image_base64 = image_base64


class ProcessingResult:
    """Processing result container"""
    def __init__(self, success: bool, elements: List[MultimodalElement], error: str = ""):
        self.success = success
        self.elements = elements
        self.error = error


class MultimodalExtractor:
    """Extract text + images using PyMuPDF"""
    
    def __init__(self):
        logger.info("MultimodalExtractor initialized (PyMuPDF mode)")
    
    def process_pdf(self, file_path: str, filename: str) -> ProcessingResult:
        """
        Extract text and page images from PDF
        
        Returns:
            ProcessingResult with text and image elements
        """
        try:
            logger.info("="*60)
            logger.info(f"MULTIMODAL PROCESSING: {filename}")
            logger.info("="*60)
            
            if not os.path.exists(file_path):
                return ProcessingResult(False, [], f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            elements = []
            
            # Open PDF with PyMuPDF
            doc = fitz.open(file_path)
            page_count = len(doc)
            logger.info(f"PDF has {page_count} pages")
            
            if page_count == 0:
                doc.close()
                return ProcessingResult(False, [], "PDF has 0 pages")
            
            # Process each page
            for page_num in range(page_count):
                logger.info(f"Processing page {page_num + 1}/{page_count}...")
                page = doc[page_num]
                
                # 1. Extract TEXT
                text = page.get_text("text").strip()
                
                if text and len(text) > 20:
                    text_element = MultimodalElement(
                        content=text,
                        content_type="text",
                        page_number=page_num + 1,
                        metadata={
                            "filename": filename,
                            "page": page_num + 1,
                            "total_pages": page_count,
                            "has_text": True,
                            "char_count": len(text)
                        }
                    )
                    elements.append(text_element)
                    logger.info(f"  ✅ Text: {len(text)} characters")
                else:
                    logger.warning(f"  ⚠️ No text on page {page_num + 1}")
                
                # 2. Extract IMAGE of the page
                try:
                    # Render page as image (higher DPI = better quality)
                    mat = fitz.Matrix(2, 2)  # 2x zoom = 144 DPI
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PNG bytes
                    img_data = pix.tobytes("png")
                    
                    # Convert to PIL Image
                    image = Image.open(BytesIO(img_data))
                    
                    # Convert to base64
                    buffered = BytesIO()
                    image.save(buffered, format="PNG", optimize=True)
                    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    
                    # Create image element
                    image_element = MultimodalElement(
                        content=f"Visual content from page {page_num + 1} of {filename}",
                        content_type="image",
                        page_number=page_num + 1,
                        metadata={
                            "filename": filename,
                            "page": page_num + 1,
                            "total_pages": page_count,
                            "has_image": True,
                            "image_size": len(img_base64)
                        },
                        image_base64=img_base64
                    )
                    elements.append(image_element)
                    logger.info(f"  ✅ Image: {len(img_base64):,} bytes (base64)")
                    
                except Exception as e:
                    logger.warning(f"  ⚠️ Image extraction failed: {str(e)}")
            
            doc.close()
            logger.info("PDF closed")
            
            if not elements:
                return ProcessingResult(False, [], "No content extracted")
            
            # Stats
            text_count = sum(1 for e in elements if e.content_type == "text")
            image_count = sum(1 for e in elements if e.content_type == "image")
            
            logger.info("="*60)
            logger.info("✅ EXTRACTION COMPLETE!")
            logger.info(f"Text elements: {text_count}")
            logger.info(f"Image elements: {image_count}")
            logger.info(f"Total elements: {len(elements)}")
            logger.info("="*60)
            
            return ProcessingResult(True, elements, "")
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return ProcessingResult(False, [], str(e))
