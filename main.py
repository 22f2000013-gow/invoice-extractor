from fastapi import FastAPI
from pydantic import BaseModel
import re

app = FastAPI()


# ---------- Request Model ----------
class InvoiceRequest(BaseModel):
    text: str


# ---------- Response Model ----------
class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResponse)
def extract_invoice(data: InvoiceRequest):
    text = data.text.strip()

    # Handle empty input
    if not text:
        return InvoiceResponse(
            vendor="",
            amount=0.0,
            currency="",
            date=""
        )

    # ---------------- Vendor ----------------
    vendor = ""

    # Common pattern: "Invoice from <vendor>"
    m = re.search(
        r"Invoice\s+from\s+(.+?)(?:\.|,|\n|Total|Amount|Due|Payment|Date|$)",
        text,
        re.IGNORECASE,
    )
    if m:
        vendor = m.group(1).strip()

    # Fallback: first non-empty line
    if not vendor:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            vendor = lines[0]

    # ---------------- Currency ----------------
    currency = ""
    m = re.search(r"\b(USD|EUR|GBP)\b", text, re.IGNORECASE)
    if m:
        currency = m.group(1).upper()

    # ---------------- Amount ----------------
    amount = 0.0

    # Currency followed by amount
    m = re.search(
        r"(?:USD|EUR|GBP)\s*[:\-]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        text,
        re.IGNORECASE,
    )

    # Amount followed by currency
    if not m:
        m = re.search(
            r"([0-9]+(?:\.[0-9]{1,2})?)\s*(?:USD|EUR|GBP)",
            text,
            re.IGNORECASE,
        )

    # Total/Amount/Due
    if not m:
        m = re.search(
            r"(?:Total|Amount|Due)[^\d]*([0-9]+(?:\.[0-9]{1,2})?)",
            text,
            re.IGNORECASE,
        )

    if m:
        amount = float(m.group(1))

    # ---------------- Date ----------------
    date = ""
    m = re.search(r"\b(2026-\d{2}-\d{2})\b", text)
    if m:
        date = m.group(1)

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date,
    )
