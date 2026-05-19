"""
Data Validation Script for Onboarding/Recruitment Unification

This script validates the data structure after the onboarding/recruitment service unification.
Since the unified service uses the same underlying data models (AgentApplication, AgentContract,
AgentTrainingProgress, ShadowingLog), no actual data migration is needed.

This script performs validation and cleanup:
1. Ensures all AgentApplication records have valid user references
2. Ensures Agent records exist for certified agents
3. Validates training module progress consistency
4. Checks for orphaned records

Run this script after deploying the unified AgentOnboardingService.
"""
import sys
import os
from datetime import datetime
import uuid

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.db.base import Base

from app.models.recruitment import AgentApplication, ApplicationStatus
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentStatus, AgentSpecialization
from app.models.onboarding import AgentContract, AgentTrainingProgress, ShadowingLog
from app.models.academy import AgentTraining


def validate_data(database_url: str):
    """Validate onboarding/recruitment data structure."""
    
    print("Starting onboarding data validation...")
    print(f"Database: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Statistics
        stats = {
            "total_applications": 0,
            "applications_without_user": 0,
            "certified_without_agent": 0,
            "orphaned_contracts": 0,
            "orphaned_progress": 0,
            "orphaned_shadowing_logs": 0,
            "training_without_agent": 0,
            "issues_fixed": 0
        }
        
        # 1. Validate AgentApplications
        print("\n[1/6] Validating AgentApplication records...")
        applications = db.query(AgentApplication).all()
        stats["total_applications"] = len(applications)
        
        for app in applications:
            # Check if user exists
            if app.user_id:
                user = db.query(User).filter(User.id == app.user_id).first()
                if not user:
                    stats["applications_without_user"] += 1
                    print(f"  ⚠️ Application {app.id} references non-existent user {app.user_id}")
            else:
                # Try to find user by phone number
                if app.phone_number:
                    user = db.query(User).filter(User.phone_number == app.phone_number).first()
                    if user:
                        app.user_id = user.id
                        stats["issues_fixed"] += 1
                        print(f"  ✅ Fixed: Application {app.id} linked to user {user.id}")
        
        # 2. Validate certified agents have Agent records
        print("\n[2/6] Validating certified agents have Agent records...")
        certified_apps = db.query(AgentApplication).filter(
            AgentApplication.status == ApplicationStatus.CERTIFIED
        ).all()
        
        for app in certified_apps:
            if app.user_id:
                agent = db.query(Agent).filter(Agent.user_id == app.user_id).first()
                if not agent:
                    stats["certified_without_agent"] += 1
                    print(f"  ⚠️ Certified application {app.id} has no Agent record")
                    
                    # Auto-fix: Create agent record
                    user = db.query(User).filter(User.id == app.user_id).first()
                    if user:
                        agent = Agent(
                            user_id=user.id,
                            agent_code=f"AGT{str(uuid.uuid4())[:5]}".upper(),
                            status=AgentStatus.ACTIVE,
                            province=app.province,
                            district=app.district,
                            specialization=AgentSpecialization.FIELD_SUPPORT
                        )
                        db.add(agent)
                        stats["issues_fixed"] += 1
                        print(f"  ✅ Fixed: Created Agent record for user {user.id}")
        
        # 3. Validate AgentContracts
        print("\n[3/6] Validating AgentContract records...")
        contracts = db.query(AgentContract).all()
        
        for contract in contracts:
            app = db.query(AgentApplication).filter(
                AgentApplication.id == contract.application_id
            ).first()
            if not app:
                stats["orphaned_contracts"] += 1
                print(f"  ⚠️ Contract {contract.id} references non-existent application {contract.application_id}")
        
        # 4. Validate AgentTrainingProgress
        print("\n[4/6] Validating AgentTrainingProgress records...")
        progress_records = db.query(AgentTrainingProgress).all()
        
        for progress in progress_records:
            app = db.query(AgentApplication).filter(
                AgentApplication.id == progress.application_id
            ).first()
            if not app:
                stats["orphaned_progress"] += 1
                print(f"  ⚠️ Progress {progress.id} references non-existent application {progress.application_id}")
        
        # 5. Validate ShadowingLogs
        print("\n[5/6] Validating ShadowingLog records...")
        shadowing_logs = db.query(ShadowingLog).all()
        
        for log in shadowing_logs:
            app = db.query(AgentApplication).filter(
                AgentApplication.id == log.application_id
            ).first()
            if not app:
                stats["orphaned_shadowing_logs"] += 1
                print(f"  ⚠️ ShadowingLog {log.id} references non-existent application {log.application_id}")
        
        # 6. Validate AgentTraining has Agent references
        print("\n[6/6] Validating AgentTraining records...")
        training_records = db.query(AgentTraining).all()
        
        for training in training_records:
            agent = db.query(Agent).filter(Agent.id == training.agent_id).first()
            if not agent:
                stats["training_without_agent"] += 1
                print(f"  ⚠️ Training {training.id} references non-existent agent {training.agent_id}")
        
        # Commit fixes
        db.commit()
        
        # Print summary
        print("\n" + "="*50)
        print("Validation Complete!")
        print("="*50)
        print(f"Total Applications: {stats['total_applications']}")
        print(f"Applications without user: {stats['applications_without_user']}")
        print(f"Certified without Agent record: {stats['certified_without_agent']}")
        print(f"Orphaned Contracts: {stats['orphaned_contracts']}")
        print(f"Orphaned Progress Records: {stats['orphaned_progress']}")
        print(f"Orphaned Shadowing Logs: {stats['orphaned_shadowing_logs']}")
        print(f"Training without Agent: {stats['training_without_agent']}")
        print(f"Issues Fixed: {stats['issues_fixed']}")
        print("="*50)
        
        if stats["issues_fixed"] > 0:
            print(f"\n✅ Successfully fixed {stats['issues_fixed']} data issues.")
        
        total_issues = (
            stats["applications_without_user"] +
            stats["certified_without_agent"] +
            stats["orphaned_contracts"] +
            stats["orphaned_progress"] +
            stats["orphaned_shadowing_logs"] +
            stats["training_without_agent"]
        )
        
        if total_issues > 0:
            print(f"\n⚠️ {total_issues} data issues remain that may need manual review.")
        else:
            print("\n✅ All data validation checks passed!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Validation failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/zimagritrust')
    
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    
    validate_data(database_url)
