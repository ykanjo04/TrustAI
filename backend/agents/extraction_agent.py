"""
Extraction Agent - Parses OCR/PDF text and extracts structured invoice fields.

Uses the local Llama 3 model to understand document structure and extract
key financial fields into a structured JSON format.

The prompt template is MUTABLE - the Reflection Agent can modify it
to improve extraction accuracy across runs.

PRIVACY NOTICE:
All extraction is performed locally via Ollama.
No invoice data leaves the local machine.
"""

from models.schemas import InvoiceData, LineItem
from services.llm_service import generate_json


# ---------- MUTABLE PROMPT TEMPLATE ----------
# This template can be modified by the Reflection Agent to improve accuracy.
# Additional hints and examples are appended dynamically.

BASE_SYSTEM_PROMPT = """You are a precise financial document extraction assistant specialized in UAE invoices and receipts.
Your task is to extract structured data from invoice/receipt text.
You must focus heavily on tax-related data, especially UAE VAT (5%).
Always output valid JSON matching the exact schema provided.
If a field cannot be determined from the text, use null.
For currency, default to "AED" if not explicitly stated.
Be careful with number parsing - remove commas and currency symbols before outputting numeric values."""

BASE_EXTRACTION_PROMPT = """Extract the following fields from this invoice/receipt text and return ONLY a JSON object:

Required JSON schema:
{{
  "invoice_number": "string or null",
  "vendor_name": "string or null",
  "invoice_date": "string in YYYY-MM-DD format or null",
  "currency": "string, default AED",
  "subtotal": number or null (amount before tax),
  "vat_amount": number or null (VAT/tax amount),
  "total": number or null (total including tax),
  "items": [
    {{
      "description": "string",
      "quantity": number or null,
      "unit_price": number or null,
      "amount": number or null
    }}
  ],
  "vendor_trn": "string or null (Tax Registration Number)"
}}

Important extraction rules:
- UAE VAT rate is 5%. If you see a tax line, it's likely 5% VAT.
- Look for TRN (Tax Registration Number) patterns like "TRN: 100XXXXXXXXX"
- Dates may be in DD/MM/YYYY format (common in UAE) - convert to YYYY-MM-DD
- Subtotal is the amount BEFORE tax/VAT
- Total is the amount AFTER tax/VAT (subtotal + VAT)
- If only total and VAT are visible, calculate subtotal = total - vat
- If only total and subtotal are visible, calculate vat = total - subtotal

--- INVOICE TEXT START ---
{ocr_text}
--- INVOICE TEXT END ---

{additional_hints}

Return ONLY the JSON object, no explanation or markdown."""


class ExtractionAgent:
    """
    Agent responsible for extracting structured invoice data from raw text.
    """

    def __init__(self):
        self.system_prompt = BASE_SYSTEM_PROMPT
        self.extraction_prompt_template = BASE_EXTRACTION_PROMPT
        self.additional_hints = ""  # Modified by Reflection Agent
        self.extraction_count = 0

    async def extract(self, ocr_text: str) -> InvoiceData:
        """
        Extract structured invoice data from OCR text.
        
        Args:
            ocr_text: Raw text extracted from invoice image/PDF.
            
        Returns:
            InvoiceData with extracted fields.
        """
        self.extraction_count += 1

        # Build prompt with current template and any reflection hints
        prompt = self.extraction_prompt_template.format(
            ocr_text=ocr_text,
            additional_hints=self.additional_hints
        )

        # Get structured response from LLM
        result = await generate_json(prompt, self.system_prompt)

        # Parse into InvoiceData model
        return self._parse_result(result)

    def _parse_result(self, raw: dict) -> InvoiceData:
        """Parse LLM JSON output into InvoiceData model with error handling."""
        items = []
        raw_items = raw.get("items", [])
        if isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    items.append(LineItem(
                        description=str(item.get("description", "")),
                        quantity=_safe_float(item.get("quantity")),
                        unit_price=_safe_float(item.get("unit_price")),
                        amount=_safe_float(item.get("amount")),
                    ))

        return InvoiceData(
            invoice_number=raw.get("invoice_number"),
            vendor_name=raw.get("vendor_name"),
            invoice_date=raw.get("invoice_date"),
            currency=raw.get("currency", "AED") or "AED",
            subtotal=_safe_float(raw.get("subtotal")),
            vat_amount=_safe_float(raw.get("vat_amount")),
            total=_safe_float(raw.get("total")),
            items=items,
            vendor_trn=raw.get("vendor_trn"),
        )

    def update_hints(self, new_hints: str):
        """
        Update extraction hints based on Reflection Agent feedback.
        This is the self-improvement mechanism.
        """
        self.additional_hints = new_hints

    def reset_hints(self):
        """Reset hints to default (no additional context)."""
        self.additional_hints = ""


def _safe_float(value) -> float | None:
    """Safely convert a value to float, handling strings with commas etc."""
    if value is None:
        return None
    try:
        if isinstance(value, str):
            # Remove commas, currency symbols, spaces
            cleaned = value.replace(",", "").replace("AED", "").replace("$", "").strip()
            return float(cleaned) if cleaned else None
        return float(value)
    except (ValueError, TypeError):
        return None
