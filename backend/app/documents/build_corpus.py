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
            seen_ids: dict[str, int] = {}
            for i, c in enumerate(chunks):
                base_id = f"{meta['circular_ref']}::{c['para_no'] or i}"
                # Same para_no kabhi kabhi ek document me dobara aata hai (jaise
                # end me "repealed circulars" ki annex table, jisme numbering
                # phir se 1, 2, 3... se shuru hoti hai) - asli clause wala
                # PEHLA occurrence apna clean id rakhta hai, baad wale
                # occurrences ko unique suffix milta hai taaki Chroma me
                # DuplicateIDError na aaye.
                if base_id in seen_ids:
                    seen_ids[base_id] += 1
                    chunk_id = f"{base_id}-dup{seen_ids[base_id]}"
                else:
                    seen_ids[base_id] = 0
                    chunk_id = base_id
                record = {
                    "chunk_id": chunk_id,
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
