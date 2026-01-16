import os
import sys
from models import InvoiceData, BankStatementData, InvoiceExtraction
from providers import get_provider
import fitz  # PyMuPDF
import config
from pdf_utils import unlock_pdf
import tempfile
from pathlib import Path


def detect_document_type(pdf_path: str) -> str:
    """
    Detect if document is a bank statement or invoice by checking first page text.
    """
    import fitz
    doc = fitz.open(pdf_path)
    first_page = doc[0].get_text().lower()
    doc.close()
    
    # Check for bank statement indicators
    bank_indicators = ['statement of account', 'bank statement', 'account statement', 
                      'opening balance', 'closing balance', 'transaction details']
    
    if any(indicator in first_page for indicator in bank_indicators):
        return "bank_statement"
    
    # Check for invoice indicators
    invoice_indicators = ['invoice', 'bill', 'tax invoice', 'invoice number']
    
    if any(indicator in first_page for indicator in invoice_indicators):
        return "invoice"
    
    # Default to bank statement for financial documents
    return "bank_statement"


def extract_document_data(pdf_path: str, doc_type: str = None, include_layout: bool = False):
    """
    Extract data from financial documents (bank statements or invoices).
    Auto-detects document type if not specified.
    """
    
    # Auto-detect document type if not provided
    if doc_type is None:
        doc_type = detect_document_type(pdf_path)
        print(f"📋 Detected document type: {doc_type.upper()}")
    
    # Get AI provider
    provider = get_provider()
    print(f"📄 Using {provider.get_provider_name()} for extraction...")
    
    # Choose schema and prompt based on document type
    if doc_type == "bank_statement":
        from models import BankStatementData
        schema = BankStatementData
        prompt = """
Extract ALL information from this bank statement document.

Account Information:
- account_holder: Full name of account holder
- account_number: Bank account number
- bank_name: Name of the bank (e.g., HDFC Bank, ICICI Bank)
- branch: Branch name or code
- statement_period_from: Statement start date (format: DD/MM/YYYY)
- statement_period_to: Statement end date (format: DD/MM/YYYY)
- opening_balance: Opening balance amount
- closing_balance: Closing balance amount
- currency: Currency code (INR, USD, EUR, etc.)

Transactions:
Extract EVERY transaction from the statement into the transactions array.
For each transaction, extract:
- date: Transaction date (DD/MM/YYYY)
- description: Full transaction description/narration
- cheque_ref_no: Cheque number or reference number if present
- value_date: Value date if different from transaction date
- withdrawal: Withdrawal/debit amount (use null if not applicable)
- deposit: Deposit/credit amount (use null if not applicable)  
- balance: Balance after this transaction

CRITICAL INSTRUCTIONS:
1. Extract ALL transactions - do not skip any, even if there are 50+ transactions
2. For amounts, use only numeric values (no currency symbols)
3. Maintain the exact chronological order of transactions
4. If a field is not present in the statement, use null
5. Return ONLY valid JSON matching the schema
6. Ensure all opening/closing balances and transaction amounts are accurate

This is a multi-page document. Process ALL pages carefully.
"""
    else:  # invoice
        from models import InvoiceData, InvoiceExtraction
        schema = InvoiceExtraction if include_layout else InvoiceData
        prompt = """
Extract all invoice information from this document.

Required fields:
- invoice_number: The invoice/document number
- date: Invoice date (keep original format)
- total_amount: Total amount due (numeric value only)
- tax_amount: Tax/VAT amount if present (numeric value only)
- vendor: Company/person issuing the invoice
- recipient: Company/person receiving the invoice
- account_no: Bank account number if present

IMPORTANT:
- Return ONLY valid JSON matching the schema
- If a field is missing or not found, return null
- For amounts, extract only the numeric value without currency symbols
"""
        
        if include_layout:
            prompt += """

Additionally, provide layout information for each field:
- bounding_box: [y_min, x_min, y_max, x_max] in normalized coordinates (0-1000 scale)
- page: page number (1-indexed, starting from 1)

Layout rules:
- If you cannot determine the position, use bounding_box: [0, 0, 0, 0]
- If field not found, set both bounding_box and page to null
"""
    
    # Extract using provider
    print(f"🤖 Extracting {doc_type.replace('_', ' ')}...")
    result = provider.extract_from_pdf(pdf_path, prompt, schema)
    print("✅ Extraction complete")
    
    return result, doc_type

def annotate_pdf(pdf_path: str, extraction: InvoiceExtraction, output_path: str):
    """Draw bounding boxes on PDF"""
    
    doc = fitz.open(pdf_path)
    
    if not extraction.layout:
        print("⚠️  No layout information available for annotation")
        doc.close()
        return
    
    field_colors = {
        'invoice_number': (1, 0, 0),
        'date': (0, 0.8, 0),
        'total_amount': (0, 0, 1),
        'tax_amount': (1, 0.5, 0),
        'vendor': (0.6, 0, 0.6),
        'recipient': (0, 0.7, 0.7),
        'account_no': (0.9, 0.9, 0),
    }
    
    annotations_drawn = 0
    
    for field_name, color in field_colors.items():
        layout_field = getattr(extraction.layout, field_name)
        
        if not layout_field or not layout_field.bounding_box or not layout_field.page:
            continue
        
        box = layout_field.bounding_box
        if box == [0, 0, 0, 0]:
            continue
        
        page_num = layout_field.page
        if page_num < 1 or page_num > len(doc):
            continue
            
        page = doc[page_num - 1]
        y0, x0, y1, x1 = box
        page_rect = page.rect
        
        rect = fitz.Rect(
            (x0 / 1000) * page_rect.width,
            (y0 / 1000) * page_rect.height,
            (x1 / 1000) * page_rect.width,
            (y1 / 1000) * page_rect.height
        )
        
        page.draw_rect(rect, color=color, width=2)
        label = field_name.replace('_', ' ').title()
        page.insert_text((rect.x0, rect.y0 - 3), label, fontsize=8, color=color)
        annotations_drawn += 1
    
    if annotations_drawn > 0:
        doc.save(output_path)
        print(f"✅ Annotated PDF saved to '{output_path}' ({annotations_drawn} fields marked)")
    else:
        print("⚠️  No valid bounding boxes found")
    
    doc.close()


def print_bank_statement_data(data: BankStatementData):
    """Pretty print bank statement data"""
    print("\n" + "="*70)
    print("📊 EXTRACTED BANK STATEMENT DATA")
    print("="*70)
    print(f"Account Holder    : {data.account_holder or 'N/A'}")
    print(f"Account Number    : {data.account_number or 'N/A'}")
    print(f"Bank              : {data.bank_name or 'N/A'}")
    print(f"Branch            : {data.branch or 'N/A'}")
    print(f"Statement Period  : {data.statement_period_from or 'N/A'} to {data.statement_period_to or 'N/A'}")
    print(f"Currency          : {data.currency or 'INR'}")
    print(f"Opening Balance   : {data.opening_balance or 'N/A'}")
    print(f"Closing Balance   : {data.closing_balance or 'N/A'}")
    print(f"Total Transactions: {len(data.transactions)}")
    print("="*70)
    
    if data.transactions:
        print("\n📝 TRANSACTIONS (showing first 10):")
        print("-" * 70)
        for i, txn in enumerate(data.transactions[:10], 1):
            print(f"\n{i}. Date: {txn.date}")
            print(f"   Description: {txn.description}")
            if txn.withdrawal:
                print(f"   Withdrawal: {txn.withdrawal}")
            if txn.deposit:
                print(f"   Deposit: {txn.deposit}")
            print(f"   Balance: {txn.balance}")
        
        if len(data.transactions) > 10:
            print(f"\n... and {len(data.transactions) - 10} more transactions")
    print("="*70 + "\n")


def print_invoice_data(data: InvoiceData):
    """Pretty print invoice data"""
    print("\n" + "="*50)
    print("📊 EXTRACTED INVOICE DATA")
    print("="*50)
    print(f"Invoice Number : {data.invoice_number or 'N/A'}")
    print(f"Date           : {data.date or 'N/A'}")
    print(f"Vendor         : {data.vendor or 'N/A'}")
    print(f"Recipient      : {data.recipient or 'N/A'}")
    print(f"Total Amount   : {data.total_amount or 'N/A'}")
    print(f"Tax Amount     : {data.tax_amount or 'N/A'}")
    print(f"Account Number : {data.account_no or 'N/A'}")
    print("="*50 + "\n")


if __name__ == "__main__":
    PDF_FILE = "big_invoice.pdf" #Change file name here
    OUTPUT_FILE = "annotated_invoice.pdf"
    
    print(f"\n🚀 Document Analyzer Starting...")
    print(f"📡 AI Provider: {config.AI_PROVIDER.upper()}\n")
    
    # Check if PDF exists
    if not os.path.exists(PDF_FILE):
        print(f"❌ Error: PDF file '{PDF_FILE}' not found")
        print(f"Please place your document PDF in the project folder")
        exit(1)
    
    # Handle password-protected PDFs
    temp_pdf_created = None
    try:
        print("🔍 Checking PDF status...")
        
        doc = fitz.open(PDF_FILE)
        
        if doc.is_encrypted:
            doc.close()
            print("🔒 PDF is password-protected")
            
            unlocked_doc = unlock_pdf(PDF_FILE)
            
            temp_pdf = Path(tempfile.gettempdir()) / f"unlocked_{Path(PDF_FILE).name}"
            unlocked_doc.save(str(temp_pdf), encryption=fitz.PDF_ENCRYPT_NONE)
            unlocked_doc.close()
            
            print(f"📄 Temporary unlocked PDF: {temp_pdf}")
            PDF_FILE = str(temp_pdf)
            temp_pdf_created = str(temp_pdf)
        else:
            doc.close()
            print("✅ PDF is not password-protected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
    
    # Extract data (auto-detects document type)
    print("\n🔍 Extracting Document Data")
    print("-" * 50)
    
    data, doc_type = extract_document_data(PDF_FILE, doc_type=None, include_layout=False)
    
    # Print results based on document type
    if doc_type == "bank_statement":
        print_bank_statement_data(data)
        
        # Save transactions to JSON for further analysis
        import json
        with open("transactions.json", "w") as f:
            json.dump(data.model_dump(), f, indent=2)
        print("💾 Full statement data saved to transactions.json")
        
    else:  # invoice
        print_invoice_data(data)
    
    # Clean up temp file
    if temp_pdf_created and os.path.exists(temp_pdf_created):
        os.remove(temp_pdf_created)
        print("🗑️  Temporary unlocked PDF cleaned up")
    
    print("\n✨ All done!\n")