"""
Pura document pipeline: sab PDFs -> parse -> chunk -> metadata attach -> JSONL.

Important concept: ye pipeline ka "runner" hai. Iska output
(data/processed/chunks.jsonl) hi Phase 3 me embed karke vector DB me jaayega —
is se pehle koi retrieval nahi ho sakti.
"""

import json
from pathlib import Path

from chunker import chunk_by_paragraph
from metadata import get_metadata
from parser import extract_text

CIRCULARS_DIR = Path(__file__).resolve().parents[3] / "data" / "circulars"
OUTPUT_PATH = Path(__file__).resolve().parents[3] / "data" / "processed" / "chunks.jsonl"


def build():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        for pdf_path in sorted(CIRCULARS_DIR.glob("*.pdf")):
            meta = get_metadata(pdf_path.name)
            text = extract_text(str(pdf_path))
            chunks = chunk_by_paragraph(text)
            for i, c in enumerate(chunks):
                record = {
                    "chunk_id": f"{meta['circular_ref']}::{c['para_no'] or i}",
                    **meta,
                    "chapter": c["chapter"],
                    "para_no": c["para_no"],
                    "heading": c["heading"],
                    "text": c["text"],
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                total += 1
            print(f"{pdf_path.name}: {len(chunks)} chunks")
    print(f"\nTotal: {total} chunks -> {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
