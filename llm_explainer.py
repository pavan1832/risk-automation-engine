"""LLM Risk Explainer: Google Gemini API integration for risk explanations"""

import os
import google.generativeai as genai
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiRiskExplainer:
    """Use Google Gemini API to generate risk explanations"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = "gemini-1.5-flash"
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                logger.info("✅ Gemini API configured")
            except Exception as e:
                logger.warning(f"⚠️ Gemini API config failed: {e}")
        else:
            logger.warning("⚠️ GOOGLE_API_KEY not set. LLM explanations will be disabled.")
    
    def generate_explanation(self, case_data: dict, risk_info: dict) -> str:
        """Generate risk explanation using Gemini"""
        if not self.api_key:
            return self._fallback_explanation(case_data, risk_info)
        
        try:
            prompt = self._build_prompt(case_data, risk_info)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt, stream=False)
            
            if response and response.text:
                return response.text.strip()
            else:
                return self._fallback_explanation(case_data, risk_info)
        
        except Exception as e:
            logger.warning(f"⚠️ Gemini API error: {e}. Using fallback.")
            return self._fallback_explanation(case_data, risk_info)
    
    def _build_prompt(self, case_data: dict, risk_info: dict) -> str:
        """Build prompt for Gemini"""
        rules = risk_info.get('triggered_rules', [])
        rule_text = "\n".join([f"  • {r}" for r in rules]) if rules else "No specific rules triggered"
        
        prompt = f"""You are a fintech risk analyst. Provide a concise, clear explanation of why 
this transaction/merchant was flagged as {risk_info['risk_level']} risk.

CASE DATA:
- Merchant ID: {case_data.get('merchant_id', 'Unknown')}
- Transaction Count: {case_data.get('transaction_count', 0)}
- Amount: ${case_data.get('amount', 0):,.0f}
- Location Mismatch: {'Yes' if case_data.get('location_mismatch') else 'No'}
- Velocity Score: {case_data.get('velocity_score', 0)}
- Failed Attempts: {case_data.get('failed_attempts', 0)}

TRIGGERED RISK FACTORS:
{rule_text}

RISK SCORE: {risk_info['final_score']:.1f}/100

TASK: Explain in 2-3 sentences why this case is flagged {risk_info['risk_level']} risk. 
Be specific about the factors. Be concise and operationally useful."""
        
        return prompt
    
    def _fallback_explanation(self, case_data: dict, risk_info: dict) -> str:
        """Fallback explanation when API is unavailable"""
        rules = risk_info.get('triggered_rules', [])
        rules_str = "\n".join([f"  • {r}" for r in rules]) if rules else "No significant risk indicators"
        
        return f"""Risk Level: {risk_info['risk_level']} (Score: {risk_info['final_score']:.1f}/100)

Triggered Risk Factors:
{rules_str}

[Note: Full LLM explanation unavailable - using rule-based summary]"""
    
    def batch_explain(self, cases_list: list) -> list:
        """Generate explanations for multiple cases (rate-limited)"""
        explanations = []
        for i, case_data in enumerate(cases_list):
            if i > 0 and i % 5 == 0:
                logger.info(f"Processing case {i}/{len(cases_list)}...")
            
            explanation = self.generate_explanation(case_data['case_data'], 
                                                   case_data['risk_info'])
            explanations.append(explanation)
        
        return explanations
