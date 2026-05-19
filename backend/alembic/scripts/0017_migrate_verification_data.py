"""
Migration script: Migrate data from legacy DocumentVerificationRequest to new DocumentVerificationRecord

This script migrates all existing verification data from the legacy system to the new verification workflow system.
It handles:
- Document records
- User verification summaries
- Verification queue entries
- Audit logs

Run this migration after deploying the new verification workflow system.
"""
from datetime import datetime
import uuid
import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.db.base import Base
from app.models.verification import (
    DocumentVerificationRecord, UserVerificationSummary,
    VerificationQueue, VerificationAuditLog,
    VerificationStatus, DocumentType, ReviewerRole
)
from app.models.user import User, UserRole
from app.api.v1.endpoints.verification import IDVerificationRequest as LegacyDocumentVerificationRequest

def map_document_type(legacy_type: str) -> DocumentType:
    """Map legacy document type to new DocumentType enum."""
    type_mapping = {
        'national_id': DocumentType.NATIONAL_ID,
        'id': DocumentType.NATIONAL_ID,
        'id_card': DocumentType.NATIONAL_ID,
        'passport': DocumentType.PASSPORT,
        'passport_id': DocumentType.PASSPORT,
        'drivers_license': DocumentType.DRIVERS_LICENSE,
        'driving_license': DocumentType.DRIVERS_LICENSE,
        'driver_license': DocumentType.DRIVERS_LICENSE,
        'proof_of_address': DocumentType.PROOF_OF_ADDRESS,
        'farm_registration': DocumentType.FARM_REGISTRATION,
        'business_registration': DocumentType.BUSINESS_REGISTRATION,
        'tax_clearance': DocumentType.TAX_CLEARANCE,
        'agent_application': DocumentType.AGENT_APPLICATION,
        'vehicle_registration': DocumentType.VEHICLE_REGISTRATION,
    }
    return type_mapping.get(legacy_type.lower().replace('-', '_').replace(' ', '_'), DocumentType.NATIONAL_ID)


def map_status(legacy_status: str) -> VerificationStatus:
    """Map legacy status to new VerificationStatus enum."""
    status_mapping = {
        'pending': VerificationStatus.PENDING_ADMIN,
        'approved': VerificationStatus.APPROVED,
        'rejected': VerificationStatus.REJECTED,
        'under_review': VerificationStatus.UNDER_REVIEW,
    }
    return status_mapping.get(legacy_status.lower(), VerificationStatus.PENDING_ADMIN)


def map_reviewer_role(legacy_role: str) -> ReviewerRole:
    """Map legacy reviewer role to new ReviewerRole enum."""
    role_mapping = {
        'admin': ReviewerRole.ADMIN,
        'agent': ReviewerRole.AGENT,
    }
    return role_mapping.get(legacy_role.lower(), ReviewerRole.ADMIN)


def migrate_document_record(db: Session, legacy: LegacyDocumentVerificationRequest) -> DocumentVerificationRecord:
    """Migrate a single legacy document record to the new format."""
    
    # Map document type
    try:
        doc_type = map_document_type(getattr(legacy, 'document_type', 'national_id'))
    except (ValueError, AttributeError):
        doc_type = DocumentType.NATIONAL_ID
    
    # Map status
    status = map_status(legacy.status)
    
    # Create new record
    new_record = DocumentVerificationRecord(
        id=uuid.uuid4(),  # Generate new UUID
        user_id=legacy.user_id,
        document_type=doc_type,
        document_label=getattr(legacy, 'document_type', 'national_id').replace('_', ' ').title(),
        status=status,
        current_stage=getattr(legacy, 'review_stage', 'admin_review'),
        required_reviewer_role=map_reviewer_role(getattr(legacy, 'reviewer_role', 'admin')),
        
        # File URLs (copy from legacy)
        file_url=getattr(legacy, 'primary_url', None) or legacy.front_url,
        back_file_url=legacy.back_url,
        selfie_file_url=legacy.selfie_url,
        supporting_file_url=getattr(legacy, 'supporting_url', None),
        
        # Document data
        document_number=legacy.national_id_number or getattr(legacy, 'document_reference', None),
        issuing_authority=None,
        issue_date=None,
        expiry_date=None,
        
        # Verification metadata
        fraud_score=0,
        fraud_flags=[],
        duplicate_check_passed=True,
        auto_screen_score=getattr(legacy, 'confidence_score', 50),
        auto_screen_passed=not getattr(legacy, 'manual_review_required', True),
        manual_review_required=getattr(legacy, 'manual_review_required', False),
        
        # Review data
        agent_reviewer_id=None,
        agent_reviewed_at=None,
        agent_decision=None,
        agent_notes=None,
        admin_reviewer_id=legacy.reviewer_id,
        admin_reviewed_at=legacy.reviewed_at,
        admin_decision='approve' if legacy.status == 'approved' else 'reject' if legacy.status == 'rejected' else None,
        admin_notes=legacy.reviewer_note,
        
        # Resubmission data
        resubmission_count=getattr(legacy, 'attempts', 1) - 1,
        max_resubmissions=3,
        resubmission_deadline=None,
        rejection_reason=getattr(legacy, 'rejected_reason', None),
        rejection_category=None,
        
        # Trust score
        trust_score_delta=getattr(legacy, 'trust_score_delta', 0),
        trust_score_applied=legacy.status == 'approved',
        
        # Timestamps
        submitted_at=legacy.submitted_at,
        created_at=legacy.submitted_at or datetime.utcnow(),
        updated_at=legacy.reviewed_at or legacy.submitted_at or datetime.utcnow(),
    )
    
    db.add(new_record)
    return new_record


def migrate_user_summary(db: Session, user_id: uuid.UUID):
    """Create or update user verification summary based on migrated documents."""
    
    # Get all documents for this user
    documents = db.query(DocumentVerificationRecord).filter(
        DocumentVerificationRecord.user_id == user_id
    ).all()
    
    if not documents:
        return
    
    # Check if summary already exists
    summary = db.query(UserVerificationSummary).filter(
        UserVerificationSummary.user_id == user_id
    ).first()
    
    if not summary:
        # Get user role
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        summary = UserVerificationSummary(
            user_id=user_id,
            role=user.role,
            overall_status=VerificationStatus.PENDING_ADMIN,
            verification_level=0,
        )
        db.add(summary)
    
    # Update summary based on documents
    identity_approved = any(
        d.document_type in [DocumentType.NATIONAL_ID, DocumentType.PASSPORT] and d.status == VerificationStatus.APPROVED
        for d in documents
    )
    
    if identity_approved:
        summary.identity_status = VerificationStatus.APPROVED
        summary.identity_verified_at = datetime.utcnow()
        summary.identity_document_type = 'national_id'
    
    # Update verification level
    approved_count = sum(1 for d in documents if d.status == VerificationStatus.APPROVED)
    summary.verification_level = min(5, approved_count)
    
    # Update overall status
    if all(d.status == VerificationStatus.APPROVED for d in documents):
        summary.overall_status = VerificationStatus.APPROVED
    elif any(d.status == VerificationStatus.REJECTED for d in documents):
        summary.overall_status = VerificationStatus.REJECTED
    else:
        summary.overall_status = VerificationStatus.PENDING_ADMIN
    
    # Update permissions
    summary.can_list_products = identity_approved
    summary.can_make_purchases = identity_approved
    summary.can_receive_payments = identity_approved
    summary.can_access_loans = summary.verification_level >= 3
    summary.can_use_platform_services = identity_approved


def migrate_queue_entry(db: Session, legacy: LegacyDocumentVerificationRequest, new_record: DocumentVerificationRecord):
    """Create queue entry for migrated document if still pending."""
    
    if legacy.status != 'pending':
        return
    
    # Get user
    user = db.query(User).filter(User.id == legacy.user_id).first()
    if not user:
        return
    
    # Check if queue entry already exists
    existing = db.query(VerificationQueue).filter(
        VerificationQueue.document_id == new_record.id
    ).first()
    
    if existing:
        return
    
    # Create queue entry
    queue_entry = VerificationQueue(
        document_id=new_record.id,
        user_id=legacy.user_id,
        status='pending',
        required_role=map_reviewer_role(legacy.reviewer_role) if legacy.reviewer_role else ReviewerRole.ADMIN,
        document_type=new_record.document_type.value,
        user_role=user.role.value,
        priority=5,
        is_urgent=False,
        submitted_at=legacy.submitted_at,
        due_by=legacy.submitted_at.replace(hour=legacy.submitted_at.hour + 24) if legacy.submitted_at else datetime.utcnow(),
    )
    
    db.add(queue_entry)


def migrate_audit_log(db: Session, legacy: LegacyDocumentVerificationRequest, new_record: DocumentVerificationRecord):
    """Create audit log entry for migrated document."""
    
    if legacy.reviewed_at and legacy.reviewer_id:
        # Check if audit log already exists
        existing = db.query(VerificationAuditLog).filter(
            VerificationAuditLog.document_id == new_record.id,
            VerificationAuditLog.action == 'admin_review'
        ).first()
        
        if existing:
            return
        
        # Create audit log
        audit_log = VerificationAuditLog(
            document_id=new_record.id,
            user_id=legacy.user_id,
            reviewer_id=legacy.reviewer_id,
            action='admin_review',
            decision=legacy.status,
            notes=legacy.reviewer_note,
            created_at=legacy.reviewed_at,
        )
        
        db.add(audit_log)


def run_migration(database_url: str):
    """Run the complete migration."""
    
    print("Starting verification data migration...")
    print(f"Database: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if legacy table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if 'id_verification_requests' not in inspector.get_table_names():
            print("Legacy table 'id_verification_requests' not found. Migration not needed.")
            return
        
        # Get all legacy records
        legacy_records = db.query(LegacyDocumentVerificationRequest).all()
        
        if not legacy_records:
            print("No legacy records found. Migration complete.")
            return
        
        print(f"Found {len(legacy_records)} legacy records to migrate.")
        
        # Track statistics
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        # Migrate each record
        for legacy in legacy_records:
            try:
                # Check if already migrated (by user_id and submitted_at)
                existing = db.query(DocumentVerificationRecord).filter(
                    DocumentVerificationRecord.user_id == legacy.user_id,
                    DocumentVerificationRecord.submitted_at == legacy.submitted_at
                ).first()
                
                if existing:
                    print(f"Skipping already migrated record for user {legacy.user_id}")
                    skipped_count += 1
                    continue
                
                # Migrate document record
                new_record = migrate_document_record(db, legacy)
                db.flush()  # Get the ID
                
                # Migrate queue entry
                migrate_queue_entry(db, legacy, new_record)
                
                # Migrate audit log
                migrate_audit_log(db, legacy, new_record)
                
                # Update user summary
                migrate_user_summary(db, legacy.user_id)
                
                migrated_count += 1
                print(f"Migrated record {migrated_count}/{len(legacy_records)}")
                
            except Exception as e:
                error_count += 1
                print(f"Error migrating record for user {legacy.user_id}: {e}")
                db.rollback()
                continue
        
        # Commit all changes
        db.commit()
        
        print("\n" + "="*50)
        print("Migration Complete!")
        print(f"Total legacy records: {len(legacy_records)}")
        print(f"Successfully migrated: {migrated_count}")
        print(f"Skipped (already migrated): {skipped_count}")
        print(f"Errors: {error_count}")
        print("="*50)
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/zimagritrust')
    
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    
    run_migration(database_url)
