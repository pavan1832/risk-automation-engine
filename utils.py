"""Utility functions for risk automation engine"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def load_risk_data(csv_path: str) -> pd.DataFrame:
    """Load risk data from CSV"""
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} cases from {csv_path}")
        return df
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return pd.DataFrame()

def generate_sample_data(num_cases: int = 100) -> pd.DataFrame:
    """Generate realistic sample risk data for testing"""
    np.random.seed(42)
    
    cases = []
    for i in range(num_cases):
        case_id = f"CASE_{i+1:05d}"
        merchant_id = f"MERCHANT_{np.random.randint(1000, 9999)}"
        
        # Realistic distributions
        transaction_count = np.random.gamma(5, 8)
        amount = np.random.exponential(5000)
        location_mismatch = np.random.binomial(1, 0.3)
        velocity_score = np.random.uniform(0, 100)
        failed_attempts = np.random.poisson(1)
        
        cases.append({
            'case_id': case_id,
            'merchant_id': merchant_id,
            'transaction_count': int(transaction_count),
            'amount': round(amount, 2),
            'location_mismatch': int(location_mismatch),
            'velocity_score': round(velocity_score, 2),
            'failed_attempts': int(failed_attempts)
        })
    
    return pd.DataFrame(cases)

def export_results(df: pd.DataFrame, output_path: str = "risk_results.csv"):
    """Export results to CSV"""
    try:
        df.to_csv(output_path, index=False)
        print(f"✅ Results exported to {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Export error: {e}")
        return None

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"

def format_timestamp(ts) -> str:
    """Format timestamp for display"""
    if isinstance(ts, str):
        return ts
    try:
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(ts)

def get_risk_color(risk_level: str) -> str:
    """Get color for risk level (for UI)"""
    colors = {
        'LOW': '#2ecc71',      # green
        'MEDIUM': '#f39c12',   # orange
        'HIGH': '#e74c3c'      # red
    }
    return colors.get(risk_level, '#95a5a6')

def calculate_percentiles(df: pd.DataFrame, score_col: str = 'final_score') -> dict:
    """Calculate score percentiles"""
    if df.empty:
        return {}
    return {
        'p50': df[score_col].quantile(0.5),
        'p75': df[score_col].quantile(0.75),
        'p90': df[score_col].quantile(0.90),
        'p99': df[score_col].quantile(0.99),
        'max': df[score_col].max(),
        'min': df[score_col].min()
    }

def get_time_window(hours: int = 24) -> tuple:
    """Get time window for filtering"""
    now = datetime.now()
    start = now - timedelta(hours=hours)
    return start, now
