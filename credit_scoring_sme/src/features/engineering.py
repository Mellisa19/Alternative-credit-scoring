import pandas as pd
import numpy as np
from typing import List

class FeatureEngineer:
    """
    Transforms raw data into features for the credit scoring model.
    """
    
    def __init__(self):
        pass
    
    def preprocess_transactions(self, df_trans: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates transaction data to business level.
        Expected features:
        - Total Inflow/Outflow
        - Net Cash Flow
        - Cash Flow Volatility (Std Dev)
        - Transaction Count
        - Average Transaction Value
        """
        # Ensure date is sorted
        df = df_trans.sort_values(['business_id', 'date'])
        
        # Split inflows and outflows
        inflows = df[df['amount'] > 0]
        outflows = df[df['amount'] < 0]
        
        # 1. Basic Aggregates
        feats = df.groupby('business_id').agg(
            txn_count=('amount', 'count'),
            net_cash_flow=('amount', 'sum'),
            txn_volatility=('amount', 'std')
        ).reset_index()
        
        # 2. Inflow specific
        inflow_stats = inflows.groupby('business_id').agg(
            total_inflow=('amount', 'sum'),
            avg_inflow=('amount', 'mean')
        ).reset_index()
        
        # 3. Outflow specific (absolute values for easier interpretation)
        outflow_stats = outflows.groupby('business_id').agg(
            total_outflow=('amount', lambda x: x.abs().sum()),
            avg_outflow=('amount', lambda x: x.abs().mean())
        ).reset_index()
        
        # Merge
        feats = feats.merge(inflow_stats, on='business_id', how='left').fillna(0)
        feats = feats.merge(outflow_stats, on='business_id', how='left').fillna(0)
        
        # 4. Burn Rate Ratio (Outflow / Inflow)
        feats['burn_rate'] = np.where(feats['total_inflow'] > 0, 
                                      feats['total_outflow'] / feats['total_inflow'], 
                                      10.0) # Penalty for no inflow
        
        return feats

    def preprocess_ad_spend(self, df_ads: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates ad spend data to business level.
        Expected features:
        - Total Spend
        - Total Conversions
        - ROI (Conversions / Spend) * Proxy Value
        - Cost Per Acquisition (Spend / Conversions)
        """
        if df_ads.empty:
            # Return empty schema if no data
            return pd.DataFrame(columns=['business_id', 'ad_spend_total', 'ad_roi', 'ad_cpa'])
            
        feats = df_ads.groupby('business_id').agg(
            ad_spend_total=('spend_amount', 'sum'),
            total_conversions=('conversions', 'sum'),
            total_clicks=('clicks', 'sum')
        ).reset_index()
        
        # ROI Proxy: Let's assume average conversion value is fixed for simplicity (e.g. $50)
        # In real life, we'd validata against transaction data, but this is a standalone signal.
        AVG_CONVERSION_VALUE = 5000.0
        
        feats['ad_revenue_est'] = feats['total_conversions'] * AVG_CONVERSION_VALUE
        feats['ad_roi'] = np.where(feats['ad_spend_total'] > 0,
                                   (feats['ad_revenue_est'] - feats['ad_spend_total']) / feats['ad_spend_total'],
                                   0)
                                   
        feats['ad_cpa'] = np.where(feats['total_conversions'] > 0,
                                   feats['ad_spend_total'] / feats['total_conversions'],
                                   feats['ad_spend_total']) # If no conversions, CPA is infinite-ish (max spend)
                                   
        return feats[['business_id', 'ad_spend_total', 'ad_roi', 'ad_cpa']]

    def create_labels(self, df_loans: pd.DataFrame) -> pd.DataFrame:
        """
        Creates target variable from loan performance.
        Binary Classification: 1 if Default, 0 if Repaid.
        If a business has ANY default, we label them as high risk (1) for now.
        """
        # Encode status
        df_loans['is_default'] = df_loans['status'].apply(lambda x: 1 if x == 'Default' else 0)
        
        # Aggregate to business level
        # Max() ensures if they defaulted once, they are flagged.
        labels = df_loans.groupby('business_id')['is_default'].max().reset_index()
        return labels

    def build_dataset(self, df_trans, df_ads, df_loans) -> pd.DataFrame:
        """
        Joins all features and labels into a single training set.
        """
        feat_trans = self.preprocess_transactions(df_trans)
        feat_ads = self.preprocess_ad_spend(df_ads)
        labels = self.create_labels(df_loans)
        
        # Master Merge
        # We only care about businesses that actually applied for loans (in labels)
        df_final = labels.merge(feat_trans, on='business_id', how='left')
        df_final = df_final.merge(feat_ads, on='business_id', how='left')
        
        # Fill NaNs for ad spend (businesses that didn't advertise get 0)
        df_final['ad_spend_total'] = df_final['ad_spend_total'].fillna(0)
        df_final['ad_roi'] = df_final['ad_roi'].fillna(0)
        # CPA is tricky, if they didn't advertise, is it 0 or high? 
        # Let's clean it by setting to a neutral value or 0 if using tree models.
        df_final['ad_cpa'] = df_final['ad_cpa'].fillna(0) 
        
        # Drop ID
        df_final = df_final.set_index('business_id')
        
        return df_final

if __name__ == "__main__":
    # Test
    from src.data.loader import DataLoader
    loader = DataLoader()
    t, a, l = loader.load_all()
    
    fe = FeatureEngineer()
    df_train = fe.build_dataset(t, a, l)
    
    print("Training Data Shape:", df_train.shape)
    print("Class Balance:\n", df_train['is_default'].value_counts())
    print(df_train.head())
