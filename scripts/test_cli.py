#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

# Ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils.logger import get_logger
from services.pdf_service import PDFService
from services.chat_service import ChatService
from services.query_service import QueryService

logger = get_logger(__name__)


def find_default_pdf() -> Path:
    assets_dir = ROOT / "src" / "ui" / "assets" / "documents"
    if assets_dir.exists():
        for p in assets_dir.iterdir():
            if p.suffix.lower() == ".pdf":
                return p
    raise FileNotFoundError("No PDF found in src/ui/assets/documents")


def ensure_index(pdf_path: Path, filename: str) -> None:
    pdf_service = PDFService(upload_dir=str(ROOT / "data" / "uploads"))
    # Upload-like behavior
    file_bytes = pdf_path.read_bytes()
    uploaded_path = pdf_service.upload_pdf(file_bytes, filename)
    ok = pdf_service.process_and_index_pdf(uploaded_path, filename)
    if not ok:
        raise RuntimeError("Processing/indexing failed")


def run_query(filename: str, query: str, provider: str, show_hits: bool, limit: int) -> None:
    chat = ChatService(llm_provider=provider)
    q = QueryService()

    if show_hits:
        results = q.search(query, limit=limit, filename=filename)
        print("\nTop search hits:")
        for i, r in enumerate(results, 1):
            payload = r["payload"]
            snippet = payload.get("content", "").replace("\n", " ")[:160]
            print(f" {i}. p{payload['page_number']} score={r['score']:.3f} :: {snippet}")

    resp = chat.chat(query=query, filename=filename, use_rag=True)
    print("\nAnswer:\n")
    print(resp.answer)
    if resp.sources:
        print("\nSources:")
        for s in resp.sources:
            print(f" - {s['filename']} p{s['page']} score={s['score']:.3f}")


def build_preset(mode: str) -> str:
    if mode == "summary":
        return (
            "Create a comprehensive summary of the document including: "
            "1. Main topics and themes discussed 2. Key findings, arguments, or claims "
            "3. Important data, examples, or evidence presented 4. Main conclusions or recommendations. "
            "Organize with clear headers and bullet points. Cite page numbers."
        )
    if mode == "keypoints":
        return (
            "Extract and list the most important key points from the document. "
            "For each point: state the point, give a brief explanation, and include the page number."
        )
    if mode == "topics":
        return (
            "Identify and describe the main topics covered in this document. "
            "For each topic: name, 2-3 sentence description, key subpoints, page numbers."
        )
    if mode == "details":
        return (
            "Provide detailed information: methodologies, specific data/measurements, technical specs, "
            "examples/applications, formulas/models (if any). Include page references."
        )
    return mode


def main():
    parser = argparse.ArgumentParser(description="iPDF CLI tester")
    parser.add_argument("--pdf", type=str, help="Path to PDF (defaults to first in assets)")
    parser.add_argument("--mode", type=str, default="interactive", choices=[
        "interactive", "summary", "keypoints", "topics", "details"
    ])
    parser.add_argument("--provider", type=str, default="groq", choices=["groq", "google"])
    parser.add_argument("--show-hits", action="store_true", help="Print top search hits before answer")
    parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    pdf_path = Path(args.pdf) if args.pdf else find_default_pdf()
    filename = pdf_path.name

    print(f"Using PDF: {pdf_path}")
    ensure_index(pdf_path, filename)

    if args.mode == "interactive":
        print("\nType your questions (Ctrl+C to exit)\n")
        while True:
            try:
                q = input("?> ").strip()
                if not q:
                    continue
                run_query(filename, q, args.provider, args.show_hits, args.limit)
            except KeyboardInterrupt:
                print("\nBye!")
                break
    else:
        query = build_preset(args.mode)
        run_query(filename, query, args.provider, args.show_hits, args.limit)


if __name__ == "__main__":
    main()
