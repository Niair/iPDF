"""
Document Processor - With OCR Fallback
Works for BOTH regular PDFs AND scanned PDFs!
"""
import sys
import os
from typing import List, Dict, Any
import fitz  # PyMuPDF

from utils.logger import get_logger
from utils.exception import DocumentProcessingError

logger = get_logger(__name__)


class DocumentElement:
    """Document element"""
    def __init__(self, content: str, content_type: str, page_number: int, metadata: Dict[str, Any]):
        self.content = content
        self.content_type = content_type
        self.page_number = page_number
        self.metadata = metadata


class ProcessingResult:
    """Processing result"""
    def __init__(self, success: bool, elements: List[DocumentElement], error: str = ""):
        self.success = success
        self.elements = elements
        self.error = error


class DocumentProcessor:
    """Document processor with OCR fallback for scanned PDFs"""
    
    def __init__(self):
        self.ocr_available = False
        
        # Check if OCR dependencies are available
        try:
            import pytesseract
            from pdf2image import convert_from_path
            from PIL import Image
            
            # Try to run tesseract
            pytesseract.get_tesseract_version()
            self.ocr_available = True
            logger.info("✅ OCR available (pytesseract + Tesseract)")
        except Exception as e:
            logger.warning(f"⚠️ OCR not available: {str(e)}")
            logger.warning("Install: pip install pytesseract pdf2image + tesseract-ocr")
        
        logger.info(f"DocumentProcessor initialized (OCR: {self.ocr_available})")
    
    def extract_with_ocr(self, file_path: str, filename: str) -> List[DocumentElement]:
        """Extract text using OCR (for scanned PDFs)"""
        try:
            import pytesseract
            from pdf2image import convert_from_path
            from PIL import Image
            
            logger.info("🔍 Using OCR to extract text from scanned PDF...")
            
            # Convert PDF pages to images
            logger.info("Converting PDF pages to images...")
            images = convert_from_path(file_path, dpi=300)
            logger.info(f"✅ Converted {len(images)} pages to images")
            
            elements = []
            
            for i, image in enumerate(images):
                try:
                    logger.info(f"OCR processing page {i + 1}/{len(images)}...")
                    
                    # Extract text using Tesseract
                    text = pytesseract.image_to_string(image, lang='eng')
                    
                    # Clean text
                    text = text.strip()
                    
                    # Remove hyphenation at line breaks
                    text = text.replace('-\n', '')
                    
                    if text and len(text) >= 10:
                        element = DocumentElement(
                            content=text,
                            content_type="text",
                            page_number=i + 1,
                            metadata={
                                "filename": filename,
                                "page": i + 1,
                                "total_pages": len(images),
                                "extraction_method": "OCR",
                                "char_count": len(text)
                            }
                        )
                        elements.append(element)
                        logger.info(f"✅ Page {i + 1}: Extracted {len(text)} characters via OCR")
                    else:
                        logger.warning(f"⚠️ Page {i + 1}: No text found via OCR")
                
                except Exception as e:
                    logger.error(f"OCR failed on page {i + 1}: {str(e)}")
                    continue
            
            return elements
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def process_pdf(self, file_path: str, filename: str) -> ProcessingResult:
        """
        Process PDF with automatic fallback to OCR for scanned PDFs
        
        Args:
            file_path: Path to PDF file
            filename: Original filename
            
        Returns:
            ProcessingResult with extracted text
        """
        elements = []
        
        try:
            logger.info("=" * 60)
            logger.info(f"Processing PDF: {filename}")
            logger.info("=" * 60)
            
            # Check file exists
            if not os.path.exists(file_path):
                error = f"File not found: {file_path}"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            # Check file size
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            if file_size == 0:
                error = "File is empty (0 bytes)"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            # Open PDF with PyMuPDF
            try:
                logger.info("Opening PDF with PyMuPDF...")
                doc = fitz.open(file_path)
                logger.info(f"✅ PDF opened successfully")
            except Exception as e:
                error = f"Cannot open PDF: {str(e)}"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            # Get page count
            page_count = len(doc)
            logger.info(f"PDF has {page_count} page(s)")
            
            if page_count == 0:
                doc.close()
                error = "PDF has 0 pages"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            # Try to extract text with PyMuPDF first
            logger.info("Attempting text extraction with PyMuPDF...")
            
            for page_num in range(page_count):
                try:
                    page = doc[page_num]
                    text = page.get_text("text").strip()
                    
                    if text and len(text) >= 10:
                        element = DocumentElement(
                            content=text,
                            content_type="text",
                            page_number=page_num + 1,
                            metadata={
                                "filename": filename,
                                "page": page_num + 1,
                                "total_pages": page_count,
                                "extraction_method": "PyMuPDF",
                                "char_count": len(text)
                            }
                        )
                        elements.append(element)
                        logger.info(f"✅ Page {page_num + 1}: {len(text)} chars (PyMuPDF)")
                    else:
                        logger.warning(f"⚠️ Page {page_num + 1}: No text via PyMuPDF")
                
                except Exception as e:
                    logger.error(f"Error on page {page_num + 1}: {str(e)}")
                    continue
            
            doc.close()
            
            # Check if we got any text
            if elements:
                # Success with PyMuPDF
                total_chars = sum(len(e.content) for e in elements)
                logger.info("=" * 60)
                logger.info("✅ SUCCESS (PyMuPDF)")
                logger.info(f"Pages: {len(elements)}/{page_count}")
                logger.info(f"Total characters: {total_chars:,}")
                logger.info("=" * 60)
                return ProcessingResult(True, elements, "")
            
            # No text found - try OCR fallback
            logger.warning("=" * 60)
            logger.warning("⚠️ No text extracted with PyMuPDF")
            logger.warning("This appears to be a SCANNED/IMAGE-BASED PDF")
            logger.warning("=" * 60)
            
            if self.ocr_available:
                logger.info("🔄 Attempting OCR fallback...")
                elements = self.extract_with_ocr(file_path, filename)
                
                if elements:
                    # Success with OCR
                    total_chars = sum(len(e.content) for e in elements)
                    logger.info("=" * 60)
                    logger.info("✅ SUCCESS (OCR)")
                    logger.info(f"Pages: {len(elements)}/{page_count}")
                    logger.info(f"Total characters: {total_chars:,}")
                    logger.info("=" * 60)
                    return ProcessingResult(True, elements, "")
                else:
                    error = "OCR failed to extract text"
                    logger.error(error)
                    return ProcessingResult(False, [], error)
            else:
                error = ("No text extracted. This is a scanned/image-based PDF.\n"
                        "Install OCR: pip install pytesseract pdf2image\n"
                        "And install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
                logger.error(error)
                return ProcessingResult(False, [], error)
        
        except Exception as e:
            error = f"Processing failed: {str(e)}"
            logger.error(error)
            import traceback
            logger.error(traceback.format_exc())
            return ProcessingResult(False, [], error)
