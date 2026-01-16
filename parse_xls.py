import pandas as pd
import json
import re


def parse_bank_statement_xls(xls_path: str) -> dict:
    """
    Parse HDFC Bank statement XLS file into structured JSON.
    
    Args:
        xls_path: Path to the XLS file
        
    Returns:
        Dictionary with account info and transactions
    """
    
    print(f"📂 Reading {xls_path}...")
    
    # Read the Excel file
    df_raw = pd.read_excel(xls_path)
    
    print(f"📊 File has {len(df_raw)} rows and {len(df_raw.columns)} columns")
    
    # Find where the transaction data starts
    start_row = None
    for idx, row in df_raw.iterrows():
        row_str = ' '.join(str(x) for x in row.values if pd.notna(x))
        if 'Date' in row_str and 'Narration' in row_str:
            start_row = idx + 1
            print(f"✅ Found transaction header at row {idx}")
            break
    
    if start_row is None:
        raise ValueError("Could not find transaction data in XLS")
    
    # Read again, skipping header rows
    df = pd.read_excel(xls_path, skiprows=start_row)
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Column mapping
    column_mapping = {
        'Date': 'date',
        'Narration': 'description',
        'Chq./Ref.No.': 'cheque_ref_no',
        'Value Dt': 'value_date',
        'Withdrawal Amt.': 'withdrawal',
        'Deposit Amt.': 'deposit',
        'Closing Balance': 'balance'
    }
    
    df = df.rename(columns=column_mapping)
    
    print(f"🔄 Mapped columns: {df.columns.tolist()}\n")
    
    # Clean up the data - remove summary rows
    df = df[df['date'].notna()].copy()
    df = df[~df['date'].astype(str).str.contains(
        'Opening Balance|STATEMENT SUMMARY|Generated|Continue|Page No', 
        na=False, 
        case=False
    )]
    
    # Remove rows with dashes (page separators)
    df = df[~df['date'].astype(str).str.match(r'^-+$')]
    
    print(f"✅ Found {len(df)} transactions after cleanup\n")
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%y', errors='coerce')
    
    # Drop rows where date conversion failed
    df = df[df['date'].notna()]
    
    # Convert amounts to float - HDFC uses commas in numbers
    for col in ['withdrawal', 'deposit', 'balance']:
        if col in df.columns:
            # Replace commas, handle empty strings
            df[col] = df[col].astype(str).str.replace(',', '').str.strip()
            df[col] = df[col].replace(['', 'nan', 'NaN'], None)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Format dates as strings for JSON
    df['date'] = df['date'].dt.strftime('%d/%m/%Y')
    
    # Extract account information from header
    raw_df = pd.read_excel(xls_path, nrows=30)
    
    account_info = {
        "account_holder": None,
        "account_number": None,
        "bank_name": "HDFC Bank",
        "branch": None,
        "statement_period_from": None,
        "statement_period_to": None,
        "currency": "INR"
    }
    
    # Parse account info from header
    for idx, row in raw_df.iterrows():
        # Get all non-null values in the row
        values = [str(x) for x in row.values if pd.notna(x)]
        row_str = ' '.join(values)
        
        # Extract account holder - usually starts with MR./MRS./MS.
        if idx < 10 and any(prefix in row_str for prefix in ['MR.', 'MRS.', 'MS.']):
            # Clean up the name
            name_parts = []
            for val in values:
                val = str(val).strip()
                if val and not val.startswith('HDFC') and len(val) > 2:
                    name_parts.append(val)
            if name_parts:
                account_info['account_holder'] = ' '.join(name_parts[:4])  # First 4 parts
        
        # Extract account number
        if 'Account No' in row_str:
            match = re.search(r'(\d{14})', row_str)
            if match:
                account_info['account_number'] = match.group(1)
        
        # Extract branch
        if 'Account Branch' in row_str:
            match = re.search(r'Account Branch\s*:\s*([A-Z\s]+?)(?:Address|$)', row_str)
            if match:
                account_info['branch'] = match.group(1).strip()
        
        # Extract statement period
        if 'Statement From' in row_str:
            match = re.search(r'(\d{2}/\d{2}/\d{4})\s+To[:\s]+(\d{2}/\d{2}/\d{4})', row_str)
            if match:
                account_info['statement_period_from'] = match.group(1)
                account_info['statement_period_to'] = match.group(2)
    
    # Calculate opening and closing balances
    opening_balance = None
    closing_balance = None
    
    if not df.empty:
        # Get first and last transactions with valid balance
        df_with_balance = df[df['balance'].notna()]
        
        if not df_with_balance.empty:
            first_txn = df_with_balance.iloc[0]
            
            # Calculate opening balance
            if pd.notna(first_txn.get('withdrawal')):
                opening_balance = first_txn['balance'] + first_txn['withdrawal']
            elif pd.notna(first_txn.get('deposit')):
                opening_balance = first_txn['balance'] - first_txn['deposit']
            else:
                opening_balance = first_txn['balance']
            
            # Get closing balance
            closing_balance = df_with_balance.iloc[-1]['balance']
    
    account_info['opening_balance'] = opening_balance
    account_info['closing_balance'] = closing_balance
    
    # Convert DataFrame to list of transaction dicts
    # Replace NaN with None for clean JSON
    transactions = []
    for _, row in df.iterrows():
        txn = {
            'date': row['date'],
            'description': row.get('description'),
            'cheque_ref_no': row.get('cheque_ref_no'),
            'value_date': row.get('value_date'),
            'withdrawal': None if pd.isna(row.get('withdrawal')) else float(row.get('withdrawal')),
            'deposit': None if pd.isna(row.get('deposit')) else float(row.get('deposit')),
            'balance': None if pd.isna(row.get('balance')) else float(row.get('balance'))
        }
        transactions.append(txn)
    
    # Build final structure
    statement_data = {
        **account_info,
        "transactions": transactions
    }
    
    return statement_data


if __name__ == "__main__":
    xls_file = "invoice_excel.xls"
    
    try:
        data = parse_bank_statement_xls(xls_file)
        
        # Save to JSON
        with open("transactions.json", "w") as f:
            json.dump(data, f, indent=2)
        
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"📊 Parsed {len(data['transactions'])} transactions")
        print(f"👤 Account Holder: {data.get('account_holder', 'N/A')}")
        print(f"🏦 Account Number: {data.get('account_number', 'N/A')}")
        print(f"🏢 Branch: {data.get('branch', 'N/A')}")
        print(f"📅 Period: {data['statement_period_from']} to {data['statement_period_to']}")
        
        if data['opening_balance'] is not None:
            print(f"💰 Opening: ₹{data['opening_balance']:,.2f}")
        else:
            print("💰 Opening: N/A")
            
        if data['closing_balance'] is not None:
            print(f"💰 Closing: ₹{data['closing_balance']:,.2f}")
        else:
            print("💰 Closing: N/A")
            
        print(f"💾 Saved to transactions.json")
        
        # Show sample transactions
        print("\n📝 Sample transactions:")
        for i, txn in enumerate(data['transactions'][:3], 1):
            print(f"\n  {i}. {txn['date']}: {txn['description'][:50]}")
            if txn['withdrawal']:
                print(f"     Withdrawal: ₹{txn['withdrawal']:,.2f}")
            if txn['deposit']:
                print(f"     Deposit: ₹{txn['deposit']:,.2f}")
            print(f"     Balance: ₹{txn['balance']:,.2f}" if txn['balance'] else "     Balance: N/A")
        
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()