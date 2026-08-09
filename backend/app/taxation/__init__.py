"""Taxation: India GST rules and tax calculation."""

from app.taxation.service import TaxCalculationResult, calculate_customer_transaction_tax

__all__ = ["TaxCalculationResult", "calculate_customer_transaction_tax"]
