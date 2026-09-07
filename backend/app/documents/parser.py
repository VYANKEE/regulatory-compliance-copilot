"""
PDF -> raw text extraction.

Important concept: layout-aware extraction. pdfplumber reads the PDF's actual
text layout (columns, spacing) instead of just dumping the raw text stream like
a naive parser would — this matters for regulatory PDFs that have tables and
multi-column layouts (e.g. the DLG cap illustration table). If a PDF is a
scanned image (no real text layer), extract_text() returns close to nothing —
that's the signal we need OCR for that file, not a parsing bug.
"""

import pdfplumber


def extract_text(pdf_path: str) -> str:
    """Pura PDF text nikaal ke ek string return karta hai, page breaks ke saath."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n".join(pages)


if __name__ == "__main__":
    import sys

    text = extract_text(sys.argv[1])
    print(text[:2000])
    print(f"\n\nTotal characters: {len(text)}")
