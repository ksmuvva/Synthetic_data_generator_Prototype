"""
Financial transaction template.

Provides schema for financial transaction records including
transaction ID, amount, currency, date, merchant, and category.
"""

from synth.agent.templates.base import SchemaTemplate, TemplateField


class FinancialTransactionTemplate(SchemaTemplate):
    """
    Template for financial transaction records.

    Fields:
    - transaction_id: Unique transaction identifier
    - amount: Transaction amount (log-normal distribution)
    - currency: Currency code (USD, EUR, GBP, etc.)
    - date: Transaction date
    - merchant: Merchant or vendor name
    - category: Transaction category
    - payment_method: How payment was made
    - status: Transaction status
    """

    template_id = "financial_transaction"
    name = "Financial Transaction"
    description = "Financial transaction records with amount, currency, and merchant details"
    category = "financial"

    def _define_fields(self) -> None:
        """Define the fields for financial transactions."""
        # Transaction ID
        self.add_field(TemplateField(
            name="transaction_id",
            data_type="string",
            description="Unique transaction identifier",
            unique=True,
            nullable=False,
            constraints={"min_length": 12, "max_length": 16},
            generator="uuid",
        ))

        # Amount
        self.add_field(TemplateField(
            name="amount",
            data_type="float",
            description="Transaction amount",
            nullable=False,
            constraints={"range": (10.0, 10000.0)},
        ))

        # Currency
        self.add_field(TemplateField(
            name="currency",
            data_type="categorical",
            description="Currency code",
            nullable=False,
            constraints={"values": ["USD", "EUR", "GBP", "JPY", "CAD"]},
        ))

        # Date
        self.add_field(TemplateField(
            name="date",
            data_type="datetime",
            description="Transaction date",
            nullable=False,
            constraints={"values": ["USD", "EUR", "GBP", "JPY"]},
        ))

        # Merchant
        self.add_field(TemplateField(
            name="merchant",
            data_type="string",
            description="Merchant or vendor name",
            nullable=False,
            constraints={"min_length": 5, "max_length": 50},
        ))

        # Category
        self.add_field(TemplateField(
            name="category",
            data_type="categorical",
            description="Transaction category",
            nullable=False,
            constraints={
                "values": [
                    "Groceries",
                    "Dining",
                    "Transportation",
                    "Shopping",
                    "Entertainment",
                    "Utilities",
                    "Healthcare",
                    "Other",
                ]
            },
        ))

        # Payment Method
        self.add_field(TemplateField(
            name="payment_method",
            data_type="categorical",
            description="Payment method used",
            nullable=False,
            constraints={
                "values": ["Credit Card", "Debit Card", "Cash", "Transfer", "Digital"]
            },
        ))

        # Status
        self.add_field(TemplateField(
            name="status",
            data_type="categorical",
            description="Transaction status",
            nullable=False,
            constraints={"values": ["completed", "pending", "failed", "refunded"]},
        ))
