"""
Validation Agent - Checks extracted invoice data for accuracy and consistency.

Performs financial validation including:
- UAE VAT rate verification (5%)
- Mathematical consistency (subtotal + VAT = total)
- Missing field detection
- Suspicious value flagging
- Confidence score computation

PRIVACY NOTICE:
Validation is purely computational. No data is stored or transmitted.
"""

from datetime import datetime
from models.schemas import InvoiceData, ValidationReport, ValidationError

# UAE VAT rate
UAE_VAT_RATE = 0.05
# Tolerance for floating point comparison (in currency units)
TOLERANCE = 0.5


class ValidationAgent:
    """
    Agent responsible for validating extracted invoice data.
    Focuses on UAE VAT compliance and financial consistency.
    """

    def validate(self, invoice: InvoiceData) -> ValidationReport:
        """
        Validate extracted invoice data and compute confidence score.
        
        Args:
            invoice: Extracted invoice data to validate.
            
        Returns:
            ValidationReport with confidence score and any errors/warnings.
        """
        errors = []
        warnings = []
        score_deductions = 0.0

        # --- Check required fields ---
        required_checks = [
            ("invoice_number", invoice.invoice_number, 8),
            ("vendor_name", invoice.vendor_name, 8),
            ("invoice_date", invoice.invoice_date, 5),
            ("total", invoice.total, 10),
        ]

        for field_name, value, deduction in required_checks:
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(ValidationError(
                    field=field_name,
                    message=f"Missing required field: {field_name}",
                    severity="error"
                ))
                score_deductions += deduction

        # --- Check tax fields specifically ---
        if invoice.vat_amount is None:
            errors.append(ValidationError(
                field="vat_amount",
                message="Missing VAT amount - critical for UAE tax compliance",
                severity="error"
            ))
            score_deductions += 12

        if invoice.subtotal is None:
            warnings.append(ValidationError(
                field="subtotal",
                message="Missing subtotal before VAT",
                severity="warning"
            ))
            score_deductions += 5

        # --- Mathematical consistency: subtotal + VAT = total ---
        if invoice.subtotal is not None and invoice.vat_amount is not None and invoice.total is not None:
            expected_total = invoice.subtotal + invoice.vat_amount
            if abs(expected_total - invoice.total) > TOLERANCE:
                errors.append(ValidationError(
                    field="total",
                    message=f"Math mismatch: subtotal ({invoice.subtotal}) + VAT ({invoice.vat_amount}) = {expected_total}, but total is {invoice.total}",
                    severity="error"
                ))
                score_deductions += 15

        # --- UAE VAT rate verification (5%) ---
        if invoice.subtotal is not None and invoice.vat_amount is not None:
            expected_vat = round(invoice.subtotal * UAE_VAT_RATE, 2)
            if invoice.vat_amount > 0 and abs(expected_vat - invoice.vat_amount) > TOLERANCE:
                warnings.append(ValidationError(
                    field="vat_amount",
                    message=f"VAT amount ({invoice.vat_amount}) does not match 5% of subtotal ({expected_vat}). "
                            f"Expected UAE VAT: {expected_vat}",
                    severity="warning"
                ))
                score_deductions += 8

        # --- Verify VAT from total if subtotal missing ---
        if invoice.subtotal is None and invoice.total is not None and invoice.vat_amount is not None:
            implied_subtotal = invoice.total - invoice.vat_amount
            expected_vat_from_total = round(implied_subtotal * UAE_VAT_RATE, 2)
            if abs(expected_vat_from_total - invoice.vat_amount) > TOLERANCE:
                warnings.append(ValidationError(
                    field="vat_amount",
                    message=f"VAT ({invoice.vat_amount}) doesn't align with 5% rate from implied subtotal ({implied_subtotal:.2f})",
                    severity="warning"
                ))
                score_deductions += 5

        # --- Suspicious value checks ---
        if invoice.total is not None and invoice.total < 0:
            errors.append(ValidationError(
                field="total",
                message=f"Negative total amount: {invoice.total}",
                severity="error"
            ))
            score_deductions += 10

        if invoice.vat_amount is not None and invoice.vat_amount < 0:
            errors.append(ValidationError(
                field="vat_amount",
                message=f"Negative VAT amount: {invoice.vat_amount}",
                severity="error"
            ))
            score_deductions += 10

        if invoice.subtotal is not None and invoice.total is not None:
            if invoice.subtotal > invoice.total:
                warnings.append(ValidationError(
                    field="subtotal",
                    message=f"Subtotal ({invoice.subtotal}) is greater than total ({invoice.total})",
                    severity="warning"
                ))
                score_deductions += 8

        # --- Date validation ---
        if invoice.invoice_date:
            try:
                parsed_date = datetime.strptime(invoice.invoice_date, "%Y-%m-%d")
                if parsed_date > datetime.now():
                    warnings.append(ValidationError(
                        field="invoice_date",
                        message=f"Future date detected: {invoice.invoice_date}",
                        severity="warning"
                    ))
                    score_deductions += 3
            except ValueError:
                warnings.append(ValidationError(
                    field="invoice_date",
                    message=f"Date format not standard YYYY-MM-DD: {invoice.invoice_date}",
                    severity="warning"
                ))
                score_deductions += 2

        # --- Vendor TRN check ---
        if not invoice.vendor_trn:
            warnings.append(ValidationError(
                field="vendor_trn",
                message="No vendor Tax Registration Number (TRN) found",
                severity="warning"
            ))
            score_deductions += 3

        # --- Currency check ---
        if invoice.currency not in ("AED", "USD", "EUR", "GBP", "SAR"):
            warnings.append(ValidationError(
                field="currency",
                message=f"Unusual currency detected: {invoice.currency}",
                severity="warning"
            ))
            score_deductions += 2

        # --- Compute confidence score ---
        confidence = max(0.0, min(100.0, 100.0 - score_deductions))
        is_valid = len(errors) == 0

        # Build notes
        notes_parts = []
        if is_valid:
            notes_parts.append("All validations passed.")
        else:
            notes_parts.append(f"{len(errors)} error(s) found.")
        if warnings:
            notes_parts.append(f"{len(warnings)} warning(s).")

        return ValidationReport(
            is_valid=is_valid,
            confidence_score=confidence,
            errors=errors,
            warnings=warnings,
            notes=" ".join(notes_parts)
        )
