from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json
import os

from app.db.session import SessionLocal
from app.models.academy import AcademyModule, AgentTraining, ModuleStatus, ExamAttempt

class TrainingService:
    """
    AgriTrust Agent Academy Service.
    Manages the 10-module training curriculum and certification exams.
    """
    def __init__(self):
        self.pass_threshold = 0.80

    def get_module_content(self, module_number: int, db: Session) -> Optional[Dict]:
        """
        Fetches module details from the database.
        """
        module = db.query(AcademyModule).filter(AcademyModule.module_number == module_number).first()
        if not module:
            return None
            
        return {
            "module_number": module.module_number,
            "title": module.title,
            "description": module.description,
            "duration_hours": module.duration_hours,
            "handbook_url": module.content_url or f"/docs/training/module_{module_number}.pdf",
            "is_mandatory": module.is_mandatory
        }

    def get_all_modules(self, db: Session) -> List[Dict]:
        modules = db.query(AcademyModule).order_by(AcademyModule.order).all()
        return [
            {
                "number": m.module_number,
                "title": m.title,
                "duration": m.duration_hours
            } for m in modules
        ]

    def evaluate_exam(self, agent_id: str, exam_type: str, correct_answers: int, total_questions: int, db: Session) -> Dict:
        """
        Processes and records exam attempts.
        """
        score = (correct_answers / total_questions) * 100
        threshold = 75.0 if exam_type == "mid" else 80.0
        passed = score >= threshold
        
        # Record attempt (Simplified, as actual saving is handled in the endpoint too)
        # This service can be used for shared logic
        
        return {
            "score": score,
            "passed": passed,
            "threshold": threshold,
            "next_step": "Continue to Module 6" if exam_type == "mid" and passed else ("Field Training" if passed else "Review Content")
        }

    def log_to_ledger(self, action: str, data: Dict):
        """
        Simulates writing a record to the AgriTrust Sovereign Ledger (Blockchain).
        In production, this would interface with a distributed ledger (e.g. Hyperledger Fabric).
        """
        ledger_path = "sovereign_ledger.json"
        entry = {
            "timestamp": str(datetime.utcnow()),
            "action": action,
            "data": data,
            "hash": str(uuid.uuid4().hex[:16]) # Mock hash
        }
        
        ledger = []
        if os.path.exists(ledger_path):
            with open(ledger_path, "r") as f:
                try:
                    ledger = json.load(f)
                except:
                    ledger = []
        
        ledger.append(entry)
        with open(ledger_path, "w") as f:
            json.dump(ledger, f, indent=4)
        
        print(f"🔒 [LEDGER] Recorded: {action}")

training_service = TrainingService()


