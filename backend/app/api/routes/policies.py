"""Policy document upload -- the user's internal policy PDF, referenced
later by /analysis/start via `policy_document_id`.

Enforces the size cap by reading chunk-by-chunk with a running size check,
so a client lying about Content-Length still can't exceed the max."""

import io
import uuid
from pathlib import Path

import pdfplumber
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...db import models
from ...db.session import get_db
from ..deps import enforce_rate_limit, get_current_user

router = APIRouter(prefix="/policies", tags=["policies"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB
STORAGE_DIR = Path(__file__).resolve().parents[4] / "data" / "policies"
SAMPLE_POLICY_PATH = STORAGE_DIR / "FinTrust_Digital_Lending_Policy_v2.1.pdf"

# Rule-based (no LLM call -- deterministic, testable) resume-vs-policy
# heuristic. Not perfect document-type classification, but real: it counts
# actual keyword occurrences in the extracted text and compares two signals.
RESUME_KEYWORDS = [
    "curriculum vitae", "career objective", "professional summary",
    "work experience", "employment history", "date of birth",
    "references available upon request", "linkedin.com/in", "github.com/",
    "objective:", "hobbies", "extracurricular",
]
POLICY_KEYWORDS = [
    "policy", "circular", "compliance", "regulatory", "rbi", "sebi",
    "guideline", "effective date", "version", "approved by", "reviewed by",
    "applicable to", "scope of this policy", "annexure", "clause",
]


def _extract_text(content: bytes) -> str:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages[:5])


def _looks_like_resume(text: str) -> bool:
    lower = text.lower()
    resume_hits = sum(1 for kw in RESUME_KEYWORDS if kw in lower)
    policy_hits = sum(1 for kw in POLICY_KEYWORDS if kw in lower)
    return resume_hits >= 2 and resume_hits > policy_hits


@router.get("/sample")
async def download_sample_policy():
    """Serves a real sample policy so anyone can demo the flow without their
    own document. No auth -- nothing sensitive here, and requiring sign-in
    just to download a sample would be needless friction."""
    if not SAMPLE_POLICY_PATH.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample policy not found on server.")
    return FileResponse(SAMPLE_POLICY_PATH, media_type="application/pdf", filename=SAMPLE_POLICY_PATH.name)


@router.post("/upload")
async def upload_policy(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    _rl: None = Depends(enforce_rate_limit),
):
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are accepted.")

    # Read into memory (size-capped) so content can be validated before
    # anything touches disk -- a bad upload never gets written.
    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit.",
            )

    try:
        text = _extract_text(bytes(content))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Couldn't read this file as a PDF -- make sure it's a valid, uncorrupted PDF.",
        )

    if len(text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Couldn't extract readable text from this PDF -- it may be a scanned image with no "
                "selectable text. Upload a text-based policy PDF, or use the sample policy on this page."
            ),
        )
    if _looks_like_resume(text):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "This looks like a resume, not a policy document. Upload your organization's internal "
                "compliance/policy PDF instead, or use the sample policy provided on this page."
            ),
        )

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    dest_name = f"{uuid.uuid4()}_{Path(file.filename or 'policy.pdf').name}"
    dest_path = STORAGE_DIR / dest_name
    dest_path.write_bytes(bytes(content))

    doc = models.PolicyDocument(uploaded_by=user.id, filename=file.filename or "policy.pdf", storage_path=str(dest_path))
    db.add(doc)
    db.add(models.AuditLog(user_id=user.id, action="policy_uploaded", detail=doc.filename))
    db.commit()
    db.refresh(doc)

    return {"policy_document_id": doc.id, "filename": doc.filename}
