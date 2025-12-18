import pandas as pd
import os
from typing import Dict, Tuple

class DataLoader:
    """
    Handles loading and basic validation of the credit scoring datasets.
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Default to project_root/data/raw
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'raw')
        else:
            self.data_dir = data_dir
            
    def load_transactions(self) -> pd.DataFrame:
        """Loads and validates transactions data."""
        path = os.path.join(self.data_dir, 'transactions.csv')
        if not os.path.exists(path):
            raise FileNotFoundError(f"transactions.csv not found at {path}")
            
        df = pd.read_csv(path)
        required_cols = ['business_id', 'date', 'amount', 'transaction_type', 'channel']
        self._validate_columns(df, required_cols, 'transactions.csv')
        
        # Type conversion
        df['date'] = pd.to_datetime(df['date'])
        return df

    def load_ad_spend(self) -> pd.DataFrame:
        """Loads and validates ad spend data."""
        path = os.path.join(self.data_dir, 'ad_spend.csv')
        if not os.path.exists(path):
            raise FileNotFoundError(f"ad_spend.csv not found at {path}")
            
        df = pd.read_csv(path)
        required_cols = ['business_id', 'date', 'platform', 'spend_amount', 'impressions', 'clicks', 'conversions']
        self._validate_columns(df, required_cols, 'ad_spend.csv')
        
        df['date'] = pd.to_datetime(df['date'])
        return df

    def load_loan_performance(self) -> pd.DataFrame:
        """Loads and validates loan performance data (target)."""
        path = os.path.join(self.data_dir, 'loan_performance.csv')
        if not os.path.exists(path):
            raise FileNotFoundError(f"loan_performance.csv not found at {path}")
            
        df = pd.read_csv(path)
        required_cols = ['loan_id', 'business_id', 'disbursement_date', 'principal_amount', 'due_date', 'repaid_date', 'status']
        self._validate_columns(df, required_cols, 'loan_performance.csv')
        
        df['disbursement_date'] = pd.to_datetime(df['disbursement_date'])
        df['due_date'] = pd.to_datetime(df['due_date'])
        # repaid_date can be NaT
        df['repaid_date'] = pd.to_datetime(df['repaid_date'])
        return df
        
    def _validate_columns(self, df: pd.DataFrame, required: list, filename: str):
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in {filename}: {missing}")

    def load_all(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Helper to load all three datasets at once."""
        return self.load_transactions(), self.load_ad_spend(), self.load_loan_performance()

if __name__ == "__main__":
    # simple test
    loader = DataLoader()
    try:
        t, a, l = loader.load_all()
        print(f"Successfully loaded data:")
        print(f"Transactions: {t.shape}")
        print(f"Ad Spend: {a.shape}")
        print(f"Loans: {l.shape}")
        print(t.head())
    except Exception as e:
        print(f"Error loading data: {e}")
