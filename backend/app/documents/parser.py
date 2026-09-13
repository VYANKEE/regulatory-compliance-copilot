"""
PDF -> raw text extraction. Uses pdfplumber's layout-aware extraction
(handles tables/multi-column layouts) rather than a naive text dump. A
scanned-image PDF with no real text layer returns near-nothing -- that's
a signal this file needs OCR, not a parsing bug.
"""

import pdfplumber


def extract_text(pdf_path: str) -> str:
    """Extracts the full PDF text as one string, with page breaks."""
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
