import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# Configuration
NUM_BUSINESSES = 100
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2023, 12, 31)
DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/raw')

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_businesses(n):
    return [f"SME-{i:03d}" for i in range(1, n + 1)]

def generate_transactions(businesses):
    print("Generating transactions...")
    transactions = []
    
    for business_id in businesses:
        # Assign random business characteristics
        daily_vol = np.random.randint(1, 10) # Transactions per day
        avg_amt = np.random.uniform(5000, 50000)
        volatility = np.random.uniform(0.1, 0.5)
        
        current_date = START_DATE
        while current_date <= END_DATE:
            # Skip some random days (business closed)
            if random.random() < 0.1:
                current_date += timedelta(days=1)
                continue
                
            num_txns = np.random.poisson(daily_vol)
            
            for _ in range(num_txns):
                # 80% inflows (sales), 20% outflows (expenses)
                if random.random() < 0.8:
                    txn_type = "Sales"
                    amount = max(100, np.random.normal(avg_amt, avg_amt * volatility))
                else:
                    txn_type = random.choice(["Utility", "Inventory", "Rent", "Salary"])
                    amount = -max(100, np.random.normal(avg_amt * 0.5, avg_amt * 0.2))
                
                channel = random.choice(["POS", "Transfer", "Cash", "Online"])
                
                transactions.append({
                    "business_id": business_id,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "amount": round(amount, 2),
                    "transaction_type": txn_type,
                    "channel": channel
                })
            
            current_date += timedelta(days=1)
            
    return pd.DataFrame(transactions)

def generate_ad_spend(businesses):
    print("Generating ad spend...")
    data = []
    platforms = ["Instagram", "Facebook", "Google"]
    
    for business_id in businesses:
        # Not all businesses advertise
        if random.random() < 0.3:
            continue
            
        current_date = START_DATE
        while current_date <= END_DATE:
            # Weekly ads
            if current_date.weekday() == 0: # Mondays
                spend = np.random.uniform(1000, 20000)
                # ROI signal: correlates with 'good' businesses later
                roi_factor = np.random.uniform(0.5, 3.0) 
                
                data.append({
                    "business_id": business_id,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "platform": random.choice(platforms),
                    "spend_amount": round(spend, 2),
                    "impressions": int(spend * np.random.uniform(10, 50)),
                    "clicks": int(spend * np.random.uniform(0.5, 2)),
                    "conversions": int(spend * np.random.uniform(0.01, 0.1) * roi_factor)
                })
            current_date += timedelta(days=1)
            
    return pd.DataFrame(data)

def generate_loan_performance(businesses, transactions_df):
    print("Generating loan performance targets...")
    loans = []
    
    # Calculate simple aggregate metrics to determine 'ground truth' risk
    # This ensures our model actually has a signal to learn
    biz_stats = transactions_df.groupby('business_id')['amount'].sum()
    
    for i, business_id in enumerate(businesses):
        # Create 1-3 loans per business
        num_loans = random.randint(1, 3)
        
        # Determine inherent risk based on net cash flow (ground truth)
        net_flow = biz_stats.get(business_id, 0)
        inherent_risk = 1.0 if net_flow < 0 else 0.2 # low risk if positive flow
        
        for j in range(num_loans):
            loan_id = f"LN-{business_id.split('-')[1]}-{j}"
            principal = np.random.choice([500000, 1000000, 2000000, 5000000])
            
            disb_date = START_DATE + timedelta(days=np.random.randint(0, 180))
            due_date = disb_date + timedelta(days=90) # 3 month tenor
            
            # Simulate default probability
            # If net flow is bad, high chance of default
            is_default = random.random() < inherent_risk
            
            status = "Default" if is_default else "Repaid"
            repaid_date = due_date - timedelta(days=np.random.randint(0, 10)) if not is_default else None
            
            loans.append({
                "loan_id": loan_id,
                "business_id": business_id,
                "disbursement_date": disb_date.strftime("%Y-%m-%d"),
                "principal_amount": principal,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "repaid_date": repaid_date.strftime("%Y-%m-%d") if repaid_date else None,
                "status": status
            })
            
    return pd.DataFrame(loans)

def main():
    np.random.seed(42)
    random.seed(42)
    
    ensure_dir(DATA_DIR)
    
    businesses = generate_businesses(NUM_BUSINESSES)
    
    df_trans = generate_transactions(businesses)
    df_ads = generate_ad_spend(businesses)
    df_loans = generate_loan_performance(businesses, df_trans)
    
    # Save to CSV
    trans_path = os.path.join(DATA_DIR, 'transactions.csv')
    ads_path = os.path.join(DATA_DIR, 'ad_spend.csv')
    loans_path = os.path.join(DATA_DIR, 'loan_performance.csv')
    
    df_trans.to_csv(trans_path, index=False)
    df_ads.to_csv(ads_path, index=False)
    df_loans.to_csv(loans_path, index=False)
    
    print(f"Dataset generated at {DATA_DIR}")
    print(f"- Transactions: {len(df_trans)} rows")
    print(f"- Ad Spend: {len(df_ads)} rows")
    print(f"- Loans: {len(df_loans)} rows")

if __name__ == "__main__":
    main()
