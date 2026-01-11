from pydantic import BaseModel, Field
from typing import List


# -----------------------
# Transaction model
# -----------------------

class Transaction(BaseModel):
    date: str | None = Field(None, description="Transaction date (DD/MM/YYYY format)")
    description: str | None = Field(None, description="Transaction description/narration")
    cheque_ref_no: str | None = Field(None, description="Cheque or reference number")
    value_date: str | None = Field(None, description="Value date")
    withdrawal: float | None = Field(None, description="Withdrawal/debit amount")
    deposit: float | None = Field(None, description="Deposit/credit amount")
    balance: float | None = Field(None, description="Balance after transaction")


# -----------------------
# Bank Statement model
# -----------------------

class BankStatementData(BaseModel):
    account_holder: str | None = Field(None, description="Account holder name")
    account_number: str | None = Field(None, description="Bank account number")
    bank_name: str | None = Field(None, description="Name of the bank")
    branch: str | None = Field(None, description="Bank branch name or code")
    statement_period_from: str | None = Field(None, description="Statement start date")
    statement_period_to: str | None = Field(None, description="Statement end date")
    opening_balance: float | None = Field(None, description="Opening balance")
    closing_balance: float | None = Field(None, description="Closing balance")
    currency: str | None = Field(None, description="Currency code (INR, USD, etc)")
    transactions: List[Transaction] = Field(default_factory=list, description="List of all transactions in the statement")


# -----------------------
# Legacy Invoice model (keep for backwards compatibility)
# -----------------------

class InvoiceData(BaseModel):
    invoice_number: str | None = Field(None, description="Invoice number")
    date: str | None = Field(None, description="Invoice date")
    total_amount: float | None = Field(None, description="Total invoice amount")
    tax_amount: float | None = Field(None, description="Tax amount")
    vendor: str | None = Field(None, description="Sender / vendor name")
    recipient: str | None = Field(None, description="Recipient name")
    account_no: str | None = Field(None, description="Account number")


# -----------------------
# Optional layout metadata
# -----------------------

class LayoutField(BaseModel):
    bounding_box: list[int] | None = Field(
        None, description="Bounding box [y_min, x_min, y_max, x_max] scaled 0-1000"
    )
    page: int | None = Field(None, description="Page number starting from 1")


class InvoiceLayout(BaseModel):
    invoice_number: LayoutField | None = None
    date: LayoutField | None = None
    total_amount: LayoutField | None = None
    tax_amount: LayoutField | None = None
    vendor: LayoutField | None = None
    recipient: LayoutField | None = None
    account_no: LayoutField | None = None


# -----------------------
# Combined response model
# -----------------------

class InvoiceExtraction(BaseModel):
    data: InvoiceData
    layout: InvoiceLayout | None = None