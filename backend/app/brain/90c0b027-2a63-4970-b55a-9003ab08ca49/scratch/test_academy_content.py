import sys
import os
from sqlalchemy.orm import Session
import json

# Ensure we can import from app
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import SessionLocal
from app.models.academy import AcademyModule

def check_academy():
    db = SessionLocal()
    try:
        print("--- [TEST] Academy Content Verification ---")
        
        # Check Module 1
        m1 = db.query(AcademyModule).filter(AcademyModule.module_number == 1).first()
        if m1:
            print(f"Module 1 Found: {m1.title}")
            for topic in m1.topics:
               if topic['id'] == '1.7':
                   print(f"[OK] Topic 1.7 Found: {topic['title']}")
        else:
            print("[FAIL] Module 1 NOT FOUND")

        # Check Module 2
        m2 = db.query(AcademyModule).filter(AcademyModule.module_number == 2).first()
        if m2:
            print(f"Module 2 Found: {m2.title}")
            for topic in m2.topics:
               if topic['id'] == '2.1':
                   print(f"[OK] Topic 2.1 Found: {topic['title']}")
                   if "Trust Account" in topic['content']:
                       print("[OK] Topic 2.1 contains Crystal-Clear Storage info.")
        else:
            print("[FAIL] Module 2 NOT FOUND")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_academy()
