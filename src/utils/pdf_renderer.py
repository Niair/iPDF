"""
PDF Renderer
Renders PDF pages as images for display in Streamlit
"""
import sys
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
from PIL import Image
import io

from utils.logger import get_logger
from utils.exception import IPDFException

logger = get_logger(__name__)


class PDFRenderer:
    """Render PDF pages as images"""
    
    def __init__(self, dpi: int = 150):
        """
        Initialize PDF renderer
        
        Args:
            dpi: Resolution for rendering (default: 150)
        """
        self.dpi = dpi
        self.zoom = dpi / 72  # PDF default DPI is 72
        logger.info(f"PDFRenderer initialized with DPI: {dpi}")
    
    def render_page(self, pdf_path: str, page_number: int) -> Optional[Image.Image]:
        """
        Render a single page as PIL Image
        
        Args:
            pdf_path: Path to PDF file
            page_number: Page number (0-indexed)
            
        Returns:
            PIL Image or None if error
        """
        try:
            doc = fitz.open(pdf_path)
            
            if page_number < 0 or page_number >= len(doc):
                logger.error(f"Invalid page number: {page_number}")
                return None
            
            page = doc[page_number]
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            doc.close()
            return img
        
        except Exception as e:
            logger.error(f"Error rendering page {page_number}: {str(e)}")
            return None
    
    def render_all_pages(self, pdf_path: str) -> List[Image.Image]:
        """
        Render all pages as PIL Images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PIL Images
        """
        try:
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                mat = fitz.Matrix(self.zoom, self.zoom)
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                images.append(img)
            
            doc.close()
            logger.info(f"Rendered {len(images)} pages from {pdf_path}")
            return images
        
        except Exception as e:
            raise IPDFException(f"Error rendering PDF: {str(e)}", sys)
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get total number of pages in PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of pages
        """
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Error getting page count: {str(e)}")
            return 0
