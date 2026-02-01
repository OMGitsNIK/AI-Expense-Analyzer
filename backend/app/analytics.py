"""
Financial Analytics Engine
Performs quantitative analysis on transaction data
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
import re


class FinancialAnalyzer:
    """Analyzes bank statement transactions"""
    
    def __init__(self, transactions_json_path: str):
        """Load transactions from JSON file"""
        with open(transactions_json_path, 'r') as f:
            data = json.load(f)
        
        self.statement_data = data
        self.transactions = data['transactions']
        self.df = pd.DataFrame(self.transactions)
        
        # Convert date strings to datetime
        self.df['date'] = pd.to_datetime(self.df['date'], format='%d/%m/%Y', errors='coerce')
        
        # Fill NaN values
        self.df['withdrawal'] = self.df['withdrawal'].fillna(0)
        self.df['deposit'] = self.df['deposit'].fillna(0)
    
    def categorize_transactions(self) -> pd.DataFrame:
        """
        Auto-categorize transactions using keyword matching.
        Returns DataFrame with added 'category' column.
        """
        categories = {
            'Food & Dining': ['swiggy', 'zomato', 'restaurant', 'food', 'cafe', 'domino', 'mcdonald', 'kfc'],
            'Shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'shop', 'mall', 'store'],
            'Transportation': ['uber', 'ola', 'rapido', 'petrol', 'fuel', 'parking'],
            'Utilities': ['electricity', 'water', 'gas', 'internet', 'mobile', 'recharge', 'jio', 'airtel'],
            'Investment': ['groww', 'zerodha', 'upstox', 'mutual fund', 'sip', 'investment'],
            'Entertainment': ['netflix', 'prime', 'hotstar', 'spotify', 'movie', 'theatre', 'book'],
            'Healthcare': ['medical', 'pharmacy', 'hospital', 'doctor', 'medicine', 'health'],
            'Transfer': ['neft', 'imps', 'rtgs', 'transfer', 'upi-.*rao'],
            'Salary': ['salary', 'nextbillion', 'payroll'],
            'Bills': ['bill', 'payment', 'autopay'],
            'Other': []
        }
        
        def categorize(description: str) -> str:
            if pd.isna(description):
                return 'Other'
            
            desc_lower = description.lower()
            
            for category, keywords in categories.items():
                if category == 'Other':
                    continue
                for keyword in keywords:
                    if keyword in desc_lower:
                        return category
            
            return 'Other'
        
        self.df['category'] = self.df['description'].apply(categorize)
        return self.df
    
    def spending_by_category(self) -> Dict[str, float]:
        """Calculate total spending per category"""
        if 'category' not in self.df.columns:
            self.categorize_transactions()
        
        spending = self.df.groupby('category')['withdrawal'].sum().to_dict()
        return {k: round(v, 2) for k, v in spending.items() if v > 0}
    
    def top_expenses(self, n: int = 10) -> List[Dict]:
        """Get top N expenses"""
        top = self.df.nlargest(n, 'withdrawal')[['date', 'description', 'withdrawal']]
        return top.to_dict('records')
    
    def recurring_payments(self) -> List[Dict]:
        """Detect recurring payments (same merchant, regular intervals)"""
        # Group by similar descriptions
        recurring = []
        
        for desc in self.df['description'].unique():
            if pd.isna(desc):
                continue
            
            # Extract merchant name (before @ or first 30 chars)
            merchant = desc.split('@')[0][:30]
            matching = self.df[self.df['description'].str.contains(merchant, case=False, na=False)]
            
            if len(matching) >= 2:  # At least 2 occurrences
                total = matching['withdrawal'].sum()
                avg = matching['withdrawal'].mean()
                
                if total > 0:  # Only withdrawals
                    recurring.append({
                        'merchant': merchant,
                        'frequency': len(matching),
                        'total_spent': round(total, 2),
                        'avg_amount': round(avg, 2)
                    })
        
        # Sort by total spent
        return sorted(recurring, key=lambda x: x['total_spent'], reverse=True)[:10]
    
    def monthly_summary(self) -> Dict:
        """Calculate monthly financial summary"""
        total_income = self.df['deposit'].sum()
        total_expenses = self.df['withdrawal'].sum()
        net_change = total_income - total_expenses
        
        opening = self.statement_data.get('opening_balance', 0)
        closing = self.statement_data.get('closing_balance', 0)
        
        return {
            'total_income': round(total_income, 2),
            'total_expenses': round(total_expenses, 2),
            'net_change': round(net_change, 2),
            'opening_balance': opening,
            'closing_balance': closing,
            'avg_daily_spending': round(total_expenses / len(self.df['date'].unique()), 2),
            'savings_rate': round((total_income - total_expenses) / total_income * 100, 2) if total_income > 0 else 0
        }
    
    def unusual_transactions(self, threshold_multiplier: float = 3.0) -> List[Dict]:
        """Detect unusually large transactions"""
        mean_withdrawal = self.df['withdrawal'].mean()
        std_withdrawal = self.df['withdrawal'].std()
        
        threshold = mean_withdrawal + (threshold_multiplier * std_withdrawal)
        
        unusual = self.df[self.df['withdrawal'] > threshold][['date', 'description', 'withdrawal']]
        return unusual.to_dict('records')
    
    def spending_trend(self) -> Dict[str, float]:
        """Calculate daily spending trend"""
        daily = self.df.groupby(self.df['date'].dt.date)['withdrawal'].sum()
        return {str(date): round(amount, 2) for date, amount in daily.items()}
    
    def generate_full_report(self) -> Dict:
        """Generate comprehensive financial report"""
        self.categorize_transactions()
        
        return {
            'summary': self.monthly_summary(),
            'spending_by_category': self.spending_by_category(),
            'top_expenses': self.top_expenses(10),
            'recurring_payments': self.recurring_payments(),
            'unusual_transactions': self.unusual_transactions(),
            'spending_trend': self.spending_trend(),
            'transaction_count': len(self.df),
            'analysis_period': {
                'from': self.statement_data.get('statement_period_from'),
                'to': self.statement_data.get('statement_period_to')
            }
        }


# Quick test function
if __name__ == "__main__":
    analyzer = FinancialAnalyzer('transactions.json')
    report = analyzer.generate_full_report()
    
    print("\n" + "="*70)
    print("📊 FINANCIAL ANALYSIS REPORT")
    print("="*70)
    
    summary = report['summary']
    print(f"\n💰 Summary:")
    print(f"   Income: ₹{summary['total_income']}")
    print(f"   Expenses: ₹{summary['total_expenses']}")
    print(f"   Net: ₹{summary['net_change']}")
    print(f"   Savings Rate: {summary['savings_rate']}%")
    
    print(f"\n📂 Spending by Category:")
    for cat, amount in sorted(report['spending_by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: ₹{amount}")
    
    print(f"\n🔁 Recurring Payments:")
    for payment in report['recurring_payments'][:5]:
        print(f"   {payment['merchant']}: ₹{payment['total_spent']} ({payment['frequency']}x)")