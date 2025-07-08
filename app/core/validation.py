import re
from datetime import datetime
from typing import List, Optional
from app.models.invoice import Transaction, TransactionType


class TransactionValidator:
    def __init__(self, transactions: List[Transaction], reference_date: datetime):
        self.transactions = transactions
        self.reference_date = reference_date
        self.results = {}

    def validate_required_fields(self) -> bool:
        for t in self.transactions:
            if not t.transaction_date or not t.description or t.amount is None:
                print(f"[VALIDATION] Missing required fields in transaction: {t}")
                return False
            print(f"[VALIDATION] Required fields validated")
        return True

    def validate_no_duplicates(self) -> bool:
        seen = set()
        for t in self.transactions:
            key = (t.transaction_date, t.amount, t.description.strip().lower())
            if key in seen:
                print(f"[VALIDATION] Duplicate transaction found: {t}")
                return False
            seen.add(key)
            print(f"[VALIDATION] No duplicates validated")
        return True

    def validate_dates(self) -> bool:
        now = datetime.now().date()
        for t in self.transactions:
            if (
                t.transaction_date > self.reference_date.date()
                or t.transaction_date > now
            ):
                print(
                    f"[VALIDATION] Invalid transaction date: {t.transaction_date} in transaction: {t}"
                )
                return False
        print(f"[VALIDATION] Dates validated")
        return True

    def validate_transactions_sum(
        self, invoice_total: float, tolerance: float = 0.01
    ) -> bool:
        total = 0.0
        for t in self.transactions:
            print(f"[VALIDATION] Transaction: {t}")
            if getattr(t, "type", None) == TransactionType.CREDIT:
                print(f"[VALIDATION] Credit transaction: {t.amount}")
                total -= t.amount
            else:
                print(f"[VALIDATION] Debit transaction: {t.amount}")
                total += t.amount
        if abs(total - invoice_total) <= tolerance:
            print(f"[VALIDATION] Sum validated")
            return True
        print(
            f"[VALIDATION] Sum mismatch: calculated {total}, expected {invoice_total}"
        )
        return False

    def validate_amount_range(
        self, min_value: float = 0.01, max_value: float = 100_000
    ) -> bool:
        for t in self.transactions:
            if not (min_value <= t.amount <= max_value):
                print(
                    f"[VALIDATION] Transaction amount out of range: {t.amount} in transaction: {t}"
                )
                return False
        print(f"[VALIDATION] Amount range validated")
        return True

    def validate_installments_consistency(self) -> bool:
        for t in self.transactions:
            if t.installments > 1:
                expected_total = t.amount * t.installments
                if abs(t.total_purchase_amount - expected_total) > 0.01:
                    print(
                        f"[VALIDATION] Installments inconsistency: {t.total_purchase_amount} != {t.amount} * {t.installments} in transaction: {t}"
                    )
                    return False
        print(f"[VALIDATION] Installments consistency validated")
        return True

    def validate_due_date_consistency(self) -> bool:
        expected_due_date = None
        for t in self.transactions:
            if expected_due_date is None:
                expected_due_date = t.due_date
            if t.due_date != expected_due_date:
                print(
                    f"[VALIDATION] Due date inconsistency: {t.due_date} != {expected_due_date} in transaction: {t}"
                )
                return False
        print(f"[VALIDATION] Due date consistency validated")
        return True

    def run_all(self, invoice_total: Optional[float] = None) -> dict:
        checks = {
            "required_fields": self.validate_required_fields(),
            "no_duplicates": self.validate_no_duplicates(),
            "valid_dates": self.validate_dates(),
            "amount_range": self.validate_amount_range(),
            "installments_consistency": self.validate_installments_consistency(),
            "due_date_consistency": self.validate_due_date_consistency(),
        }
        if invoice_total is not None:
            checks["sum_valid"] = self.validate_transactions_sum(invoice_total)
        self.results = checks
        score = sum(checks.values()) / len(checks)
        print(f"[VALIDATION] Confidence score: {score:.2f}")
        return {"score": score, "details": checks}
