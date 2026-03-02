"""Database Module: SQLite-based persistence with audit trail"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from contextlib import contextmanager

class RiskDatabase:
    """SQLite database for risk cases, actions, and audit logs"""
    
    def __init__(self, db_path: str = "risk_cases.db"):
        self.db_path = db_path
        self._init_tables()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS risk_cases (
                case_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL,
                transaction_count INTEGER, amount REAL, location_mismatch INTEGER,
                velocity_score REAL, failed_attempts INTEGER, rule_score REAL,
                ml_score REAL, final_score REAL NOT NULL, risk_level TEXT NOT NULL,
                triggered_rules TEXT, explanation TEXT, status TEXT DEFAULT 'NEW',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS risk_actions (
                action_id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
                action_type TEXT NOT NULL, risk_level_at_action TEXT,
                risk_score_at_action REAL, performed_by TEXT DEFAULT 'SYSTEM',
                notes TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES risk_cases(case_id))""")
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
                case_id TEXT, action_taken TEXT, risk_score REAL,
                classification_method TEXT, rule_applied TEXT, user_id TEXT DEFAULT 'SYSTEM',
                ip_address TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, details TEXT)""")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_level ON risk_cases(risk_level)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_id ON risk_actions(case_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit ON audit_logs(timestamp)")
            print("✅ Database tables initialized")
    
    def insert_risk_case(self, case_data: Dict) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""INSERT OR REPLACE INTO risk_cases
                (case_id, merchant_id, transaction_count, amount, location_mismatch,
                 velocity_score, failed_attempts, rule_score, ml_score, final_score,
                 risk_level, triggered_rules, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (case_data['case_id'], case_data.get('merchant_id', 'UNKNOWN'),
                 case_data.get('transaction_count', 0), case_data.get('amount', 0),
                 case_data.get('location_mismatch', 0), case_data.get('velocity_score', 0),
                 case_data.get('failed_attempts', 0), case_data.get('rule_score', 0),
                 case_data.get('ml_score'), case_data.get('final_score', 0),
                 case_data.get('risk_level', 'LOW'), 
                 json.dumps(case_data.get('triggered_rules', [])),
                 case_data.get('explanation', '')))
            self._log_audit(conn, event_type='CASE_CREATED', case_id=case_data['case_id'],
                           action_taken='New risk case ingested',
                           risk_score=case_data.get('final_score', 0),
                           classification_method='HYBRID (Rule + ML)',
                           details=json.dumps(case_data))
            return True
    
    def batch_insert_cases(self, cases_df: pd.DataFrame) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for idx, row in cases_df.iterrows():
                try:
                    case_data = row.to_dict()
                    cursor.execute("""INSERT OR REPLACE INTO risk_cases
                        (case_id, merchant_id, transaction_count, amount, location_mismatch,
                         velocity_score, failed_attempts, rule_score, ml_score, final_score,
                         risk_level, triggered_rules, explanation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (case_data['case_id'], case_data.get('merchant_id', 'UNKNOWN'),
                         case_data.get('transaction_count', 0), case_data.get('amount', 0),
                         case_data.get('location_mismatch', 0), case_data.get('velocity_score', 0),
                         case_data.get('failed_attempts', 0), case_data.get('rule_score', 0),
                         case_data.get('ml_score'), case_data.get('final_score', 0),
                         case_data.get('risk_level', 'LOW'),
                         json.dumps(case_data.get('triggered_rules', [])),
                         case_data.get('explanation', '')))
                    count += 1
                except Exception as e:
                    print(f"⚠️ Error: {e}")
            print(f"✅ Inserted {count}/{len(cases_df)} cases")
            return count
    
    def log_action(self, case_id: str, action_type: str, notes: str = "", 
                   performed_by: str = "SYSTEM") -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT risk_level, final_score FROM risk_cases WHERE case_id = ?",
                          (case_id,))
            result = cursor.fetchone()
            if not result:
                return False
            risk_level, risk_score = result
            cursor.execute("""INSERT INTO risk_actions
                (case_id, action_type, risk_level_at_action, risk_score_at_action,
                 performed_by, notes) VALUES (?, ?, ?, ?, ?, ?)""",
                (case_id, action_type, risk_level, risk_score, performed_by, notes))
            cursor.execute("UPDATE risk_cases SET status = ? WHERE case_id = ?",
                          (action_type, case_id))
            self._log_audit(conn, event_type=f'ACTION_{action_type.upper()}',
                           case_id=case_id, action_taken=action_type,
                           risk_score=risk_score, classification_method='N/A',
                           details=notes)
            return True
    
    def bulk_action(self, case_ids: List[str], action_type: str, notes: str = "",
                    performed_by: str = "SYSTEM") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            success_count = 0
            for case_id in case_ids:
                try:
                    cursor.execute("SELECT risk_level, final_score FROM risk_cases WHERE case_id = ?",
                                  (case_id,))
                    result = cursor.fetchone()
                    if not result:
                        continue
                    risk_level, risk_score = result
                    cursor.execute("""INSERT INTO risk_actions
                        (case_id, action_type, risk_level_at_action, risk_score_at_action,
                         performed_by, notes) VALUES (?, ?, ?, ?, ?, ?)""",
                        (case_id, action_type, risk_level, risk_score, performed_by, notes))
                    cursor.execute("UPDATE risk_cases SET status = ? WHERE case_id = ?",
                                  (action_type, case_id))
                    self._log_audit(conn, event_type='BULK_ACTION', case_id=case_id,
                                   action_taken=action_type, risk_score=risk_score,
                                   classification_method='BULK_OPERATION',
                                   details=f"Bulk action. Notes: {notes}")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ Error: {e}")
            return success_count
    
    def _log_audit(self, conn: sqlite3.Connection, event_type: str, case_id: Optional[str] = None,
                   action_taken: str = "", risk_score: float = 0, classification_method: str = "",
                   rule_applied: str = "", user_id: str = "SYSTEM", details: str = ""):
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO audit_logs
            (event_type, case_id, action_taken, risk_score, classification_method,
             rule_applied, user_id, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_type, case_id, action_taken, risk_score, classification_method,
             rule_applied, user_id, details))
    
    def get_risk_cases(self, risk_level: Optional[str] = None, status: Optional[str] = None,
                       limit: int = 1000) -> pd.DataFrame:
        query = "SELECT * FROM risk_cases WHERE 1=1"
        params = []
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY final_score DESC LIMIT ?"
        params.append(limit)
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            if 'triggered_rules' in df.columns:
                df['triggered_rules'] = df['triggered_rules'].apply(
                    lambda x: json.loads(x) if x else [])
        return df
    
    def get_case_details(self, case_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM risk_cases WHERE case_id = ?", (case_id,))
            case = cursor.fetchone()
            if not case:
                return None
            case_dict = dict(case)
            case_dict['triggered_rules'] = json.loads(case_dict.get('triggered_rules', '[]'))
            cursor.execute("SELECT * FROM risk_actions WHERE case_id = ? ORDER BY timestamp DESC",
                          (case_id,))
            actions = [dict(row) for row in cursor.fetchall()]
            case_dict['actions'] = actions
            return case_dict
    
    def get_audit_logs(self, case_id: Optional[str] = None, event_type: Optional[str] = None,
                       limit: int = 1000) -> pd.DataFrame:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        if case_id:
            query += " AND case_id = ?"
            params.append(case_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        return df
    
    def get_statistics(self) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM risk_cases")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT risk_level, COUNT(*) as count FROM risk_cases GROUP BY risk_level")
            by_level = {row[0]: row[1] for row in cursor.fetchall()}
            cursor.execute("SELECT status, COUNT(*) as count FROM risk_cases GROUP BY status")
            by_status = {row[0]: row[1] for row in cursor.fetchall()}
            cursor.execute("SELECT COUNT(*) as total FROM audit_logs")
            audit_count = cursor.fetchone()[0]
        return {'total_cases': total, 'by_risk_level': by_level, 'by_status': by_status,
                'audit_log_entries': audit_count}
