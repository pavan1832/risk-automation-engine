# ⚡ Quick Start Guide

## 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate sample data
python generate_sample_data.py

# 3. Run dashboard
streamlit run app.py
```

Done! Visit `http://localhost:8501`

## What Each Page Does

### 📊 Risk Dashboard
- **See all risk cases** in a real-time table
- **View statistics**: Total cases, HIGH risk count, average score
- **Charts**: Risk level distribution, score histogram
- **Bulk select** cases for actions

### ⚙️ Bulk Actions
- **Upload CSV** with case IDs for bulk processing
- **Manual selection** from filtered cases
- **Execute actions**: APPROVE, ESCALATE, BLOCK
- **Add notes** for audit trail

### 🔍 Case Details
- **View individual case** full data
- **See triggered risk factors** that caused the score
- **Read AI explanation** (powered by Gemini)
- **View action history** for the case
- **Take manual action** on the case

### 📋 Audit Logs
- **Compliance-grade audit trail** of all operations
- **Filter by event type** (CASE_CREATED, ACTION_*, etc.)
- **Export to CSV** for compliance reporting

### ⚙️ Settings
- **Generate sample data** (100 test cases)
- **Configure Gemini API** for AI explanations (optional)
- **View risk engine rules** and thresholds

## Sample Data Explained

When you run `python generate_sample_data.py`, it creates 100 realistic risk cases:

```csv
case_id,merchant_id,transaction_count,amount,location_mismatch,velocity_score,failed_attempts
CASE_00001,MERCHANT_1234,45,12500.50,0,25.3,0      → LOW risk
CASE_00050,MERCHANT_5678,150,85000.00,1,92.5,4     → HIGH risk
CASE_00075,MERCHANT_9999,75,45000.00,1,65.0,2      → MEDIUM risk
```

**Scoring Logic:**
- High transaction count (>50): +20 points
- Large amount (>$50K): +20 points
- Location mismatch: +25 points
- High velocity (>80): +20 points
- Repeated failures (≥3): +15 points
- **Final Score** = Average of rule score and ML model score

**Risk Levels:**
- LOW (0–35): Monitor
- MEDIUM (35–70): Review
- HIGH (70–100): Escalate

## Common Tasks

### Task 1: Upload Your Own Risk Data

1. Prepare CSV with columns:
   ```
   case_id,merchant_id,transaction_count,amount,location_mismatch,velocity_score,failed_attempts
   ```

2. Go to **Settings** → "Load from CSV" (or edit `data/sample_data.csv`)

3. System automatically scores all cases

### Task 2: Approve High-Risk Cases After Review

1. Go to **Risk Dashboard**
2. Filter by **Risk Level: HIGH**
3. Select cases to review
4. Click "Apply Action" → Select "APPROVE"
5. Action is logged to audit trail

### Task 3: Escalate Suspicious Cases to Fraud Team

1. Go to **Case Details**
2. Select a specific case
3. Read the **AI Risk Explanation** (powered by Gemini)
4. Click **Manual Action** → Select "ESCALATE"
5. Add notes like "Suspicious merchant pattern"

### Task 4: Generate Audit Report

1. Go to **Audit Logs**
2. Filter by event type (e.g., "ACTION_ESCALATE")
3. Click **"Download Audit Logs (CSV)"**
4. Use for compliance reporting

### Task 5: Enable AI Explanations (Optional)

1. Get free Gemini API key: https://makersuite.google.com/app/apikey
2. Go to **Settings** → Paste API key
3. Click "Test Gemini Connection"
4. System will now generate AI explanations for cases

## Database Schema (SQLite)

Three core tables:

### risk_cases
```sql
case_id (PK) | merchant_id | amount | transaction_count | 
velocity_score | location_mismatch | final_score | risk_level | 
rule_score | ml_score | triggered_rules | status
```

### risk_actions
```sql
action_id (PK) | case_id (FK) | action_type | risk_score_at_action | 
performed_by | timestamp | notes
```

### audit_logs
```sql
log_id (PK) | event_type | case_id | action_taken | 
classification_method | risk_score | user_id | timestamp
```

## Troubleshooting

**Problem**: Streamlit won't start
```bash
rm -rf ~/.streamlit
pip install --upgrade streamlit
streamlit run app.py
```

**Problem**: Database errors
```bash
rm risk_cases.db
# It will recreate on next run
```

**Problem**: "No cases found" after sample data generation
```bash
# Check if data was inserted
python -c "from database import RiskDatabase; db = RiskDatabase(); print(db.get_statistics())"
```

**Problem**: Gemini API not working
- Go to Settings, leave API key blank
- System works fine without it (uses rule-based explanations)

## Deployment to Streamlit Cloud

1. Push code to GitHub (public repo)
2. Go to https://streamlit.io/cloud
3. Click "New app" → Select repo + `app.py`
4. Go to "Secrets" → Add:
   ```
   GOOGLE_API_KEY = "your-key-here"
   ```
5. App deploys automatically

## Next Steps

1. **Load real data**: Put your risk data in `data/sample_data.csv`
2. **Train ML model**: Run `engine.train_model(your_df)` with historical labels
3. **Customize rules**: Edit `RULES` dict in `risk_engine.py`
4. **Add workflows**: Integrate with your fraud detection system
5. **Monitor metrics**: Track approval rates, escalation reasons

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit dashboard |
| `risk_engine.py` | Scoring and classification |
| `database.py` | SQLite persistence |
| `llm_explainer.py` | Gemini AI integration |
| `generate_sample_data.py` | Create test data |
| `requirements.txt` | Dependencies |

## Python API Reference

```python
# Score a case
from risk_engine import RiskScoringEngine

engine = RiskScoringEngine()
result = engine.score_case({
    'case_id': 'CASE_001',
    'amount': 50000,
    'transaction_count': 75,
    'location_mismatch': 1,
    'velocity_score': 90,
    'failed_attempts': 3
})
print(result['risk_level'])  # HIGH
print(result['final_score']) # ~85

# Log an action
from database import RiskDatabase

db = RiskDatabase()
db.log_action('CASE_001', 'ESCALATE', notes='Fraud team review')

# Get AI explanation
from llm_explainer import GeminiRiskExplainer

exp = GeminiRiskExplainer(api_key="YOUR_KEY")
explanation = exp.generate_explanation(case_data, risk_info)
```

---

**Questions?** Check README.md for full documentation.
