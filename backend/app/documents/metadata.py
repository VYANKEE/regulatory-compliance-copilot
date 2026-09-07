"""
Circular-level metadata.

Important concept: chunk-level metadata (circular number, date, whether it's
superseded) is what lets the Diff/Impact agents later filter and compare —
without this, retrieval can only match on text similarity, never on
"give me the CURRENT operative rule" vs "what did the OLD rule say".
"""

CIRCULAR_METADATA = {
    "2020_notification_258.pdf": {
        "circular_ref": "RBI/2019-20/258",
        "title": "Loans Sourced by Banks and NBFCs over Digital Lending Platforms",
        "date": "2020-06-24",
        "status": "repealed",
        "superseded_by": "RBI/2025-26/36",
    },
    "2022_guidelines_digital_lending.pdf": {
        "circular_ref": "RBI/2022-23/111",
        "title": "Guidelines on Digital Lending",
        "date": "2022-09-02",
        "status": "repealed",
        "superseded_by": "RBI/2025-26/36",
    },
    "2023_dlg_guidelines.pdf": {
        "circular_ref": "RBI/2023-24/41",
        "title": "Guidelines on Default Loss Guarantee (DLG) in Digital Lending",
        "date": "2023-06-08",
        "status": "repealed",
        "superseded_by": "RBI/2025-26/36",
    },
    "2025_directions.pdf": {
        "circular_ref": "RBI/2025-26/36",
        "title": "RBI (Digital Lending) Directions, 2025",
        "date": "2025-05-08",
        "status": "current",
        "superseded_by": None,
    },
}


def get_metadata(filename: str) -> dict:
    return CIRCULAR_METADATA[filename]
