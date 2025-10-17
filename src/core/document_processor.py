"""
Document Processor - Extract content from PDFs
"""
import sys
from typing import List, Dict, Any
import pdfplumber
from pathlib import Path

from utils.logger import get_logger
from utils.exception import DocumentProcessingError
from models.document import ProcessingResult, ContentElement, ContentType
from utils.helpers import get_file_hash

logger = get_logger(__name__)


class DocumentProcessor:
    """Process PDF documents and extract text"""
    
    def __init__(self, enable_ocr: bool = True):
        """
        Initialize document processor
        
        Args:
            enable_ocr: Enable OCR for scanned PDFs
        """
        self.enable_ocr = enable_ocr
        logger.info("DocumentProcessor initialized")
    
    def process_pdf(self, pdf_path: str, filename: str) -> ProcessingResult:
        """
        Process a PDF file
        
        Args:
            pdf_path: Path to PDF file
            filename: Original filename
            
        Returns:
            ProcessingResult with extracted content
        """
        try:
            logger.info(f"Processing PDF: {filename}")
            
            elements = []
            full_text = ""
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text() or ""
                    
                    if page_text.strip():
                        element = ContentElement(
                            element_id=f"{filename}_text_p{page_num}",
                            content_type=ContentType.TEXT,
                            content=page_text,
                            page_number=page_num + 1,
                            metadata={"source": "pdfplumber"}
                        )
                        elements.append(element)
                        full_text += page_text + "\n\n"
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table:
                            # Convert table to markdown
                            table_md = self._table_to_markdown(table)
                            element = ContentElement(
                                element_id=f"{filename}_table_p{page_num}_t{table_idx}",
                                content_type=ContentType.TABLE,
                                content=table_md,
                                page_number=page_num + 1,
                                metadata={
                                    "rows": len(table),
                                    "cols": len(table) if table else 0
                                }
                            )
                            elements.append(element)
            
            # Get file hash
            file_hash = get_file_hash(Path(pdf_path).read_bytes())
            
            result = ProcessingResult(
                filename=filename,
                text=full_text,
                elements=elements,
                metadata={
                    "file_hash": file_hash,
                    "element_count": len(elements)
                },
                success=True
            )
            
            logger.info(f"✅ Processed {filename}: {len(elements)} elements extracted")
            return result
        
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            return ProcessingResult(
                filename=filename,
                text="",
                success=False,
                error=str(e)
            )
    
    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """Convert table to markdown format"""
        if not table:
            return ""
        
        markdown = ""
        
        # Header row
        header = table
        markdown += "| " + " | ".join(str(cell) if cell else "" for cell in header) + " |\n"
        markdown += "|" + " --- |" * len(header) + "\n"
        
        # Data rows
        for row in table[1:]:
            markdown += "| " + " | ".join(str(cell) if cell else "" for cell in row) + " |\n"
        
        return markdown
