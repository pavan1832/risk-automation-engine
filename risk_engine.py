"""
Risk Engine: Rule-based and ML-based risk classification
Combines domain rules with logistic regression for explainable risk scoring
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import joblib
import os
from datetime import datetime
from typing import Tuple, Dict, List

class RiskScoringEngine:
    """
    Hybrid risk scoring using:
    1. Rule-based thresholds (domain expertise)
    2. Logistic Regression model (learned patterns)
    
    Output: Risk Score (0-100) + Risk Level (LOW/MEDIUM/HIGH)
    """
    
    # Rule-based thresholds (domain expertise)
    RULES = {
        'high_transaction_count': 50,       # transactions in period
        'high_amount': 50000,               # USD
        'location_mismatch_weight': 25,     # points if mismatch
        'high_velocity_score': 80,          # velocity indicator (0-100)
        'repeated_failures': 3,             # failed attempts
    }
    
    # Risk level thresholds
    RISK_THRESHOLDS = {
        'LOW': (0, 35),
        'MEDIUM': (35, 70),
        'HIGH': (70, 100)
    }
    
    def __init__(self, model_path: str = None):
        """Initialize risk engine with optional pre-trained model"""
        self.model = None
        self.scaler = None
        self.model_path = model_path
        
        # Load model if it exists
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def calculate_rule_score(self, case: Dict) -> Tuple[float, List[str]]:
        """
        Calculate rule-based risk score (0-100)
        Returns: (score, triggered_rules)
        """
        score = 0
        triggered_rules = []
        
        # Transaction count rule
        if case.get('transaction_count', 0) > self.RULES['high_transaction_count']:
            score += 20
            triggered_rules.append(f"High transaction count: {case['transaction_count']}")
        
        # Transaction amount rule
        if case.get('amount', 0) > self.RULES['high_amount']:
            score += 20
            triggered_rules.append(f"High amount: ${case['amount']:,.0f}")
        
        # Location mismatch rule
        if case.get('location_mismatch', 0) == 1:
            score += self.RULES['location_mismatch_weight']
            triggered_rules.append("Location mismatch detected")
        
        # Velocity score rule
        if case.get('velocity_score', 0) > self.RULES['high_velocity_score']:
            score += 20
            triggered_rules.append(f"Abnormal velocity: {case['velocity_score']}")
        
        # Repeated failures rule
        if case.get('failed_attempts', 0) >= self.RULES['repeated_failures']:
            score += 15
            triggered_rules.append(f"Repeated failures: {case['failed_attempts']} attempts")
        
        return min(score, 100), triggered_rules
    
    def classify_with_ml(self, case: Dict) -> Tuple[float, str]:
        """
        Classify case using pre-trained logistic regression model
        Returns: (risk_score, predicted_risk_level)
        """
        if self.model is None:
            return None, None
        
        # Prepare features
        features = self._prepare_features(pd.DataFrame([case]))
        
        # Get probability of HIGH risk
        prob = self.model.predict_proba(features)[0][1]  # P(HIGH risk)
        ml_score = prob * 100
        
        return ml_score, self._score_to_level(ml_score)
    
    def score_case(self, case: Dict) -> Dict:
        """
        Comprehensive risk scoring combining rule-based + ML
        
        Returns:
        {
            'rule_score': float,
            'ml_score': float,
            'final_score': float,
            'risk_level': str (LOW/MEDIUM/HIGH),
            'triggered_rules': List[str],
            'explanation': str
        }
        """
        # Calculate rule-based score
        rule_score, triggered_rules = self.calculate_rule_score(case)
        
        # Calculate ML score if model available
        ml_score, _ = self.classify_with_ml(case)
        
        # Ensemble: average rule and ML if available
        if ml_score is not None:
            final_score = (rule_score + ml_score) / 2
        else:
            final_score = rule_score
        
        risk_level = self._score_to_level(final_score)
        
        # Generate explanation
        explanation = self._generate_explanation(
            final_score, 
            risk_level, 
            triggered_rules,
            ml_score
        )
        
        return {
            'rule_score': round(rule_score, 2),
            'ml_score': round(ml_score, 2) if ml_score is not None else None,
            'final_score': round(final_score, 2),
            'risk_level': risk_level,
            'triggered_rules': triggered_rules,
            'explanation': explanation
        }
    
    def _score_to_level(self, score: float) -> str:
        """Convert numerical score to risk level"""
        for level, (low, high) in self.RISK_THRESHOLDS.items():
            if low <= score < high:
                return level
        return 'HIGH'
    
    def _generate_explanation(
        self, 
        score: float, 
        level: str, 
        rules: List[str],
        ml_score: float = None
    ) -> str:
        """Generate human-readable explanation of risk score"""
        
        explanation = f"Risk Level: {level} (Score: {score:.1f}/100)\n"
        
        if rules:
            explanation += "\nTriggered Rules:\n"
            for rule in rules:
                explanation += f"  • {rule}\n"
        else:
            explanation += "\nNo significant risk indicators detected.\n"
        
        if ml_score is not None:
            explanation += f"\nModel Confidence: {ml_score:.1f}%"
        
        return explanation
    
    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for ML model"""
        feature_cols = [
            'transaction_count', 'amount', 'location_mismatch',
            'velocity_score', 'failed_attempts'
        ]
        
        X = df[feature_cols].fillna(0)
        
        if self.scaler:
            X = self.scaler.transform(X)
        
        return X
    
    def train_model(self, df: pd.DataFrame, target_col: str = 'risk_label'):
        """
        Train logistic regression model on historical data
        
        Expects df with columns:
        - transaction_count, amount, location_mismatch, velocity_score, failed_attempts
        - risk_label: 1 (HIGH) or 0 (LOW/MEDIUM)
        """
        feature_cols = [
            'transaction_count', 'amount', 'location_mismatch',
            'velocity_score', 'failed_attempts'
        ]
        
        X = df[feature_cols].fillna(0)
        y = (df[target_col] == 'HIGH').astype(int)  # Binary: HIGH vs. others
        
        # Standardize features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train logistic regression
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.model.fit(X_scaled, y)
        
        print(f"✅ Model trained. Accuracy: {self.model.score(X_scaled, y):.2%}")
        
        return self
    
    def save_model(self, path: str):
        """Save trained model and scaler"""
        joblib.dump(self.model, f"{path}/model.pkl")
        joblib.dump(self.scaler, f"{path}/scaler.pkl")
        print(f"✅ Model saved to {path}")
    
    def load_model(self, path: str):
        """Load pre-trained model and scaler"""
        self.model = joblib.load(f"{path}/model.pkl")
        self.scaler = joblib.load(f"{path}/scaler.pkl")
        print(f"✅ Model loaded from {path}")
        
        return self
    
    def batch_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Score entire DataFrame of cases
        Returns: DataFrame with scoring results
        """
        results = []
        
        for idx, row in df.iterrows():
            case_dict = row.to_dict()
            score_result = self.score_case(case_dict)
            score_result['case_id'] = row.get('case_id', idx)
            score_result['timestamp'] = datetime.now()
            results.append(score_result)
        
        return pd.DataFrame(results)
