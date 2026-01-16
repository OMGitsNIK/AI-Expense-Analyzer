# AI Document Analyzer

This project is a Python-based document analysis tool that uses AI to extract structured data from PDF and XLS files. It can parse invoices and bank statements, providing insights into the contained data.

## Features

- **PDF Invoice Parsing:** Extracts line items, totals, and other information from PDF invoices.
- **XLS Bank Statement Parsing:** Parses HDFC bank statements in XLS format to extract transaction data.
- **AI-Powered Analysis:** Uses various AI providers (like Gemini, Claude, etc.) to analyze the extracted data.

## Setup

1.  **Install Dependencies:**
    This project uses `uv` for package management. To install the dependencies, run:
    ```bash
    uv sync
    ```

2.  **Configure Environment:**
    Create a `.env` file in the root directory and add the following, choosing your desired AI provider:
    ```
    AI_PROVIDER="gemini" # or "claude", "openai", "groq", "openrouter"
    API_KEY="YOUR_API_KEY"
    ```

## Usage

### Analyzing PDF Invoices

1.  Place your PDF invoice in the root directory (e.g., `invoice.pdf`).
2.  Update the `PDF_FILE` variable in `main.py` to point to your file.
3.  Run the main script:
    ```bash
    uv run python main.py
    ```

### Parsing XLS Bank Statements

1.  Place your XLS bank statement file in the root directory (e.g., `invoice_excel.xls`).
2.  Run the `parse_xls.py` script:
    ```bash
    uv run python parse_xls.py
    ```
    This will generate a `transactions.json` file with the parsed data.

### Analyzing Transactions with AI

After extracting data, you can use `analyze.py` to get AI-powered insights:

```bash
uv run python analyze.py
```
