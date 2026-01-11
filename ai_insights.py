"""
AI-Powered Financial Insights Generator
Uses Claude/OpenAI to generate natural language insights from analytics
"""

import json
from typing import Dict, Optional
import os
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class FinancialInsightsAgent:
    """Generates human-readable financial insights using AI"""
    
    def __init__(self, provider: str = "claude"):
        """
        Initialize AI agent
        
        Args:
            provider: 'claude', 'openai', or 'groq'
        """
        self.provider = provider
        
        if provider == "claude":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-sonnet-4-20250514"
        elif provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4o-mini"
        elif provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = "openai/gpt-oss-120b"
    
    def generate_insights(self, financial_report: Dict) -> str:
        """
        Generate natural language insights from financial report
        
        Args:
            financial_report: Output from FinancialAnalyzer.generate_full_report()
            
        Returns:
            Formatted markdown insights
        """
        
        prompt = f"""You are a personal financial advisor analyzing a client's bank statement.

Here is the financial data:

{json.dumps(financial_report, indent=2)}

Provide a comprehensive financial analysis in markdown format with these sections:

1. **Executive Summary** (2-3 sentences overview)
2. **Key Insights** (3-5 bullet points of most important findings)
3. **Spending Breakdown** (analysis of category spending)
4. **Recurring Payments** (identify subscriptions and regular expenses)
5. **Unusual Activity** (flag any concerning transactions)
6. **Recommendations** (3-5 actionable suggestions to improve financial health)
7. **Financial Forecast** (predict next month based on current patterns)

Be specific with numbers, percentages, and actionable advice.
Tone: Friendly but professional, like a financial advisor talking to a friend.
"""
        
        if self.provider == "claude":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        
        elif self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    
    def answer_question(self, question: str, financial_report: Dict) -> str:
        """
        Answer specific questions about finances
        
        Example questions:
        - "How much did I spend on food this month?"
        - "What are my biggest expenses?"
        - "Am I saving enough?"
        """
        
        prompt = f"""You are a financial advisor with access to the following financial data:

{json.dumps(financial_report, indent=2)}

User question: {question}

Provide a clear, specific answer based on the data. Include numbers and percentages where relevant.
"""
        
        if self.provider == "claude":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        
        elif self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content


# Example usage
if __name__ == "__main__":
    from analytics import FinancialAnalyzer
    
    # Generate analytics
    analyzer = FinancialAnalyzer('transactions.json')
    report = analyzer.generate_full_report()
    
    # Generate AI insights
    agent = FinancialInsightsAgent(provider="claude")
    insights = agent.generate_insights(report)
    
    print(insights)
    
    # Save to file
    with open("financial_insights.md", "w") as f:
        f.write(insights)
    
    print("\n💾 Insights saved to financial_insights.md")