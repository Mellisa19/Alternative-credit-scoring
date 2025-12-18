import pandas as pd
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.decision_engine import CreditDecisionEngine
from src.data.loader import DataLoader
from src.features.engineering import FeatureEngineer

def validate_risk_tiers():
    print("\n=== 1. Risk Tier Validation ===")
    
    # 1. Load historical data
    loader = DataLoader()
    t, a, l = loader.load_all()
    
    # 2. Re-engineer features to get the "Actual" state
    fe = FeatureEngineer()
    df = fe.build_dataset(t, a, l)
    
    # 3. Score everyone using Decision Engine
    # (We bypass the API wrapper for bulk processing efficiency, but use same logic)
    engine = CreditDecisionEngine()
    
    # Predict
    X = df.drop('is_default', axis=1)
    
    # Align features
    if hasattr(engine.model.named_steps['clf'], 'feature_names_in_'):
         cols = engine.model.named_steps['clf'].feature_names_in_
         X = X.reindex(columns=cols, fill_value=0)
    
    probs = engine.model.predict_proba(X)[:, 0] # Prob(Repay)
    scores = (probs * 100).astype(int)
    
    # Create Analysis DataFrame
    analysis = pd.DataFrame({
        'credit_score': scores,
        'actual_default': df['is_default'],
        'actual_repayment': 1 - df['is_default']
    })
    
    # Apply Tier Logic
    def get_tier(s):
        if s >= 70: return 'Low Risk'
        if s >= 50: return 'Medium Risk'
        return 'High Risk'
        
    analysis['risk_tier'] = analysis['credit_score'].apply(get_tier)
    
    # Group by Risk Tier
    tier_stats = analysis.groupby('risk_tier').agg(
        count=('actual_default', 'count'),
        default_rate=('actual_default', 'mean'),
        repayment_rate=('actual_repayment', 'mean'),
        avg_score=('credit_score', 'mean')
    ).reindex(['Low Risk', 'Medium Risk', 'High Risk']) # Sort
    
    print(tier_stats)
    
    # Validation Checks
    print("\n--- Logic Checks ---")
    
    low_def = tier_stats.loc['Low Risk', 'default_rate']
    high_def = tier_stats.loc['High Risk', 'default_rate']
    
    if low_def < high_def:
        print("[PASS] Low Risk tier has lower default rate than High Risk tier.")
    else:
        print("[FAIL] Logic Inversion: Low Risk tier has higher/equal default rate!")

    return analysis

def run_stress_tests():
    print("\n=== 2. Stress Testing (Synthetic Scenarios) ===")
    
    engine = CreditDecisionEngine()
    
    scenarios = [
        {
            "name": "High Spend, Low Revenue (The 'Burner')",
            "data": {
                "transactions": [
                    {"date": "2023-01-01", "amount": 1000, "transaction_type": "Sales"},
                    {"date": "2023-01-02", "amount": -5000, "transaction_type": "Expense"}, # Net -4000
                ],
                "ad_spend": [
                    {"date": "2023-01-01", "spend_amount": 3000, "clicks": 100, "conversions": 1} # Terrible ROI
                ]
            }
        },
        {
            "name": "Stable Revenue, Zero Ads (The 'Organic' Small Shop)",
            "data": {
                "transactions": [
                    {"date": "2023-01-01", "amount": 5000, "transaction_type": "Sales"},
                    {"date": "2023-01-02", "amount": -2000, "transaction_type": "Expense"},
                    {"date": "2023-01-03", "amount": 5000, "transaction_type": "Sales"},
                ],
                "ad_spend": [] # Zero ads
            }
        },
        {
            "name": "High Volume, Thin Margins (The 'Busy' Trader)",
            "data": {
                "transactions": [
                    {"date": "2023-01-01", "amount": 10000, "transaction_type": "Sales"},
                    {"date": "2023-01-01", "amount": -9800, "transaction_type": "Expense"}, # 200 profit
                    {"date": "2023-01-02", "amount": 10000, "transaction_type": "Sales"},
                    {"date": "2023-01-02", "amount": -9800, "transaction_type": "Expense"},
                ],
                "ad_spend": []
            }
        },
        {
             "name": "Sudden Cash Flow Drop (The 'Crasher')",
             "data": {
                 "transactions": [
                     {"date": "2023-01-01", "amount": 10000, "transaction_type": "Sales"},
                     {"date": "2023-01-02", "amount": 10000, "transaction_type": "Sales"},
                     {"date": "2023-01-03", "amount": -500, "transaction_type": "Expense"},
                     # Volatility calculated on amounts. If we add a huge negative or just low sales?
                     # Let's add extreme volatility
                     {"date": "2023-01-04", "amount": 100, "transaction_type": "Sales"}, 
                 ],
                 "ad_spend": []
             }
        }
    ]
    
    print(f"{'Scenario':<40} | {'Score':<5} | {'Tier':<12} | {'Summary'}")
    print("-" * 100)
    
    for sc in scenarios:
        result = engine.credit_decision(sc['data'])
        print(f"{sc['name']:<40} | {result['credit_score']:<5} | {result['risk_tier']:<12} | {result['decision_summary'][:50]}...")
        
if __name__ == "__main__":
    validate_risk_tiers()
    run_stress_tests()
