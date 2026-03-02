"""Generate sample risk data for testing"""

import pandas as pd
import numpy as np
from risk_engine import RiskScoringEngine
from database import RiskDatabase

def main():
    print("🔄 Generating sample risk data...")
    
    # Generate sample data
    np.random.seed(42)
    cases = []
    
    for i in range(100):
        case_id = f"CASE_{i+1:05d}"
        merchant_id = f"MERCHANT_{np.random.randint(1000, 9999)}"
        
        transaction_count = int(np.random.gamma(5, 8))
        amount = round(np.random.exponential(5000), 2)
        location_mismatch = int(np.random.binomial(1, 0.3))
        velocity_score = round(np.random.uniform(0, 100), 2)
        failed_attempts = int(np.random.poisson(1))
        
        cases.append({
            'case_id': case_id,
            'merchant_id': merchant_id,
            'transaction_count': transaction_count,
            'amount': amount,
            'location_mismatch': location_mismatch,
            'velocity_score': velocity_score,
            'failed_attempts': failed_attempts
        })
    
    df = pd.DataFrame(cases)
    
    # Score cases
    print("📊 Scoring cases...")
    engine = RiskScoringEngine()
    
    scored_cases = []
    for idx, row in df.iterrows():
        score_result = engine.score_case(row.to_dict())
        score_result.update(row.to_dict())
        scored_cases.append(score_result)
        
        if (idx + 1) % 25 == 0:
            print(f"  Scored {idx + 1}/100 cases")
    
    scored_df = pd.DataFrame(scored_cases)
    
    # Save to CSV
    scored_df.to_csv('data/sample_data.csv', index=False)
    print(f"✅ Saved to data/sample_data.csv")
    
    # Insert to database
    print("💾 Inserting into database...")
    db = RiskDatabase("risk_cases.db")
    db.batch_insert_cases(scored_df)
    
    # Print summary
    print("\n📈 Summary:")
    print(f"Total cases: {len(scored_df)}")
    print(f"\nBy Risk Level:")
    print(scored_df['risk_level'].value_counts())
    print(f"\nScore Statistics:")
    print(scored_df['final_score'].describe())

if __name__ == "__main__":
    main()
