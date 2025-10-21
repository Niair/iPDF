"""
Multimodal Document Extractor - PyMuPDF Based with Resource Management
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
        content_type: str,
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
    """Extract text + images with proper resource management"""
    
    # Class constants
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
    MAX_PAGES = 500  # Maximum pages to process
    
    def __init__(self):
        logger.info("MultimodalExtractor initialized (PyMuPDF + Resource Management)")
    
    def process_pdf(self, file_path: str, filename: str) -> ProcessingResult:
        """
        Extract text and page images with proper error handling
        
        Returns:
            ProcessingResult with text and image elements
        """
        doc = None
        
        try:
            logger.info("="*60)
            logger.info(f"MULTIMODAL PROCESSING: {filename}")
            logger.info("="*60)
            
            # VALIDATION
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            if file_size == 0:
                raise ValueError("File is empty (0 bytes)")
            
            if file_size > self.MAX_FILE_SIZE:
                raise ValueError(
                    f"File size {file_size/1024/1024:.1f}MB exceeds limit of "
                    f"{self.MAX_FILE_SIZE/1024/1024:.1f}MB"
                )
            
            # OPEN PDF
            try:
                doc = fitz.open(file_path)
            except Exception as e:
                raise DocumentProcessingError(f"Cannot open PDF: {str(e)}")
            
            page_count = len(doc)
            logger.info(f"PDF has {page_count} pages")
            
            if page_count == 0:
                raise ValueError("PDF has 0 pages")
            
            if page_count > self.MAX_PAGES:
                logger.warning(f"PDF has {page_count} pages, limiting to {self.MAX_PAGES}")
                page_count = self.MAX_PAGES
            
            elements = []
            
            # PROCESS EACH PAGE
            for page_num in range(page_count):
                logger.info(f"Processing page {page_num + 1}/{page_count}...")
                
                try:
                    page = doc[page_num]
                    
                    # Extract TEXT
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
                    
                    # Extract IMAGE
                    try:
                        mat = fitz.Matrix(2, 2)  # 2x zoom
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        
                        # Convert to PIL and optimize
                        image = Image.open(BytesIO(img_data))
                        
                        # Compress if too large
                        buffered = BytesIO()
                        image.save(buffered, format="PNG", optimize=True, quality=85)
                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        
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
                        logger.info(f"  ✅ Image: {len(img_base64):,} bytes")
                        
                    except Exception as e:
                        logger.warning(f"  ⚠️ Image extraction failed: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Failed to process page {page_num + 1}: {str(e)}")
                    continue
            
            if not elements:
                raise DocumentProcessingError("No content extracted from any page")
            
            # STATS
            text_count = sum(1 for e in elements if e.content_type == "text")
            image_count = sum(1 for e in elements if e.content_type == "image")
            
            logger.info("="*60)
            logger.info("✅ EXTRACTION COMPLETE!")
            logger.info(f"Text elements: {text_count}")
            logger.info(f"Image elements: {image_count}")
            logger.info(f"Total elements: {len(elements)}")
            logger.info("="*60)
            
            return ProcessingResult(True, elements, "")
            
        except FileNotFoundError as e:
            logger.error(f"File error: {str(e)}")
            return ProcessingResult(False, [], f"File error: {str(e)}")
        
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return ProcessingResult(False, [], f"Validation error: {str(e)}")
        
        except DocumentProcessingError as e:
            logger.error(f"Processing error: {str(e)}")
            return ProcessingResult(False, [], str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return ProcessingResult(False, [], f"Unexpected error: {str(e)}")
        
        finally:
            # CLEANUP RESOURCES
            if doc:
                try:
                    doc.close()
                    logger.info("PDF document closed")
                except:
                    pass
