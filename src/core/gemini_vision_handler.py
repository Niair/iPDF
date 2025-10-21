"""
Gemini Vision Handler - Multimodal LLM
Handles both text and images
"""
import sys
import os
import base64
from typing import List, Optional
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

from utils.logger import get_logger
from utils.exception import LLMError

logger = get_logger(__name__)


class GeminiVisionHandler:
    """Google Gemini with Vision capabilities"""
    
    def __init__(self):
        """Initialize Gemini Vision"""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise LLMError("GOOGLE_API_KEY not set in .env")
            
            genai.configure(api_key=api_key)
            
            # Use Gemini 2.0 Flash (supports vision)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            self.model = genai.GenerativeModel(model_name)
            
            logger.info(f"✅ Gemini Vision initialized ({model_name})")
            
        except Exception as e:
            logger.error(f"Gemini Vision init failed: {str(e)}")
            raise LLMError(f"Failed to initialize: {str(e)}")
    
    def generate_with_multimodal_context(
        self,
        query: str,
        text_context: str = "",
        images_base64: List[str] = None
    ) -> str:
        """
        Generate response using text AND images
        
        Args:
            query: User question
            text_context: Text from PDF
            images_base64: List of base64-encoded images
        
        Returns:
            Generated answer
        """
        try:
            import google.generativeai as genai
            from PIL import Image
            
            # Build multimodal prompt
            prompt_parts = []
            
            # System instruction
            system_text = """You are an expert PDF document assistant with vision capabilities.

**Your Powers:**
- Read and analyze text from documents
- SEE and interpret images, diagrams, tables, charts, and figures
- Combine information from BOTH text and visual content
- Understand complex visual elements like:
  • Tables (extract and format data)
  • Figures and diagrams (describe and explain)
  • Charts and graphs (analyze trends)
  • Mathematical equations
  • Architecture diagrams

**Response Guidelines:**
1. **Comprehensive**: Use ALL available information (text + images)
2. **Visual First**: For tables/figures, describe what you SEE in the images
3. **Formatting**: Use clear Markdown (headers, bullets, **bold**, tables)
4. **Citations**: Always mention page numbers
5. **Tables**: Reproduce in markdown format when asked
6. **Synthesis**: Combine information from multiple sources

Be thorough, accurate, and helpful!"""
            
            prompt_parts.append(system_text)
            
            # Add text context
            if text_context and len(text_context.strip()) > 10:
                prompt_parts.append(f"\n**TEXT FROM DOCUMENT:**\n{text_context}\n")
            
            # Add images
            if images_base64:
                prompt_parts.append(f"\n**VISUAL CONTENT ({len(images_base64)} pages):**")
                prompt_parts.append("(See the page images below - they may contain tables, figures, charts, or diagrams)")
                
                for idx, img_b64 in enumerate(images_base64[:10]):  # Max 10 images
                    try:
                        # Decode base64 to PIL Image
                        img_data = base64.b64decode(img_b64)
                        image = Image.open(BytesIO(img_data))
                        
                        # Add to prompt
                        prompt_parts.append(image)
                        logger.info(f"Added image {idx+1}/{len(images_base64)} to prompt")
                        
                    except Exception as e:
                        logger.warning(f"Failed to add image {idx+1}: {str(e)}")
            
            # Add user question
            prompt_parts.append(f"\n**USER QUESTION:**\n{query}\n")
            prompt_parts.append("""
**YOUR TASK:**
Provide a comprehensive answer using BOTH the text and visual content above.
- If the question is about a table/figure, look at the images to find and describe it
- Format tables in markdown if requested
- Use clear headers and structure
- Cite page numbers
- Be thorough and detailed
""")
            
            # Generate response
            num_images = len(images_base64) if images_base64 else 0
            logger.info(f"Generating response with {num_images} images, {len(text_context)} chars of text")
            
            response = self.model.generate_content(prompt_parts)
            
            logger.info(f"✅ Generated {len(response.text)} chars response")
            return response.text
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise LLMError(f"Generation failed: {str(e)}", sys)
    
    def process_pdf(self, pdf_path: str) -> str:
        """
        Process PDF file to extract text and images, then generate response
        """
        from processors.multimodal_processor import MultimodalProcessor
        
        try:
            # Initialize processor
            processor = MultimodalProcessor()
            
            # Process PDF to extract text and images
            logger.info(f"📂 Processing PDF: {pdf_path}")
            elements_raw = processor.partition_pdf(pdf_path)
            
            logger.info(f"✅ Extracted {len(elements_raw['texts'])} text elements and {len(elements_raw['images'])} images")
            
            # Generate response using extracted content
            response = self.generate_with_multimodal_context(
                query="",
                text_context=" ".join(elements_raw["texts"]),
                images_base64=elements_raw["images"]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise LLMError(f"PDF processing failed: {str(e)}", sys)
