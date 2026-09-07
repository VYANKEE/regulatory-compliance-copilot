"""
Section-aware chunking.

Important concept: chunk on the document's own structure (numbered paragraphs
like "18. Eligibility as DLG provider"), not on a fixed character count. A
fixed-size chunker would happily cut a clause in half between two chunks —
then retrieval returns half a rule and the Diff/Impact agents reason over
incomplete text. TOC lines (dot leaders like "....... 13") are filtered out
so they don't get mistaken for real headings.
"""

import re

HEADING_RE = re.compile(r"^(\d{1,2})\.\s+([A-Z][^\n]{2,90})$")
CHAPTER_RE = re.compile(r"^Chapter\s+([IVXLC]+):\s*(.+)$", re.IGNORECASE)
TOC_LEADER_RE = re.compile(r"\.{5,}")


def chunk_by_paragraph(text: str) -> list[dict]:
    """Text ko numbered-paragraph boundaries pe todta hai. Har chunk: para_no,
    heading, chapter, aur us paragraph ka pura text."""
    chunks = []
    current = None
    chapter = None

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        chap_match = CHAPTER_RE.match(line)
        if chap_match:
            chapter = f"Chapter {chap_match.group(1)}: {chap_match.group(2)}"
            continue
        if TOC_LEADER_RE.search(line):
            continue  # table-of-contents line, real heading nahi hai

        head_match = HEADING_RE.match(line)
        if head_match:
            if current and current["text"]:
                current["text"] = "\n".join(current["text"]).strip()
                chunks.append(current)
            current = {
                "para_no": head_match.group(1),
                "heading": head_match.group(2).strip(),
                "chapter": chapter,
                "text": [line],
            }
        elif current and line:
            current["text"].append(line)

    if current and current["text"]:
        current["text"] = "\n".join(current["text"]).strip()
        chunks.append(current)

    if not chunks:
        # Fallback: is document me numbered headings detect nahi hui — poora
        # text ek hi chunk. Baad me is document-type ke liye alag pattern
        # likhna padega.
        chunks = [{"para_no": None, "heading": None, "chapter": None, "text": text.strip()}]

    return chunks


if __name__ == "__main__":
    import sys

    from parser import extract_text

    result = chunk_by_paragraph(extract_text(sys.argv[1]))
    print(f"Total chunks: {len(result)}")
    for c in result[:3]:
        print(f"\n--- Para {c['para_no']}: {c['heading']} ({c['chapter']}) ---")
        print(c["text"][:200])
