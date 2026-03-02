# 🛡️ Risk Automation Engine - Implementation Guide

## Complete Technical Walkthrough

This guide explains how the Risk Automation Engine works and how to use/extend it.

---

## 1. System Overview

### Architecture Flow

```
CSV Input → Risk Engine → Database → Streamlit Dashboard
                    ↓
               Gemini LLM
              (Explanations)
```

### Three Core Systems

1. **Risk Scoring** (`risk_engine.py`)
   - Rule-based classification
   - ML-based prediction
   - Ensemble scoring

2. **Data Persistence** (`database.py`)
   - SQLite storage
   - Audit trail logging
   - Action tracking

3. **Explanation** (`llm_explainer.py`)
   - Gemini API integration
   - Fallback explanations
   - Batch processing

---

## 2. Risk Scoring Deep Dive

### Rule-Based Scoring

The `RiskScoringEngine` implements domain-expert rules:

```python
def calculate_rule_score(self, case: Dict) -> Tuple[float, List[str]]:
    """
    Each rule adds points to risk score:
    - High transaction count (>50): +20 points
    - Large amount (>$50K): +20 points
    - Location mismatch: +25 points
    - High velocity (>80): +20 points
    - Repeated failures (≥3): +15 points
    
    Maximum score: 100 (capped)
    """
```

**Example Calculation:**

```
Case: CASE_001
- transaction_count: 150 (>50) → +20 ✓
- amount: $95,000 (>$50K) → +20 ✓
- location_mismatch: 1 → +25 ✓
- velocity_score: 92 (>80) → +20 ✓
- failed_attempts: 5 (≥3) → +15 ✓

Rule Score: 20+20+25+20+15 = 100
```

### Machine Learning Component

Optional logistic regression model for learning from historical data:

```python
# Train on historical cases with labels
engine.train_model(
    df=historical_data,
    target_col='risk_label'  # 'HIGH' or other
)

# Predicts probability of HIGH risk
# Score 0-100 based on probability
```

### Ensemble Scoring

Final score = Average of rule score and ML score:

```python
final_score = (rule_score + ml_score) / 2
```

**Why Ensemble?**
- Rules ensure explainability (domain expert rules)
- ML learns patterns from data
- Together: Explainable + Accurate

---

## 3. Database Architecture

### Three Tables

#### risk_cases
```sql
SELECT * FROM risk_cases WHERE case_id = 'CASE_001';

case_id          │ CASE_001
merchant_id      │ MERCHANT_5432
transaction_count│ 150
amount           │ 95000.00
location_mismatch│ 1
velocity_score   │ 92.5
failed_attempts  │ 5
rule_score       │ 100.0
ml_score         │ 87.3
final_score      │ 93.65
risk_level       │ HIGH
triggered_rules  │ ['High transaction count', 'Location mismatch', ...]
status           │ NEW
created_at       │ 2024-03-02 10:15:30
```

#### risk_actions
```sql
SELECT * FROM risk_actions WHERE case_id = 'CASE_001';

action_id      │ 1
case_id        │ CASE_001
action_type    │ ESCALATE
risk_level_at  │ HIGH
risk_score_at  │ 93.65
performed_by   │ SYSTEM
timestamp      │ 2024-03-02 10:20:15
notes          │ "Escalated to fraud team"
```

#### audit_logs
```sql
SELECT * FROM audit_logs WHERE case_id = 'CASE_001' LIMIT 5;

log_id                 │ 1
event_type             │ CASE_CREATED
case_id                │ CASE_001
action_taken           │ New risk case ingested
classification_method  │ HYBRID (Rule + ML)
risk_score             │ 93.65
user_id                │ SYSTEM
timestamp              │ 2024-03-02 10:15:30
details                │ {...full JSON...}
```

### Key Operations

```python
from database import RiskDatabase

db = RiskDatabase()

# Single case insertion (auto-logs to audit)
db.insert_risk_case({
    'case_id': 'CASE_001',
    'merchant_id': 'MERCHANT_5432',
    'amount': 95000,
    'transaction_count': 150,
    'location_mismatch': 1,
    'velocity_score': 92,
    'failed_attempts': 5,
    'rule_score': 100.0,
    'ml_score': 87.3,
    'final_score': 93.65,
    'risk_level': 'HIGH',
    'triggered_rules': ['High transaction count', ...]
})

# Bulk insertion
db.batch_insert_cases(cases_dataframe)

# Log action with automatic timestamp
db.log_action(
    case_id='CASE_001',
    action_type='ESCALATE',
    notes='Manual review by analyst',
    performed_by='analyst_john'
)

# Bulk action (most important for workflow)
count = db.bulk_action(
    case_ids=['CASE_001', 'CASE_002', 'CASE_003'],
    action_type='APPROVE',
    notes='Batch review complete',
    performed_by='team_lead'
)
# Logs every action and case status change

# Retrieve with filters
cases = db.get_risk_cases(risk_level='HIGH', status='NEW')

# Get full case history
details = db.get_case_details('CASE_001')

# Audit log queries
logs = db.get_audit_logs(
    case_id='CASE_001',
    event_type='ACTION_ESCALATE'
)
```

---

## 4. Streamlit Dashboard Walkthrough

### Page: Risk Dashboard

**Components:**
1. **Filters** (top)
   - Risk Level filter: ALL, LOW, MEDIUM, HIGH
   - Status filter: ALL, NEW, APPROVED, ESCALATED, BLOCKED
   - Refresh button

2. **Metrics** (cards)
   - Total cases
   - HIGH risk count
   - MEDIUM risk count
   - Average risk score

3. **Charts**
   - Risk Level Distribution (bar chart)
   - Score Distribution (histogram)

4. **Table**
   - Sortable/filterable case table
   - Color-coded by risk level
   - Shows: case_id, merchant, amount, score, level, status

5. **Bulk Actions**
   - Multi-select cases from table
   - Choose action type
   - Add notes
   - Apply

**Code Flow:**
```python
# 1. Get filtered cases
cases_df = db.get_risk_cases(
    risk_level='HIGH',  # or None for all
    status='NEW'
)

# 2. Display metrics
st.metric("HIGH Risk", len(cases_df[cases_df['risk_level']=='HIGH']))

# 3. Chart data
risk_dist = cases_df['risk_level'].value_counts()
# → Plotly bar chart

# 4. Table display
st.dataframe(cases_df[display_cols])

# 5. Bulk action
if selected_ids:
    db.bulk_action(selected_ids, 'APPROVE', notes)
    # → Logged to audit_actions + audit_logs
```

### Page: Bulk Actions

**Two workflows:**

1. **CSV Upload** (for automated pipelines)
   - Upload CSV with case_id column
   - Choose action (APPROVE/ESCALATE/BLOCK)
   - Execute

2. **Manual Selection** (for manual review)
   - Filter by risk level
   - Multi-select cases
   - Choose action
   - Execute

**Code:**
```python
# CSV workflow
uploaded_file = st.file_uploader('Upload CSV')
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    case_ids = df['case_id'].tolist()
    
    # Execute bulk action
    count = db.bulk_action(case_ids, action_type, notes)
```

### Page: Case Details

**Sections:**
1. **Case Info** (metrics)
   - Risk Score, Risk Level, Status, Merchant

2. **Case Data** (input features)
   - Amount, Transaction Count, Velocity, Location Match, Failures

3. **Scoring Details** (scoring breakdown)
   - Rule Score, ML Score, Final Score

4. **Triggered Rules** (explainability)
   - List of rules that fired

5. **AI Explanation** (LLM)
   - Gemini-generated summary

6. **Action History** (audit)
   - Timeline of all actions taken

7. **Manual Action** (control)
   - Button to execute action on this case

### Page: Audit Logs

**Features:**
- Filter by event type or case_id
- Show last N entries (slider)
- Display as sortable table
- Download as CSV

**Audit Events:**
- `CASE_CREATED`: New case ingested
- `ACTION_APPROVE`: Case approved
- `ACTION_ESCALATE`: Case escalated
- `ACTION_BLOCKED`: Case blocked
- `BULK_ACTION`: Multiple cases actioned

### Page: Settings

**Options:**
1. **Data Management**
   - Generate sample data (100 cases)
   - Load from CSV
   - Clear database

2. **LLM Configuration**
   - Input Gemini API key
   - Test connection
   - View if enabled/disabled

3. **Risk Engine Config**
   - Display current rules
   - Display thresholds

---

## 5. Gemini LLM Integration

### How It Works

```python
from llm_explainer import GeminiRiskExplainer

# Initialize
explainer = GeminiRiskExplainer(api_key="YOUR_API_KEY")

# Generate explanation
explanation = explainer.generate_explanation(
    case_data={
        'merchant_id': 'MERCHANT_5432',
        'amount': 95000,
        'transaction_count': 150,
        'location_mismatch': 1,
        'velocity_score': 92,
        'failed_attempts': 5
    },
    risk_info={
        'final_score': 93.65,
        'risk_level': 'HIGH',
        'triggered_rules': [
            'High transaction count: 150',
            'High amount: $95,000',
            'Location mismatch detected',
            'Abnormal velocity: 92'
        ]
    }
)
```

**Gemini Response:**
```
This case was flagged HIGH risk due to four critical factors:
1. Abnormally high transaction velocity (92/100)
2. Large transaction amount ($95,000) combined with high frequency (150 transactions)
3. Location mismatch indicating possible fraud ring
4. Multiple failed attempts suggesting account testing
This pattern is consistent with organized card-testing attacks.
```

### Fallback (When API Unavailable)

If Gemini API fails, system generates rule-based explanation:

```
Risk Level: HIGH (Score: 93.65/100)

Triggered Risk Factors:
• High transaction count: 150
• High amount: $95,000.00
• Location mismatch detected
• Abnormal velocity: 92
```

### API Key Management

**Option 1: Environment Variable**
```bash
export GOOGLE_API_KEY="your-key-here"
python app.py
```

**Option 2: Runtime Configuration**
```python
import os
os.environ['GOOGLE_API_KEY'] = 'your-key'
```

**Option 3: Streamlit Secrets** (Cloud)
```
# .streamlit/secrets.toml
GOOGLE_API_KEY = "your-key"
```

---

## 6. Workflow Examples

### Workflow 1: Daily Risk Triage

**Process:**
1. Load overnight risk cases from CSV
2. Score all cases
3. Flag HIGH risk cases
4. Review HIGH risk cases in dashboard
5. Approve low-risk, escalate suspicious
6. Log all decisions to audit trail

**Code:**
```python
# Load data
cases = pd.read_csv('overnight_risks.csv')

# Score
engine = RiskScoringEngine()
scored = engine.batch_score(cases)

# Insert
db = RiskDatabase()
db.batch_insert_cases(scored)

# Filter HIGH risk
high_risk = db.get_risk_cases(risk_level='HIGH', status='NEW')
print(f"Found {len(high_risk)} HIGH risk cases for review")

# Use dashboard to review and action
```

### Workflow 2: Automated Approval

**For cases that pass additional checks:**

```python
# Get LOW risk cases
low_risk = db.get_risk_cases(risk_level='LOW', status='NEW')

# Auto-approve if extra conditions met
to_approve = []
for case in low_risk:
    if case['velocity_score'] < 30 and case['amount'] < 10000:
        to_approve.append(case['case_id'])

# Bulk approve
count = db.bulk_action(
    to_approve,
    'APPROVE',
    'Auto-approved: Low risk + velocity < 30'
)
print(f"Auto-approved {count} cases")
```

### Workflow 3: Fraud Pattern Detection

**Escalate similar suspicious cases:**

```python
# Find cases with location mismatch + high velocity
cases = db.get_risk_cases(limit=1000)

suspicious = cases[
    (cases['location_mismatch'] == 1) & 
    (cases['velocity_score'] > 85)
]['case_id'].tolist()

# Bulk escalate
count = db.bulk_action(
    suspicious,
    'ESCALATE',
    'Suspected fraud ring: location mismatch + high velocity'
)
print(f"Escalated {count} suspected fraud cases")
```

---

## 7. Extending the System

### Add New Risk Rule

```python
# In risk_engine.py, update calculate_rule_score():

def calculate_rule_score(self, case: Dict) -> Tuple[float, List[str]]:
    score = 0
    triggered_rules = []
    
    # ... existing rules ...
    
    # NEW RULE: High merchant chargeback ratio
    if case.get('chargeback_ratio', 0) > 0.05:
        score += 20
        triggered_rules.append(
            f"High chargeback ratio: {case['chargeback_ratio']:.1%}"
        )
    
    # NEW RULE: Multiple failed payment methods
    if case.get('payment_methods_tried', 0) > 5:
        score += 15
        triggered_rules.append(
            f"Multiple payment methods tried: {case['payment_methods_tried']}"
        )
    
    return min(score, 100), triggered_rules
```

### Add New Action Type

```python
# In database.py, bulk_action() already supports any action_type
# Just use it:

db.bulk_action(case_ids, 'REVIEW', 'Flagged for manual analyst review')

# In app.py, update selectbox options:

action = st.selectbox(
    "Action",
    ["APPROVE", "ESCALATE", "BLOCKED", "REVIEW", "RELEASE"]
)
```

### Custom Notification

```python
# Add to app.py or create notify.py

def send_slack_alert(case_id, risk_level):
    """Send Slack notification for HIGH risk"""
    from slack_sdk import WebClient
    
    client = WebClient(token=os.getenv('SLACK_TOKEN'))
    client.chat_postMessage(
        channel='#risk-alerts',
        text=f"🚨 {case_id} flagged as {risk_level} risk"
    )

# Use in app.py when escalating:
if action == 'ESCALATE':
    db.bulk_action(selected, 'ESCALATE', notes)
    for case_id in selected:
        send_slack_alert(case_id, 'HIGH')
```

---

## 8. Performance & Optimization

### Benchmarks (MacBook Pro)

| Operation | Time | Notes |
|-----------|------|-------|
| Score single case | 1-2ms | Rule-based only |
| Score 100 cases | 100-200ms | Batch process |
| Database insert | 5ms | Per case |
| Gemini API call | 1-3 seconds | Rate limited |
| Dashboard load | 500ms | With 500 cases |

### Query Optimization

```sql
-- Slow (full table scan)
SELECT * FROM risk_cases WHERE risk_level = 'HIGH'

-- Fast (indexed)
SELECT * FROM risk_cases WHERE risk_level = 'HIGH'
-- (index on risk_level exists)
```

Database automatically creates indexes on:
- `risk_level`
- `case_id`
- `timestamp`

### Batch Operations

```python
# SLOW: Loop with individual inserts
for case in cases:
    db.insert_risk_case(case)  # ❌ N database transactions

# FAST: Batch insert
db.batch_insert_cases(cases_df)  # ✅ 1 database transaction
```

---

## 9. Production Checklist

- [ ] Database backups automated
- [ ] Gemini API key in secrets (not hardcoded)
- [ ] Audit logs exported regularly
- [ ] Risk rules documented and version-controlled
- [ ] ML model evaluation metrics tracked
- [ ] Dashboard access controls (if needed)
- [ ] Data retention policy defined
- [ ] Performance monitoring active
- [ ] Error handling and logging
- [ ] Disaster recovery plan

---

## 10. Troubleshooting

### Issue: Cases not appearing

```python
# Debug: Check database
from database import RiskDatabase
db = RiskDatabase()
stats = db.get_statistics()
print(stats)  # Should show total_cases > 0

# Check if insert worked
cases = db.get_risk_cases(limit=10)
print(len(cases))
```

### Issue: Slow dashboard

```python
# Reduce data fetched
cases = db.get_risk_cases(limit=100)  # Instead of 1000

# Add caching in Streamlit
@st.cache_data
def get_cases():
    return db.get_risk_cases()
```

### Issue: Gemini API errors

```python
# Check API key
import google.generativeai as genai
try:
    genai.configure(api_key=api_key)
    print("✅ API configured")
except Exception as e:
    print(f"❌ Error: {e}")

# Check rate limits
import time
time.sleep(1)  # Add delay between calls
```

---

**Next:** Read QUICKSTART.md for simple usage guide.

