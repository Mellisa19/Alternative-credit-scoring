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

def analyze_fairness():
    print("\n=== Fairness & Bias Analysis ===")
    
    # 1. Load Data
    loader = DataLoader()
    t, a, l = loader.load_all()
    fe = FeatureEngineer()
    df = fe.build_dataset(t, a, l)
    
    # 2. Score Everyone
    engine = CreditDecisionEngine()
    X = df.drop('is_default', axis=1)
    
    # Align features
    if hasattr(engine.model.named_steps['clf'], 'feature_names_in_'):
         cols = engine.model.named_steps['clf'].feature_names_in_
         X = X.reindex(columns=cols, fill_value=0)
         
    probs = engine.model.predict_proba(X)[:, 1] # Prob(Default) -> No, trained on is_default=1
    # Wait, in validation I used predict_proba[:, 0] as Prob(Repay) ??
    # Let's check train.py.
    # y = data['is_default']. 1 = Default, 0 = Repaid.
    # model.predict_proba returns [prob_0, prob_1].
    # So index 0 is Repayment, index 1 is Default.
    # High score should be High Repayment Prob.
    
    prob_repay = engine.model.predict_proba(X)[:, 0]
    scores = (prob_repay * 100).astype(int)
    
    results = df.copy()
    results['credit_score'] = scores
    results['approved'] = results['credit_score'] >= 50 # Threshold for Medium Risk+
    results['actual_good'] = (results['is_default'] == 0)
    
    # 3. Define Proxy Groups
    print("Defining sensitive groups...")
    
    # A. Business Size (Revenue)
    # Micro < 25th percentile
    revenue_threshold = results['total_inflow'].quantile(0.25)
    results['group_size'] = np.where(results['total_inflow'] <= revenue_threshold, 'Micro', 'Active')
    
    # B. Digital Presence (Ad Spend)
    # Non-Digital = 0 Ad Spend
    results['group_digital'] = np.where(results['ad_spend_total'] > 0, 'Digital', 'Non-Digital')
    
    # 4. Calculate Metrics per Group
    groups = {
        'Business Size': 'group_size',
        'Digital Presence': 'group_digital'
    }
    
    report = []
    
    for name, col in groups.items():
        print(f"\n--- Analyzing {name} ---")
        report.append(f"\n### {name} Bias Analysis")
        
        # Group stats
        # business_id is likely the index, so we count the index or 'total_inflow' (always present)
        stats = results.groupby(col).agg(
            total=('total_inflow', 'count'), # Count any non-null column
            approval_rate=('approved', 'mean'),
            avg_score=('credit_score', 'mean'),
            actual_repayment_rate=('actual_good', 'mean')
        )
        
        print(stats)
        
        # Calculate Logic Errors (Fairness)
        # False Positive Rate (FPR): We approved them, but they defaulted (Financial Risk)
        # False Negative Rate (FNR): We rejected them, but they were actually good (Fairness Risk / Opportunity Cost)
        
        # We need a custom aggregation for FNR
        # FNR = (Rejected & Good) / Total Good
        
        parity_metrics = []
        
        # Iterate subgroups
        for group_name in stats.index:
            sub = results[results[col] == group_name]
            total_good = sub['actual_good'].sum()
            rejected_good = sub[(~sub['approved']) & (sub['actual_good'])].shape[0]
            
            fnr = rejected_good / total_good if total_good > 0 else 0.0
            
            # Disparate Impact (Ratio of approval rates)
            # Reference group is usually the "privileged" one.
            # We'll just list the raw metrics.
            
            metrics = f"- **{group_name}**: Avg Score {stats.loc[group_name, 'avg_score']:.1f}, Approval Rate {stats.loc[group_name, 'approval_rate']:.1%}, Rejection Error (Good but Rejected): {fnr:.1%}"
            print(metrics)
            report.append(metrics)
            parity_metrics.append({'group': group_name, 'rate': stats.loc[group_name, 'approval_rate']})
            
        # Statistical Parity Gap
        if len(stats) == 2:
            gap = parity_metrics[0]['rate'] - parity_metrics[1]['rate']
            warn = "⚠️ Significant Disparity" if abs(gap) > 0.1 else "✅ Balanced"
            summary_str = f"Approval Gap: {gap:.1%} ({warn})"
            print(summary_str)
            report.append(summary_str)
            
    # Save Report
    with open('reports/fairness_check.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
        
if __name__ == "__main__":
    analyze_fairness()
