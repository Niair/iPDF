# src/utils/pdf_extractor.py
import os
import re
import concurrent.futures
import time
from typing import Dict, List
from io import BytesIO
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
from src.config.logger import logger
from src.config.exception import CustomException

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", pytesseract.pytesseract.tesseract_cmd)

def get_single_pdf_text(pdf_bytes: bytes, filename: str, enable_ocr: bool = True) -> str:
    text = ""
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf_reader:
            first_page = pdf_reader.pages[0] if pdf_reader.pages else None
            metadata = first_page.extract_text()[:1000] if first_page and first_page.extract_text() else ""
            pages = pdf_reader.pages
            for page in pages:
                try:
                    page_text = page.extract_text() or ""
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            table_text = "\n".join(["\t".join(cell or "" for cell in row) for row in table])
                            text += f"\n[Table]\n{table_text}\n[/Table]\n"
                    page_text = re.sub(r'(\w+)\s*=\s*([^\.\n]+)', r'\1 = \2 [FORMULA]', page_text)
                    text += page_text + "\n"
                except Exception:
                    logger.exception(f"Error extracting page from {filename}")
            if metadata:
                text = f"[METADATA_START]\n{metadata}\n[METADATA_END]\n" + text
    except Exception as e:
        logger.warning(f"pdfplumber failed for {filename}: {e}")

    if not text.strip() and enable_ocr:
        try:
            images = convert_from_bytes(pdf_bytes, dpi=100)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                ocr_results = list(executor.map(pytesseract.image_to_string, images))
            text = "\n".join(ocr_results)
        except Exception as ocr_error:
            logger.exception(f"OCR fallback failed for {filename}: {ocr_error}")

    return text

def get_pdf_text(pdf_files: List[BytesIO], enable_ocr: bool = True) -> Dict[str, str]:
    texts = {}
    empty_files = []
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {}
        for pdf in pdf_files:
            content = pdf.getvalue()
            futures[executor.submit(get_single_pdf_text, content, pdf.name, enable_ocr)] = pdf.name

        progress_bar = None
        try:
            progress_bar = None
            total = len(futures)
            i = 0
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    texts[name] = result
                    if not result.strip():
                        empty_files.append(name)
                except Exception as e:
                    logger.exception(f"Error processing {name}")
                    texts[name] = ""
                    empty_files.append(name)
                i += 1
        finally:
            elapsed = time.time() - start_time
            logger.info(f"Processed {len(pdf_files)} PDFs in {elapsed:.1f}s")
    if empty_files:
        logger.warning(f"No text extracted from: {', '.join(empty_files)}")
    return texts
