"""
Reflection Agent - Self-improvement core of the multi-agent system.

Analyzes extraction errors, compares output against expected invoice patterns,
and dynamically adjusts the Extraction Agent's prompts to improve accuracy.

Improvement is achieved WITHOUT retraining model weights - purely through
prompt engineering and strategy adjustment.

PRIVACY NOTICE:
Reflection metrics are logged without storing any sensitive invoice data.
Only confidence scores, field names, and strategy descriptions are kept.
"""

from models.schemas import (
    InvoiceData,
    ValidationReport,
    ReflectionMetrics,
    MetricsHistory,
)
from services.llm_service import generate


class ReflectionAgent:
    """
    Agent responsible for analyzing extraction quality and improving
    the system's accuracy over time.
    """

    def __init__(self):
        self.metrics_history: list[ReflectionMetrics] = []
        self.run_counter = 0
        self.confidence_threshold = 80.0  # Below this, trigger re-extraction

    async def reflect_and_improve(
        self,
        ocr_text: str,
        extraction: InvoiceData,
        validation: ValidationReport,
        extraction_agent,  # Reference to the ExtractionAgent to update its prompts
    ) -> tuple[InvoiceData, ValidationReport, ReflectionMetrics]:
        """
        Analyze extraction quality and attempt to improve it.
        
        If confidence is below threshold:
        1. Analyze what went wrong using LLM
        2. Generate improved extraction hints
        3. Re-run extraction with improved prompts
        4. Re-validate and compare
        
        Args:
            ocr_text: Original OCR text.
            extraction: Initial extraction result.
            validation: Initial validation result.
            extraction_agent: The ExtractionAgent instance to update.
            
        Returns:
            Tuple of (final_extraction, final_validation, metrics).
        """
        self.run_counter += 1
        initial_confidence = validation.confidence_score

        metrics = ReflectionMetrics(
            run_id=self.run_counter,
            confidence_before=initial_confidence,
            confidence_after=initial_confidence,
            fields_improved=[],
            strategy_changes=[],
            improvement_delta=0.0,
        )

        # If confidence is already high, no improvement needed
        if initial_confidence >= self.confidence_threshold:
            metrics.strategy_changes.append("No improvement needed - confidence above threshold")
            self._record_metrics(metrics)
            return extraction, validation, metrics

        # --- REFLECTION PHASE ---
        # Analyze what went wrong
        error_analysis = self._build_error_summary(validation)
        improvement_hints = await self._generate_improvement_hints(
            ocr_text, error_analysis, extraction
        )

        if improvement_hints:
            metrics.strategy_changes.append(f"Updated extraction hints: {improvement_hints[:100]}...")

            # Update the extraction agent's hints
            extraction_agent.update_hints(improvement_hints)

            # --- RE-EXTRACTION PHASE ---
            improved_extraction = await extraction_agent.extract(ocr_text)

            # --- RE-VALIDATION PHASE ---
            from agents.validation_agent import ValidationAgent
            validator = ValidationAgent()
            improved_validation = validator.validate(improved_extraction)

            # Calculate improvement
            new_confidence = improved_validation.confidence_score
            metrics.confidence_after = new_confidence
            metrics.improvement_delta = new_confidence - initial_confidence

            # Track which fields improved
            metrics.fields_improved = self._find_improved_fields(
                extraction, improved_extraction, validation, improved_validation
            )

            if new_confidence > initial_confidence:
                metrics.strategy_changes.append(
                    f"Improvement achieved: {initial_confidence:.1f} -> {new_confidence:.1f}"
                )
                self._record_metrics(metrics)
                return improved_extraction, improved_validation, metrics
            else:
                metrics.strategy_changes.append(
                    "Re-extraction did not improve results, keeping original"
                )
                metrics.confidence_after = initial_confidence
                metrics.improvement_delta = 0.0

        self._record_metrics(metrics)
        return extraction, validation, metrics

    async def _generate_improvement_hints(
        self, ocr_text: str, error_summary: str, extraction: InvoiceData
    ) -> str:
        """
        Use the LLM to analyze extraction errors and generate better hints
        for the next extraction attempt.
        """
        prompt = f"""You are analyzing why an invoice extraction had errors.

ERRORS FOUND:
{error_summary}

CURRENT EXTRACTION RESULT:
- Invoice Number: {extraction.invoice_number}
- Vendor Name: {extraction.vendor_name}
- Date: {extraction.invoice_date}
- Subtotal: {extraction.subtotal}
- VAT Amount: {extraction.vat_amount}
- Total: {extraction.total}
- Vendor TRN: {extraction.vendor_trn}

ORIGINAL TEXT (first 500 chars):
{ocr_text[:500]}

Based on these errors, provide SPECIFIC extraction hints that would help correctly extract the data.
Focus on:
1. What fields are missing and where they might be found in the text
2. Any number parsing issues (commas, currency symbols)
3. UAE VAT (5%) calculation hints
4. Date format corrections
5. Any patterns you see in the text that were missed

Provide your hints as a brief, direct instruction paragraph (max 150 words).
Do NOT include JSON or code. Just plain text instructions."""

        system = "You are a helpful assistant that analyzes document extraction errors and provides improvement hints."

        try:
            hints = await generate(prompt, system)
            return hints.strip()
        except Exception:
            return ""

    def _build_error_summary(self, validation: ValidationReport) -> str:
        """Build a human-readable error summary from validation report."""
        parts = []
        for err in validation.errors:
            parts.append(f"- ERROR [{err.field}]: {err.message}")
        for warn in validation.warnings:
            parts.append(f"- WARNING [{warn.field}]: {warn.message}")
        return "\n".join(parts) if parts else "No specific errors found."

    def _find_improved_fields(
        self,
        old: InvoiceData,
        new: InvoiceData,
        old_val: ValidationReport,
        new_val: ValidationReport,
    ) -> list[str]:
        """Identify which fields improved between extraction runs."""
        improved = []

        # Check if previously missing fields are now present
        field_pairs = [
            ("invoice_number", old.invoice_number, new.invoice_number),
            ("vendor_name", old.vendor_name, new.vendor_name),
            ("invoice_date", old.invoice_date, new.invoice_date),
            ("subtotal", old.subtotal, new.subtotal),
            ("vat_amount", old.vat_amount, new.vat_amount),
            ("total", old.total, new.total),
            ("vendor_trn", old.vendor_trn, new.vendor_trn),
        ]

        for name, old_val_field, new_val_field in field_pairs:
            if (old_val_field is None or old_val_field == "") and new_val_field is not None and new_val_field != "":
                improved.append(name)

        return improved

    def _record_metrics(self, metrics: ReflectionMetrics):
        """Record metrics without storing any sensitive data."""
        self.metrics_history.append(metrics)

    def get_metrics_history(self) -> MetricsHistory:
        """Return historical metrics for display in frontend."""
        if not self.metrics_history:
            return MetricsHistory()

        avg_confidence = sum(m.confidence_after for m in self.metrics_history) / len(self.metrics_history)
        avg_improvement = sum(m.improvement_delta for m in self.metrics_history) / len(self.metrics_history)

        return MetricsHistory(
            history=self.metrics_history,
            average_confidence=round(avg_confidence, 1),
            total_extractions=len(self.metrics_history),
            average_improvement=round(avg_improvement, 1),
        )
