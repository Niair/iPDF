# Code Corrections and Improvements

This document outlines potential issues found in the codebase and suggests improvements for better performance, reliability, and error handling.

## 1. Memory Management in PDF Service
**File**: `src/services/pdf_service.py`

**Issue**: Unbounded memory usage during document processing

**Current Code**:
```python
def process_and_index_pdf(self, file_path: str, filename: str) -> bool:
    # ...
    for element in result.elements:
        if element.content_type == "text":
            text = element.content  # Potential memory issue
```

**Suggested Improvement**:
```python
def process_and_index_pdf(self, file_path: str, filename: str) -> bool:
    MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10MB limit
    
    for element in result.elements:
        if element.content_type == "text":
            text_size = len(element.content.encode('utf-8'))
            if text_size > MAX_TEXT_SIZE:
                logger.warning(f"Text size {text_size} exceeds limit, processing in chunks")
                for chunk in self._process_large_text(element.content, MAX_TEXT_SIZE):
                    # Process chunk
                    self._process_text_chunk(chunk, element.page_number)
            else:
                self._process_text_chunk(element.content, element.page_number)
```

**Benefits**:
- Prevents memory exhaustion
- Handles large documents efficiently
- Better resource management

---

## 2. Embedding Generation Optimization
**File**: `src/core/embeddings.py`

**Issue**: Non-optimized batch processing for embeddings

**Current Code**:
```python
def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
    embeddings = self.model.encode(texts)  # Can overwhelm memory
```

**Suggested Improvement**:
```python
def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
    all_embeddings = []
    total = len(texts)
    
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        try:
            batch_embeddings = self.model.encode(batch)
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Processed {min(i + batch_size, total)}/{total} embeddings")
        except Exception as e:
            logger.error(f"Failed to process batch {i//batch_size}: {str(e)}")
            raise EmbeddingError(f"Batch processing failed at {i}: {str(e)}")
    
    return all_embeddings
```

**Benefits**:
- Controlled memory usage
- Better progress tracking
- Proper error handling per batch
- More reliable processing of large datasets

---

## 3. PDF Processing Error Handling
**File**: `src/core/multimodal_parser.py`

**Issue**: Generic error handling and missing resource cleanup

**Current Code**:
```python
def process_pdf(self, file_path: str, filename: str) -> ProcessingResult:
    try:
        elements_raw = partition_pdf(...)
    except Exception as e:
        error = f"Unstructured partition failed: {str(e)}"
```

**Suggested Improvement**:
```python
def process_pdf(self, file_path: str, filename: str) -> ProcessingResult:
    doc = None
    try:
        # Validate file first
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
            
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File size {file_size} exceeds limit of {self.MAX_FILE_SIZE}")
            
        doc = fitz.open(file_path)
        elements_raw = partition_pdf(
            filename=file_path,
            strategy="fast",
            infer_table_structure=True,
            extract_images_in_pdf=self.extract_images
        )
        # Process elements...
        
    except FileNotFoundError as e:
        return ProcessingResult(False, [], f"File error: {str(e)}")
    except ValueError as e:
        return ProcessingResult(False, [], f"Validation error: {str(e)}")
    except Exception as e:
        return ProcessingResult(False, [], f"Processing error: {str(e)}")
    finally:
        if doc:
            doc.close()
```

**Benefits**:
- Proper resource cleanup
- Specific error handling
- Better error messages
- Input validation
- Resource management

---

## 4. Query Service Relevance Filtering
**File**: `src/services/query_service.py`

**Issue**: Missing relevance score filtering in retriever

**Current Code**:
```python
def get_context_for_query(self, query: str, limit: int = 5) -> str:
    # Missing relevance threshold
```

**Suggested Improvement**:
```python
def get_context_for_query(
    self, 
    query: str, 
    limit: int = 5,
    min_score: float = 0.7
) -> Tuple[str, List[Dict]]:
    try:
        results = self.vector_store.similarity_search_with_score(
            query,
            k=limit,
            score_threshold=min_score
        )
        
        filtered_results = [
            r for r, score in results 
            if score >= min_score
        ]
        
        if not filtered_results:
            logger.warning(f"No results above threshold {min_score}")
            return "", []
            
        context = self._build_context(filtered_results)
        return context, filtered_results
            
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise
```

**Benefits**:
- Better quality results
- Relevance filtering
- Proper error handling
- More informative response structure

---

## 5. OCR Processing Improvements
**File**: `src/core/document_processor.py`

**Issue**: Insufficient OCR error handling and quality control

**Current Code**:
```python
def extract_with_ocr(self, file_path: str, filename: str) -> List[DocumentElement]:
    # Missing OCR quality checks
```

**Suggested Improvement**:
```python
def extract_with_ocr(self, file_path: str, filename: str) -> List[DocumentElement]:
    MIN_CONFIDENCE = 60  # Minimum OCR confidence score
    MIN_TEXT_LENGTH = 10  # Minimum extracted text length
    
    elements = []
    try:
        images = convert_from_path(file_path)
        
        for i, image in enumerate(images):
            try:
                # Get OCR data with confidence
                ocr_data = pytesseract.image_to_data(
                    image, 
                    output_type=pytesseract.Output.DICT
                )
                
                # Filter by confidence
                confident_text = [
                    word for word, conf in zip(
                        ocr_data['text'], 
                        ocr_data['conf']
                    ) if conf > MIN_CONFIDENCE
                ]
                
                text = ' '.join(confident_text)
                
                if len(text) >= MIN_TEXT_LENGTH:
                    element = DocumentElement(
                        content=text,
                        content_type="text",
                        page_number=i + 1,
                        metadata={
                            "filename": filename,
                            "page": i + 1,
                            "extraction_method": "OCR",
                            "ocr_confidence": sum(ocr_data['conf'])/len(ocr_data['conf'])
                        }
                    )
                    elements.append(element)
                    logger.info(f"OCR succeeded for page {i+1}")
                else:
                    logger.warning(f"OCR text too short on page {i+1}")
                    
            except Exception as e:
                logger.error(f"OCR failed for page {i+1}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"OCR process failed: {str(e)}")
        raise
        
    return elements
```

**Benefits**:
- Quality control for OCR results
- Confidence scoring
- Better error handling
- Detailed metadata
- Progress tracking
- Graceful failure handling

---

## Implementation Notes

1. All improvements should be implemented with proper testing
2. Changes should be made incrementally to ensure stability
3. Monitor memory usage after implementation
4. Add logging for new error conditions
5. Update documentation to reflect new parameters and behaviors

## Priority Order

1. Memory Management (PDF Service) - Critical for stability
2. OCR Processing Improvements - Important for accuracy
3. Embedding Generation Optimization - Performance impact
4. PDF Processing Error Handling - Reliability improvement
5. Query Service Relevance Filtering - Quality of results improvement