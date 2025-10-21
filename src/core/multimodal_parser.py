"""
Multimodal Document Processor
Extracts TEXT, IMAGES, and TABLES from PDFs
Uses Google Gemini to describe images and summarize tables
"""
import sys
import os
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import BytesIO
from PIL import Image

from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    Text, Title, NarrativeText, ListItem, Table, Image as UnstructuredImage
)
import google.generativeai as genai

from utils.logger import get_logger
from utils.exception import DocumentProcessingError

logger = get_logger(__name__)


class DocumentElement:
    """Enhanced document element supporting multimodal content"""
    def __init__(
        self,
        content: str,
        content_type: str,  # "text", "image", "table"
        page_number: int,
        metadata: Dict[str, Any],
        image_data: Optional[bytes] = None,
        image_description: Optional[str] = None,
        table_data: Optional[str] = None
    ):
        self.content = content
        self.content_type = content_type
        self.page_number = page_number
        self.metadata = metadata
        self.image_data = image_data
        self.image_description = image_description
        self.table_data = table_data


class ProcessingResult:
    """Processing result"""
    def __init__(self, success: bool, elements: List[DocumentElement], error: str = ""):
        self.success = success
        self.elements = elements
        self.error = error


class MultimodalProcessor:
    """
    Multimodal Document Processor
    
    Handles:
    - Text extraction
    - Image extraction + AI description
    - Table extraction + AI summarization
    """
    
    def __init__(self):
        """Initialize with Google Gemini for multimodal processing"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found - multimodal features disabled")
            self.gemini_available = False
        else:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")
            self.vision_model = genai.GenerativeModel(model_name)
            self.gemini_available = True
            logger.info(f"✅ Multimodal processing enabled with {model_name}")
        
        self.extract_images = os.getenv("EXTRACT_IMAGES", "true").lower() == "true"
        self.extract_tables = os.getenv("EXTRACT_TABLES", "true").lower() == "true"
        
        logger.info(f"Images: {self.extract_images}, Tables: {self.extract_tables}")
    
    def describe_image_with_gemini(self, image_bytes: bytes) -> str:
        """Use Gemini to describe an image"""
        if not self.gemini_available:
            return "Image description unavailable (no Gemini API key)"
        
        try:
            logger.info("Describing image with Gemini...")
            
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_bytes))
            
            # Ask Gemini to describe
            response = self.vision_model.generate_content([
                "Describe this image in detail. Focus on:",
                "- What is shown in the image",
                "- Any text visible in the image",
                "- Key data points or information",
                "- Context and significance",
                "Provide a clear, detailed description.",
                image
            ])
            
            description = response.text
            logger.info(f"✅ Generated description: {len(description)} chars")
            return description
        
        except Exception as e:
            logger.error(f"Image description failed: {str(e)}")
            return f"Image description failed: {str(e)}"
    
    def summarize_table_with_gemini(self, table_text: str) -> str:
        """Use Gemini to summarize a table"""
        if not self.gemini_available:
            return table_text  # Return raw table
        
        try:
            logger.info("Summarizing table with Gemini...")
            
            response = self.vision_model.generate_content([
                "Analyze this table and provide:",
                "1. A brief summary of what the table shows",
                "2. Key data points and insights",
                "3. Any important patterns or findings",
                "",
                "Table content:",
                table_text
            ])
            
            summary = response.text
            logger.info(f"✅ Generated table summary: {len(summary)} chars")
            return summary
        
        except Exception as e:
            logger.error(f"Table summarization failed: {str(e)}")
            return table_text  # Return original
    
    def process_pdf(self, file_path: str, filename: str) -> ProcessingResult:
        """
        Process PDF with multimodal support
        
        Extracts:
        - Text elements
        - Images (with AI descriptions)
        - Tables (with AI summaries)
        
        Args:
            file_path: Path to PDF
            filename: Original filename
            
        Returns:
            ProcessingResult with all elements
        """
        doc = None
        try:
            logger.info("=" * 80)
            logger.info(f"MULTIMODAL PROCESSING: {filename}")
            logger.info("=" * 80)
            
            # Check file
            if not os.path.exists(file_path):
                error = f"File not found: {file_path}"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size:,} bytes")
            
            # Use Unstructured to partition PDF
            logger.info("Partitioning PDF with Unstructured...")
            
            try:
                elements_raw = partition_pdf(
                    filename=file_path,
                    strategy="fast",  # High resolution for better image/table extraction
                    infer_table_structure=True,
                    extract_images_in_pdf=self.extract_images,
                    extract_image_block_types=["Image", "Table"] if self.extract_images else []
                )
                
                logger.info(f"✅ Extracted {len(elements_raw)} elements")
            
            except Exception as e:
                error = f"Unstructured partition failed: {str(e)}"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            # Process elements
            doc_elements = []
            stats = {"text": 0, "images": 0, "tables": 0}
            
            for idx, element in enumerate(elements_raw):
                try:
                    element_type = type(element).__name__
                    logger.info(f"Processing element {idx}: {element_type}")
                    
                    # Get metadata
                    metadata = element.metadata.to_dict() if hasattr(element, 'metadata') else {}
                    page_num = metadata.get('page_number', 1)
                    
                    # HANDLE TEXT ELEMENTS
                    if isinstance(element, (Text, Title, NarrativeText, ListItem)):
                        text = str(element).strip()
                        if text and len(text) > 5:
                            doc_element = DocumentElement(
                                content=text,
                                content_type="text",
                                page_number=page_num,
                                metadata={
                                    "filename": filename,
                                    "page": page_num,
                                    "element_type": element_type
                                }
                            )
                            doc_elements.append(doc_element)
                            stats["text"] += 1
                            logger.info(f"✅ Text element: {len(text)} chars")
                    
                    # HANDLE TABLE ELEMENTS
                    elif isinstance(element, Table) and self.extract_tables:
                        table_text = str(element).strip()
                        if table_text:
                            # Get AI summary of table
                            table_summary = self.summarize_table_with_gemini(table_text)
                            
                            doc_element = DocumentElement(
                                content=f"TABLE SUMMARY: {table_summary}\n\nRAW TABLE:\n{table_text}",
                                content_type="table",
                                page_number=page_num,
                                metadata={
                                    "filename": filename,
                                    "page": page_num,
                                    "element_type": "Table"
                                },
                                table_data=table_text
                            )
                            doc_elements.append(doc_element)
                            stats["tables"] += 1
                            logger.info(f"✅ Table element with AI summary")
                    
                    # HANDLE IMAGE ELEMENTS
                    elif isinstance(element, UnstructuredImage) and self.extract_images:
                        # Try to get image data
                        if hasattr(element, 'image'):
                            image_data = element.image
                            
                            # Get AI description of image
                            image_description = self.describe_image_with_gemini(image_data)
                            
                            doc_element = DocumentElement(
                                content=f"IMAGE DESCRIPTION: {image_description}",
                                content_type="image",
                                page_number=page_num,
                                metadata={
                                    "filename": filename,
                                    "page": page_num,
                                    "element_type": "Image"
                                },
                                image_data=image_data,
                                image_description=image_description
                            )
                            doc_elements.append(doc_element)
                            stats["images"] += 1
                            logger.info(f"✅ Image element with AI description")
                
                except Exception as e:
                    logger.warning(f"Error processing element {idx}: {str(e)}")
                    continue
            
            if not doc_elements:
                error = "No content extracted"
                logger.error(error)
                return ProcessingResult(False, [], error)
            
            # Final stats
            total_chars = sum(len(e.content) for e in doc_elements)
            
            logger.info("=" * 80)
            logger.info("✅ MULTIMODAL PROCESSING COMPLETE!")
            logger.info(f"Text elements: {stats['text']}")
            logger.info(f"Image elements: {stats['images']}")
            logger.info(f"Table elements: {stats['tables']}")
            logger.info(f"Total elements: {len(doc_elements)}")
            logger.info(f"Total content: {total_chars:,} chars")
            logger.info("=" * 80)
            
            return ProcessingResult(True, doc_elements, "")
        
        except Exception as e:
            error = f"Processing failed: {str(e)}"
            logger.error(error)
            import traceback
            logger.error(traceback.format_exc())
            return ProcessingResult(False, [], error)
        
        # In PDFService.process_and_index_pdf
        for element in result.elements:
            if element.content_type == "text":
                text = element.content  # Could be very large
                # No memory limit check
