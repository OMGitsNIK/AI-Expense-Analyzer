import shutil
import tempfile
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.main import extract_document_data
from app.parse_xls import parse_bank_statement_xls
from app.analytics import FinancialAnalyzer
from app.ai_insights import FinancialInsightsAgent
from app import config

# -----------------------------------------------------------------------------
# Global State (Simplified persistence)
# -----------------------------------------------------------------------------
TRANSACTIONS_FILE = Path("transactions.json")
REPORT_FILE = Path("financial_report.json")
INSIGHTS_FILE = Path("financial_insights.md")

# -----------------------------------------------------------------------------
# App Lifecycle
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure necessary files/dirs exist
    print("🚀 API Starting...")
    yield
    # Shutdown
    print("👋 API Shutting down...")

app = FastAPI(title="AI Expense Analyzer API", lifespan=lifespan)

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. In prod, lock this down.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def save_transactions(data: Dict[str, Any]):
    """Save extracted data to transactions.json"""
    # If it's bank statement data, it has 'transactions' key
    # If it's invoice data, we might want to append it to a list?
    # For now, let's treat this as "Current Session Data" overwrite
    # But for a real app, we'd append or DB.
    # The current CLI overwrites "transactions.json" for bank statements.
    
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_stored_transactions() -> Dict[str, Any]:
    if not TRANSACTIONS_FILE.exists():
        return {}
    try:
        with open(TRANSACTIONS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def load_stored_report() -> Dict[str, Any]:
    if not REPORT_FILE.exists():
        return {}
    try:
        with open(REPORT_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "AI Expense Analyzer API is running"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a file (PDF or XLS).
    Returns the extracted data.
    """
    filename = file.filename
    ext = filename.split('.')[-1].lower()
    
    if ext not in ['pdf', 'xls', 'xlsx']:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use PDF or XLS.")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        data = {}
        doc_type = "unknown"
        
        if ext in ['xls', 'xlsx']:
            doc_type = "bank_statement_xls"
            # Parse XLS
            # Note: parse_xls.py might behave differently for xlsx vs xls, 
            # but pandas reads both usually.
            data = parse_bank_statement_xls(tmp_path)
            # Save immediately
            save_transactions(data)
            
        elif ext == 'pdf':
            # Extract PDF
            # extract_document_data returns (result, doc_type)
            # result is a Pydantic model
            result, doc_type = extract_document_data(tmp_path)
            data = result.model_dump()
            
            if doc_type == "bank_statement":
                save_transactions(data)
            
        return {
            "status": "success",
            "doc_type": doc_type,
            "data": data
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.get("/api/transactions")
async def get_transactions():
    """Get stored transactions"""
    data = load_stored_transactions()
    transactions = data.get("transactions", [])
    account_info = {k: v for k, v in data.items() if k != "transactions"}
    return {
        "account_info": account_info,
        "transactions": transactions
    }

@app.get("/api/analysis")
async def get_analysis():
    """Trigger analysis and return report + insights"""
    if not TRANSACTIONS_FILE.exists():
        raise HTTPException(status_code=404, detail="No transactions found. Upload a statement first.")
    
    try:
        # 1. Run Quantitative Analysis
        analyzer = FinancialAnalyzer(str(TRANSACTIONS_FILE))
        report = analyzer.generate_full_report()
        
        # Serialize report (handle timestamps)
        def convert_timestamps(obj):
            if hasattr(obj, 'strftime'):
                return obj.strftime('%Y-%m-%d')
            if isinstance(obj, dict):
                return {k: convert_timestamps(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_timestamps(item) for item in obj]
            return obj
            
        clean_report = convert_timestamps(report)
        
        # Save Report
        with open(REPORT_FILE, "w") as f:
            json.dump(clean_report, f, indent=2)
            
        # 2. Run AI Analysis
        # Note: This might be slow, so maybe we want to cache or run in background?
        # For now, run synchronously or use cached if recent?
        # Let's run it every time for simplicity, or check if insights exist?
        # The user might want fresh insights.
        
        agent = FinancialInsightsAgent(provider=config.AI_PROVIDER)
        insights = agent.generate_insights(clean_report)
        
        with open(INSIGHTS_FILE, "w") as f:
            f.write(insights)
            
        return {
            "report": clean_report,
            "insights": insights
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    """Chat with the financial agent about the data"""
    if not REPORT_FILE.exists():
        # If no report, maybe try to generate it?
        # Or just tell user to analyze first.
         raise HTTPException(status_code=404, detail="Analysis report not found. Please Run Analysis first.")
    
    try:
        report = load_stored_report()
        agent = FinancialInsightsAgent(provider=config.AI_PROVIDER)
        answer = agent.answer_question(request.message, report)
        return ChatResponse(response=answer)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
