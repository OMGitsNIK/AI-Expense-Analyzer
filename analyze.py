"""
Main script to analyze bank statements
"""

import sys
import json
import pandas as pd
from analytics import FinancialAnalyzer
from ai_insights import FinancialInsightsAgent


def load_transactions():
    """Load transactions from the JSON file created by main.py"""
    try:
        with open('transactions.json', 'r') as f:
            data = json.load(f)
        
        # Extract transactions from the bank statement data
        transactions = data.get('transactions', [])
        
        if not transactions:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Convert date strings to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
        
        return df
        
    except FileNotFoundError:
        print("❌ transactions.json not found. Please run main.py first to extract data.")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error loading transactions: {e}")
        return pd.DataFrame()


def main():
    print("\n🧮 Starting Financial Analysis...")
    print("="*70)

    # Load transactions
    transactions = load_transactions()
    
    if transactions.empty:
        print("❌ No transactions found. Please run main.py first to extract data.")
        return
    
    # Step 1: Quantitative Analysis
    print("\n📊 Running quantitative analysis...")
    analyzer = FinancialAnalyzer('transactions.json')
    report = analyzer.generate_full_report()
    
    summary = report['summary']
    print(f"\n✅ Analysis complete!")
    print(f"   Processed {report['transaction_count']} transactions")
    print(f"   Period: {report['analysis_period']['from']} to {report['analysis_period']['to']}")
    print(f"   Net change: ₹{summary['net_change']}")
    
    # Convert timestamps to strings for JSON serialization
    def convert_timestamps(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, dict):
            return {k: convert_timestamps(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_timestamps(item) for item in obj]
        return obj
    
    clean_report = convert_timestamps(report)

    # Step 2: AI Insights
    print("\n🤖 Generating AI-powered insights...")
    print("   (This may take 10-20 seconds...)")
    
    agent = FinancialInsightsAgent(provider="groq")  # or "claude", "openai"
    insights = agent.generate_insights(clean_report)
    
    # Save results
    with open("financial_insights.md", "w") as f:
        f.write(insights)
    
    with open("financial_report.json", "w") as f:
        json.dump(clean_report, f, indent=2)
    
    print("\n" + "="*70)
    print(insights)
    print("="*70)
    
    print("\n💾 Results saved:")
    print("   - financial_insights.md (AI insights)")
    print("   - financial_report.json (Full analytics)")
    
    # Interactive Q&A
    print("\n" + "="*70)
    print("💬 Ask questions about your finances (or 'quit' to exit)")
    print("="*70)
    
    while True:
        question = input("\n❓ Your question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if not question:
            continue
        
        answer = agent.answer_question(question, clean_report)
        print(f"\n💡 {answer}\n")
    
    print("\n✨ Analysis complete!\n")


if __name__ == "__main__":
    main()