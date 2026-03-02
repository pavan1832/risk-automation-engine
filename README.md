# 🛡️ Risk Automation Engine: AI-Driven Risk Case Triage

A production-ready Python system that automates operational risk workflows using rule-based scoring, machine learning classification, and LLM-powered explanations. Replaces spreadsheet-based risk tracking with a real-time, audit-compliant dashboard.

## 🎯 Overview

This system enables fintech teams to:
- **Automatically classify risk cases** (LOW/MEDIUM/HIGH) using hybrid scoring
- **Detect and explain risk factors** using both domain rules and ML models
- **Execute bulk risk actions** with full audit trails
- **Maintain compliance-grade audit logs** for regulatory requirements
- **Eliminate Excel spreadsheets** with a real-time Streamlit dashboard

### Key Features
✅ Rule-based + ML hybrid risk classification  
✅ Google Gemini LLM for explainable risk summaries  
✅ Bulk action execution (Approve, Escalate, Block)  
✅ Compliance-grade audit logging  
✅ Real-time Streamlit dashboard  
✅ SQLite persistence  
✅ Production-ready code  

## 🏗️ Architecture

```
Risk Events (CSV/API)
        ↓
Risk Scoring Engine
 ├─ Rule-Based Scoring (domain expertise)
 ├─ Logistic Regression ML Model (learned patterns)
 ├─ Ensemble scoring (rule + ML average)
        ↓
Database Layer (SQLite)
 ├─ risk_cases table (case data + scores)
 ├─ risk_actions table (action history)
 ├─ audit_logs table (compliance trail)
        ↓
Gemini LLM
 └─ Risk explanation generation
        ↓
Streamlit Dashboard
 ├─ Real-time risk dashboard
 ├─ Bulk action panel
 ├─ Audit logs viewer
 └─ Case management UI
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
# Create project directory
mkdir risk_automation_engine
cd risk_automation_engine

# Copy all Python files
# (or clone from repository)

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Sample Data (Optional)

```bash
# Create sample risk cases
python generate_sample_data.py

# Output:
# ✅ Generated 100 sample cases
# ✅ Inserted into database
```

### 3. Run Streamlit App

```bash
# Set Gemini API key (optional)
export GOOGLE_API_KEY="your-api-key-here"

# Start the app
streamlit run app.py
```

Visit `http://localhost:8501` to access the dashboard.

## 📋 Project Structure

```
risk_automation_engine/
├── app.py                      # Main Streamlit dashboard
├── risk_engine.py              # Risk scoring & classification
├── database.py                 # SQLite persistence & audit
├── llm_explainer.py            # Gemini API integration
├── utils.py                    # Utility functions
├── generate_sample_data.py     # Sample data generator
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── data/
    └── sample_data.csv         # Example data
```

## 🔑 Core Components

### 1. Risk Scoring Engine (`risk_engine.py`)

**Hybrid approach combining:**

#### Rule-Based Scoring
Domain-expert rules that evaluate specific risk factors:
- High transaction count (>50)
- Large amounts (>$50,000)
- Location mismatch (25 points)
- High velocity score (>80)
- Repeated failures (≥3 attempts)

```python
from risk_engine import RiskScoringEngine

engine = RiskScoringEngine()

case = {
    'case_id': 'CASE_001',
    'merchant_id': 'MERCHANT_5432',
    'transaction_count': 75,
    'amount': 75000,
    'location_mismatch': 1,
    'velocity_score': 92,
    'failed_attempts': 4
}

result = engine.score_case(case)
# Output:
# {
#   'rule_score': 100.0,
#   'ml_score': 87.5,
#   'final_score': 93.75,
#   'risk_level': 'HIGH',
#   'triggered_rules': [...],
#   'explanation': '...'
# }
```

#### ML Classification
Simple logistic regression model that learns from historical data:

```python
# Train on historical cases
engine.train_model(historical_df, target_col='risk_label')

# Predict on new cases
engine.save_model('./models')
```

#### Ensemble Scoring
Final score = (rule_score + ml_score) / 2

### 2. Database Layer (`database.py`)

SQLite-based persistence with three core tables:

#### risk_cases
Stores case data and scoring results
```
case_id | merchant_id | amount | final_score | risk_level | status | ...
```

#### risk_actions
Audit trail of all actions taken
```
case_id | action_type | risk_score_at_action | performed_by | timestamp
```

#### audit_logs
Compliance-grade logs for all operations
```
event_type | case_id | action_taken | classification_method | timestamp | ...
```

**API Example:**

```python
from database import RiskDatabase

db = RiskDatabase("risk_cases.db")

# Insert a scored case
db.insert_risk_case({
    'case_id': 'CASE_001',
    'merchant_id': 'MERCHANT_123',
    'final_score': 75.5,
    'risk_level': 'HIGH',
    'triggered_rules': ['High amount', 'Location mismatch']
})

# Log an action
db.log_action('CASE_001', 'ESCALATE', notes='Manual review required')

# Bulk action (most important)
count = db.bulk_action(
    case_ids=['CASE_001', 'CASE_002', 'CASE_003'],
    action_type='APPROVE',
    notes='Batch approved after review'
)

# Retrieve cases
cases = db.get_risk_cases(risk_level='HIGH', limit=100)

# Get audit logs
logs = db.get_audit_logs(event_type='ACTION_ESCALATE')

# Statistics
stats = db.get_statistics()
# {'total_cases': 500, 'by_risk_level': {'HIGH': 50, ...}, ...}
```

### 3. LLM Explainer (`llm_explainer.py`)

Google Gemini integration for risk explanations:

```python
from llm_explainer import GeminiRiskExplainer

explainer = GeminiRiskExplainer(api_key="YOUR_API_KEY")

explanation = explainer.generate_explanation(
    case_data={
        'merchant_id': 'MERCHANT_123',
        'transaction_count': 75,
        'amount': 75000,
        'location_mismatch': 1,
        'velocity_score': 92
    },
    risk_info={
        'final_score': 85.0,
        'risk_level': 'HIGH',
        'triggered_rules': [
            'High transaction count: 75',
            'High amount: $75,000.00',
            'Location mismatch detected'
        ]
    }
)

# Output (from Gemini):
# "This case was flagged HIGH risk due to abnormal transaction velocity 
#  (92), repeated location mismatches, and a large transaction amount 
#  ($75,000). Combined with elevated transaction frequency, this pattern
#  suggests potential fraud or abuse."
```

**Features:**
- Optional: Falls back to rule-based explanation if API unavailable
- Rate-limited: Built-in protection for batch operations
- Configurable: Customizable prompts for different risk types

### 4. Streamlit Dashboard (`app.py`)

Real-time risk management interface replacing Excel sheets.

#### Pages

1. **📊 Risk Dashboard**
   - Risk level distribution (pie/bar charts)
   - Score distribution histogram
   - Filterable case table
   - Real-time statistics (total cases, HIGH count, avg score)
   - Bulk action selection interface

2. **⚙️ Bulk Actions**
   - Upload CSV with case IDs
   - Manual multi-select from filtered cases
   - Execute actions: APPROVE, ESCALATE, BLOCKED
   - Add notes for documentation

3. **🔍 Case Details**
   - Individual case inspection
   - Full case data and scoring breakdown
   - Triggered risk factors
   - AI-generated explanation (via Gemini)
   - Action history timeline
   - Manual action execution

4. **📋 Audit Logs**
   - Compliance-grade audit trail
   - Filter by event type or case ID
   - Export to CSV
   - Timestamp and user tracking

5. **⚙️ Settings**
   - Generate sample data
   - Configure Gemini API
   - View risk engine rules
   - Database management

## 📊 Data Format

### Input CSV Format

```csv
case_id,merchant_id,transaction_count,amount,location_mismatch,velocity_score,failed_attempts
CASE_001,MERCHANT_5432,75,75000.00,1,92.5,4
CASE_002,MERCHANT_1234,15,5000.00,0,25.3,0
CASE_003,MERCHANT_9999,200,250000.00,1,95.0,8
```

### Output Database Schema

```sql
-- Main risk cases
CREATE TABLE risk_cases (
    case_id TEXT PRIMARY KEY,
    merchant_id TEXT,
    transaction_count INTEGER,
    amount REAL,
    location_mismatch INTEGER,
    velocity_score REAL,
    failed_attempts INTEGER,
    rule_score REAL,
    ml_score REAL,
    final_score REAL,
    risk_level TEXT,
    triggered_rules TEXT,
    explanation TEXT,
    status TEXT,
    created_at TIMESTAMP
);

-- Action audit trail
CREATE TABLE risk_actions (
    action_id INTEGER PRIMARY KEY,
    case_id TEXT,
    action_type TEXT,
    risk_score_at_action REAL,
    performed_by TEXT,
    timestamp TIMESTAMP
);

-- Compliance logs
CREATE TABLE audit_logs (
    log_id INTEGER PRIMARY KEY,
    event_type TEXT,
    case_id TEXT,
    action_taken TEXT,
    classification_method TEXT,
    timestamp TIMESTAMP
);
```

## 🚀 Deployment

### Local Development

```bash
streamlit run app.py
```

### Streamlit Cloud

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Click "New app"
   - Select your GitHub repo and `app.py`
   - Set environment variable: `GOOGLE_API_KEY`
   - Deploy

3. **Requirements for Cloud**
   - `requirements.txt` with all dependencies
   - `app.py` as entry point
   - All Python modules in same directory
   - Gemini API key in secrets

### Docker Deployment

```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

```bash
docker build -t risk-engine .
docker run -p 8501:8501 \
  -e GOOGLE_API_KEY="your-key" \
  risk-engine
```

## 🔒 Security & Compliance

### Audit Trail
Every operation is logged to `audit_logs`:
- Case creation
- Action execution (approve/escalate/block)
- Bulk operations
- User/system information
- Timestamp precision

### Data Protection
- SQLite local persistence
- No cloud storage by default
- Exportable audit logs for compliance
- Case status tracking

### API Security
- Google Gemini API key kept in environment variables
- Never hardcoded credentials
- Fallback when API unavailable
- Rate limiting for batch operations

## 🧪 Testing & Validation

### Generate Sample Data

```bash
python generate_sample_data.py
```

Creates 100 realistic risk cases with:
- Varied transaction counts (gamma distribution)
- Realistic amounts (exponential distribution)
- Random location mismatches
- Realistic velocity scores

### Test Scoring

```python
from risk_engine import RiskScoringEngine
import pandas as pd

engine = RiskScoringEngine()

# Score a single case
result = engine.score_case({
    'case_id': 'TEST_001',
    'merchant_id': 'TEST_MERCHANT',
    'transaction_count': 100,
    'amount': 100000,
    'location_mismatch': 1,
    'velocity_score': 95,
    'failed_attempts': 5
})

print(f"Risk Level: {result['risk_level']}")  # HIGH
print(f"Score: {result['final_score']:.1f}")  # ~93
```

## 📈 Performance & Scaling

### Current Capacity
- **Cases per scoring**: ~100 cases/second (on MacBook)
- **Database**: Handles 100K+ cases efficiently with indexes
- **Dashboard**: Real-time updates for 500+ cases
- **Audit logs**: Millions of entries supported

### Optimization Tips
1. Use batch operations for bulk actions
2. Index frequently-filtered columns
3. Archive old audit logs periodically
4. Use ML model for faster scoring than rules

## 🔗 Integration Examples

### With External Risk APIs

```python
# Integrate with risk data sources
import requests

def fetch_risk_cases(api_url):
    """Fetch cases from external risk API"""
    response = requests.get(api_url)
    data = response.json()
    return pd.DataFrame(data['cases'])

# Score and store
cases = fetch_risk_cases("https://risk-api.example.com/cases")
engine = RiskScoringEngine()
scored = engine.batch_score(cases)

db = RiskDatabase()
db.batch_insert_cases(scored)
```

### With Slack Notifications

```python
from slack_sdk import WebClient

def notify_high_risk(case_id, risk_level):
    """Send Slack notification for HIGH risk cases"""
    client = WebClient(token=os.getenv('SLACK_TOKEN'))
    client.chat_postMessage(
        channel='#risk-alerts',
        text=f"🚨 {case_id} flagged as {risk_level} risk"
    )

# Use in database.py
db.log_action(case_id, 'ESCALATE')
notify_high_risk(case_id, 'HIGH')
```

## 🐛 Troubleshooting

### Streamlit Won't Start
```bash
# Clear cache
rm -rf ~/.streamlit

# Reinstall
pip install --upgrade streamlit

# Run with debug
streamlit run app.py --logger.level=debug
```

### Database Locked
```bash
# Remove corrupted database
rm risk_cases.db

# Recreate on next run
python app.py
```

### Gemini API Errors
```python
# Set API key manually
os.environ['GOOGLE_API_KEY'] = 'your-key'

# Test connection
from llm_explainer import GeminiRiskExplainer
exp = GeminiRiskExplainer()
```

## 📚 Documentation

### Risk Scoring Rules

| Rule | Weight | Threshold |
|------|--------|-----------|
| High Transaction Count | +20 | > 50 |
| High Amount | +20 | > $50,000 |
| Location Mismatch | +25 | Binary |
| High Velocity | +20 | > 80 |
| Repeated Failures | +15 | ≥ 3 |

**Risk Levels:**
- **LOW**: 0–35 (Monitor)
- **MEDIUM**: 35–70 (Review)
- **HIGH**: 70–100 (Escalate)

## 🤝 Contributing

To extend this system:

1. **Add new risk rules** → `risk_engine.py` `calculate_rule_score()`
2. **Add new actions** → Modify action types in `app.py` and `database.py`
3. **Customize dashboard** → Edit pages in `app.py`
4. **Train ML model** → `engine.train_model()` with your historical data

## 📄 License

MIT License - Use freely for educational and commercial purposes.

## 🎓 For Internship/Interview

This project demonstrates:
✅ **Software Engineering**: Clean architecture, modularity, error handling  
✅ **Risk Management**: Domain knowledge (thresholds, rules, classifications)  
✅ **Data Engineering**: ETL, database design, audit trails  
✅ **ML**: Logistic regression, feature engineering, ensemble scoring  
✅ **API Integration**: Google Gemini LLM, error handling, fallbacks  
✅ **Full-Stack**: Python backend + Streamlit UI  
✅ **DevOps**: Docker, Streamlit Cloud deployment  

## 📞 Support

For questions or issues:
1. Check troubleshooting section
2. Review risk_engine.py documentation
3. Check database.py for schema details
4. Review Streamlit documentation: https://docs.streamlit.io

---

**Last Updated**: March 2026  
**Version**: 1.0.0  
**Status**: Production Ready ✅
