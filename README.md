# AI Expense Analyzer

A full-stack web application that uses AI to extract structured data from PDF and XLS files. It parses invoices and bank statements, providing automated categorization, spending trends, and AI-powered financial insights.

## 🚀 Features

-   **Intelligent Extraction**: Uses Gemini, Claude, or Groq to parse PDF invoices and bank statements.
-   **Excel Support**: Native support for HDFC bank statement XLS exports.
-   **Analytical Dashboard**: View spending trends, top expenses, and category breakdowns.
-   **AI Financial Agent**: Chat with your data to get personalized insights and recommendations.
-   **Secure**: Sensitive data and API keys are managed locally via environment variables.

## 🛠️ Tech Stack

-   **Backend**: FastAPI (Python)
-   **Frontend**: Streamlit
-   **AI Engine**: Google GenAI, Anthropic, OpenAI, Groq

## 📦 Setup & Installation

### 1. Prerequisites
-   Python 3.11+
-   `uv` for fast package management

### 2. Configure Environment
Create a `.env` file inside the `backend/` directory:

```env
AI_PROVIDER="groq" # or "gemini", "claude", "openai"
GEMINI_API_KEY="YOUR_KEY"
ANTHROPIC_API_KEY="YOUR_KEY"
OPENAI_API_KEY="YOUR_KEY"
GROQ_API_KEY="YOUR_KEY"
```

### 3. Install Dependencies
Run the following from the project root:

```bash
cd backend
uv sync
```

## 🏃 Running the Application

You need to run the **Backend** and **Frontend** in separate terminals.

### Step 1: Start the Backend API
```bash
cd backend
uv run uvicorn app.api:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

### Step 2: Start the Frontend UI
```bash
cd backend
uv run streamlit run ../frontend/app.py
```
The dashboard will open automatically in your browser at `http://localhost:8501`.

## 🔒 Security Note
-   Never commit your `.env` file to version control. It is already added to `.gitignore`.
-   All processing of your financial documents happens via the API providers you configure.
-   Data is stored locally in `transactions.json` and `financial_report.json`.
