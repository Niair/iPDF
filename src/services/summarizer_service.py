# src/services/summarizer_service.py
import concurrent.futures
from src.services.llm_manager import get_llm
from src.config.logger import logger
from src.config.exception import CustomException
import os
from typing import Dict

def _build_summary_prompt(filename: str, text_content: str):
    trimmed = text_content[:12000]
    prompt = f"""
Create a comprehensive academic summary for "{filename}" in well-structured markdown format:

## Document Information
**File Name:** {filename}

## Title
[The title of the document]

## Authors & Affiliations
[List authors with affiliations]

## Abstract
[A concise abstract of the document]

## Key Contributions
[Bullet points of the main contributions]

## Methodology Highlights
[Detailed description of methods]

## Main Findings
[Detailed findings with quantitative results]

## References
[List at least 5 key references found in the document]

## Additional Notes
[Datasets, limitations, future work]

Preserve technical terms, formulas, and important notations.

Content:
{trimmed}
"""
    return prompt

def _generate_for_file(args):
    filename, text, use_ollama = args
    try:
        llm = get_llm(use_ollama=use_ollama)
        prompt = _build_summary_prompt(filename, text)
        resp = llm.invoke(prompt)
        # ChatGroq or Ollama returns with .content sometimes; handle both
        content = getattr(resp, "content", None) or getattr(resp, "text", None) or str(resp)
        return content.strip()
    except Exception as e:
        logger.exception(f"Failed summarizing {filename}")
        return f"### Summary for {filename} failed\nError: {e}"

def generate_summaries(raw_texts: Dict[str, str], use_ollama: bool = False) -> str:
    all_summaries = []
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(_generate_for_file, (fn, txt, use_ollama)): fn for fn, txt in raw_texts.items()}
            for future in concurrent.futures.as_completed(futures):
                filename = futures[future]
                try:
                    all_summaries.append(future.result())
                except Exception as e:
                    logger.exception(f"Summary generation error for {filename}")
                    all_summaries.append(f"### Summary for {filename} failed\nError: {e}")
        return "\n\n---\n\n".join(all_summaries)
    except Exception as e:
        logger.exception("generate_summaries failure")
        raise CustomException(e, __import__("sys"))
