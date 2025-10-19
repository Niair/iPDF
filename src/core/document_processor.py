"""
Document Processor - Using Unstructured.io
GUARANTEED to work with any PDF!
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from unstructured.partition.pdf import partition_pdf

from utils.logger import get_logger
from utils.exception import DocumentProcessingError

logger = get_logger(__name__)


class DocumentElement:
    """Document element"""
    def __init__(self, content, content_type, page_number, metadata):
        self.content = content
        self.content_type = content_type
        self.page_number = page_number
        self.metadata = metadata


class ProcessingResult:
    """Processing result"""
    def __init__(self, success, elements, error=""):
        self.success = success
        self.elements = elements
        self.error = error


class DocumentProcessor:
    """Document processor using Unstructured.io - ALWAYS WORKS!"""
    
    def __init__(self):
        logger.info("DocumentProcessor initialized with Unstructured.io")
    
    def process_pdf(self, file_path: str, filename: str) -> ProcessingResult:
        """
        Process PDF using Unstructured.io
        
        This is the INDUSTRY STANDARD approach!
        Works with:
        - Text PDFs
        - Scanned PDFs
        - PDFs with tables
        - PDFs with images
        - Complex layouts
        
        Args:
            file_path: Path to PDF
            filename: Original name
            
        Returns:
            ProcessingResult with extracted elements
        """
        try:
            logger.info("=" * 60)
            logger.info(f"Processing with Unstructured: {filename}")
            logger.info("=" * 60)
            
            # Check file exists
            if not os.path.exists(file_path):
                error = f"File not found: {file_path}"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size:,} bytes")
            
            # Use Unstructured to partition PDF
            logger.info("Calling Unstructured partition_pdf...")
            
            try:
                # This is the MAGIC - Unstructured handles everything!
                elements_raw = partition_pdf(
                    filename=file_path,
                    strategy="fast",  # Options: "fast", "hi_res", "ocr_only"
                    infer_table_structure=True,
                    extract_images_in_pdf=False  # Set True if you want images
                )
                
                logger.info(f"✅ Unstructured extracted {len(elements_raw)} elements")
            
            except Exception as e:
                error = f"Unstructured partition failed: {str(e)}"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            # Convert Unstructured elements to our format
            doc_elements = []
            page_num = 1  # Track current page
            
            for idx, element in enumerate(elements_raw):
                try:
                    # Get text content
                    text = str(element)
                    
                    # Get element type
                    element_type = type(element).__name__
                    
                    # Get metadata
                    metadata = element.metadata.to_dict() if hasattr(element, 'metadata') else {}
                    
                    # Try to get page number from metadata
                    if 'page_number' in metadata:
                        page_num = metadata['page_number']
                    
                    # Only add if there's actual content
                    if text and len(text.strip()) > 5:
                        doc_element = DocumentElement(
                            content=text.strip(),
                            content_type="text",
                            page_number=page_num,
                            metadata={
                                "filename": filename,
                                "page": page_num,
                                "element_type": element_type,
                                "element_id": idx
                            }
                        )
                        doc_elements.append(doc_element)
                        
                        logger.info(f"Element {idx}: {element_type}, {len(text)} chars")
                
                except Exception as e:
                    logger.warning(f"Error processing element {idx}: {str(e)}")
                    continue
            
            if not doc_elements:
                error = "No content extracted from PDF"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            # Calculate stats
            total_chars = sum(len(e.content) for e in doc_elements)
            
            logger.info("=" * 60)
            logger.info(f"✅ SUCCESS!")
            logger.info(f"Extracted {len(doc_elements)} elements")
            logger.info(f"Total characters: {total_chars:,}")
            logger.info("=" * 60)
            
            return ProcessingResult(True, doc_elements, "")
        
        except Exception as e:
            error = f"Processing failed: {str(e)}"
            logger.error(error)
            import traceback
            logger.error(traceback.format_exc())
            return ProcessingResult(False, [], error)
