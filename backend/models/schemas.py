"""
Pydantic models for the TrustAI Invoice Extraction System.

PRIVACY NOTICE:
All models defined here are used for in-memory processing only.
No invoice data is persisted to disk or transmitted externally.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LineItem(BaseModel):
    """A single line item from an invoice."""
    description: str = ""
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class InvoiceData(BaseModel):
    """Structured data extracted from an invoice or receipt."""
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: str = "AED"
    subtotal: Optional[float] = None
    vat_amount: Optional[float] = None
    total: Optional[float] = None
    items: list[LineItem] = Field(default_factory=list)
    vendor_trn: Optional[str] = None  # Tax Registration Number


class ValidationError(BaseModel):
    """A single validation error or warning."""
    field: str
    message: str
    severity: str = "error"  # "error" or "warning"


class ValidationReport(BaseModel):
    """Report from the Validation Agent."""
    is_valid: bool = False
    confidence_score: float = 0.0  # 0-100
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)
    notes: str = ""


class ReflectionMetrics(BaseModel):
    """Metrics from the Reflection Agent's self-improvement cycle."""
    run_id: int = 0
    confidence_before: float = 0.0
    confidence_after: float = 0.0
    fields_improved: list[str] = Field(default_factory=list)
    strategy_changes: list[str] = Field(default_factory=list)
    improvement_delta: float = 0.0


class ExtractionResponse(BaseModel):
    """Complete response returned to the frontend."""
    extracted_data: InvoiceData
    validation: ValidationReport
    metrics: ReflectionMetrics
    ocr_text: str = ""
    excel_filename: str = ""
    processing_time_seconds: float = 0.0
    privacy_notice: str = "All processing performed locally. No data left this machine."


class MetricsHistory(BaseModel):
    """Historical improvement metrics (no sensitive data stored)."""
    history: list[ReflectionMetrics] = Field(default_factory=list)
    average_confidence: float = 0.0
    total_extractions: int = 0
    average_improvement: float = 0.0
