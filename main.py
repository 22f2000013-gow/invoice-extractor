import os
import json
import re
from fastapi import FastAPI
from pydantic import BaseModel, field_validator
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

class InvoiceRequest(BaseModel):
    text: str = ""

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v):
        return v.upper()

@app.post("/extract", response_model=InvoiceResponse)
def extract_invoice(request: InvoiceRequest):
    text = (request.text or "").strip()

    if not text:
        return InvoiceResponse(vendor="Unknown", amount=0.0, currency="USD", date="1970-01-01")

    prompt = f"""Extract invoice details from the text below.
Return ONLY a JSON object with exactly these keys:
- vendor: the vendor/company name as a string
- amount: the total amount due as a number (no currency symbol)
- currency: 3-letter uppercase currency code (e.g. USD, EUR, GBP)
- date: the payment due date in YYYY-MM-DD format

Invoice text:
{text}

Respond with ONLY the JSON object, no explanation, no markdown, no backticks."""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"```[a-z]*", "", raw).strip("` \n")
        data = json.loads(raw)

        return InvoiceResponse(
            vendor=str(data.get("vendor", "Unknown")),
            amount=float(data.get("amount", 0.0)),
            currency=str(data.get("currency", "USD")).upper(),
            date=str(data.get("date", "1970-01-01"))
        )
    except Exception:
        return InvoiceResponse(vendor="Unknown", amount=0.0, currency="USD", date="1970-01-01")
