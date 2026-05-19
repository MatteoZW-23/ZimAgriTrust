"""
Migration script to load training materials from data/training-materials
into the new classroom database system.
"""
import sys
import os
from pathlib import Path
import json
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.classroom import (
    Course, CourseTopic, Resource, QuizQuestion,
    ResourceType, QuestionType, EnrollmentStatus
)


def load_training_materials(base_path: Path = None):
    """Load training materials from the training-materials directory."""
    if base_path is None:
        # Try multiple possible paths
        possible_paths = [
            Path("/app/data/training-materials"),  # Docker container path (mounted)
            Path("/data/training-materials"),  # Alternative Docker path
            Path(__file__).parent.parent.parent / "data" / "training-materials",  # Local development
            Path("C:/Users/MJ/Desktop/Agric/data/training-materials"),  # Windows path
        ]
        for path in possible_paths:
            if path.exists():
                base_path = path
                break
        else:
            base_path = possible_paths[0]  # Default to first option
    
    if not base_path.exists():
        print(f"Error: Training materials directory not found: {base_path}")
        return
    
    db = SessionLocal()
    
    try:
        # Module mapping
        module_map = {
            "module_1_platform_operations": {
                "title": "Platform Operations",
                "description": "Learn the fundamentals of ZimAgritrust platform operations",
                "module_number": 1
            },
            "module_2_escrow_and_payment": {
                "title": "Escrow and Payment",
                "description": "Understand escrow transactions and payment processing",
                "module_number": 2
            },
            "module_3_crop_verification_quality": {
                "title": "Crop Verification and Quality",
                "description": "Learn to verify crop quality and grade produce",
                "module_number": 3
            },
            "module_4_dispute_resolution": {
                "title": "Dispute Resolution",
                "description": "Handle and resolve buyer-farmer disputes",
                "module_number": 4
            },
            "module_5_trust_reputation": {
                "title": "Trust and Reputation",
                "description": "Build and maintain trust in the marketplace",
                "module_number": 5
            },
            "module_6_ethics_integrity": {
                "title": "Ethics and Integrity",
                "description": "Professional ethics and integrity standards",
                "module_number": 6
            },
            "module_7_rural_finance_credit": {
                "title": "Rural Finance and Credit",
                "description": "Understand rural finance and credit systems",
                "module_number": 7
            },
            "module_8_legal_regulatory": {
                "title": "Legal and Regulatory",
                "description": "Legal requirements and regulations",
                "module_number": 8
            },
            "module_9_agtech_iot": {
                "title": "AgTech and IoT",
                "description": "Agricultural technology and IoT systems",
                "module_number": 9
            },
            "module_10_customer_excellence": {
                "title": "Customer Excellence",
                "description": "Delivering excellent customer service",
                "module_number": 10
            },
            "final_exam": {
                "title": "Final Assessment",
                "description": "Comprehensive final exam for certification",
                "module_number": 11
            }
        }
        
        courses_created = 0
        topics_created = 0
        resources_created = 0
        questions_created = 0
        
        for folder_name, module_info in module_map.items():
            folder_path = base_path / folder_name
            
            if not folder_path.exists():
                print(f"Skipping {folder_name} - directory not found")
                continue
            
            print(f"\nProcessing: {folder_name}")
            
            # Check if course already exists
            existing_course = db.query(Course).filter(
                Course.module_number == module_info["module_number"]
            ).first()
            
            if existing_course:
                print(f"  Course already exists, skipping...")
                continue
            
            # Create course
            course = Course(
                title=module_info["title"],
                description=module_info["description"],
                module_number=module_info["module_number"],
                passing_score=80.0,
                estimated_hours=2.0,
                is_active=True
            )
            db.add(course)
            db.flush()
            db.refresh(course)
            courses_created += 1
            print(f"  Created course: {course.title}")
            
            # Create topic
            topic = CourseTopic(
                course_id=course.id,
                topic_number=1,
                title=f"{module_info['title']} - Complete",
                order_sequence=1
            )
            db.add(topic)
            db.flush()
            db.refresh(topic)
            topics_created += 1
            print(f"  Created topic: {topic.title}")
            
            # Look for handbook file
            handbook_files = list(folder_path.glob("handbook_*.txt"))
            if handbook_files:
                handbook_file = handbook_files[0]
                try:
                    with open(handbook_file, 'r', encoding='utf-8') as f:
                        handbook_content = f.read()
                    
                    # Create resource for handbook
                    resource = Resource(
                        course_id=course.id,
                        topic_id=topic.id,
                        resource_type=ResourceType.DOCUMENT,
                        title=f"Training Handbook - {module_info['title']}",
                        content_text=handbook_content,
                        order_sequence=1
                    )
                    db.add(resource)
                    resources_created += 1
                    print(f"  Added handbook resource")
                except Exception as e:
                    print(f"  Error reading handbook: {e}")
            
            # Look for quiz file
            quiz_files = list(folder_path.glob("quiz_*.json"))
            if quiz_files:
                quiz_file = quiz_files[0]
                try:
                    with open(quiz_file, 'r', encoding='utf-8') as f:
                        quiz_data = json.load(f)
                    
                    # Create quiz resource
                    quiz_resource = Resource(
                        course_id=course.id,
                        topic_id=topic.id,
                        resource_type=ResourceType.QUIZ,
                        title=f"Quiz - {module_info['title']}",
                        time_limit_minutes=30,
                        passing_score=80.0,
                        order_sequence=2
                    )
                    db.add(quiz_resource)
                    db.flush()
                    db.refresh(quiz_resource)
                    resources_created += 1
                    print(f"  Created quiz resource")
                    
                    # Load quiz questions
                    if isinstance(quiz_data, dict) and 'questions' in quiz_data:
                        questions = quiz_data['questions']
                    elif isinstance(quiz_data, list):
                        questions = quiz_data
                    else:
                        questions = []
                    
                    for idx, q_data in enumerate(questions):
                        question_text = q_data.get('question', q_data.get('question_text', ''))
                        q_type_str = q_data.get('type', q_data.get('question_type', 'multiple_choice'))
                        
                        # Map question types
                        if q_type_str.lower() in ['multiple_choice', 'mcq']:
                            q_type = QuestionType.MULTIPLE_CHOICE
                        elif q_type_str.lower() in ['true_false', 'tf']:
                            q_type = QuestionType.TRUE_FALSE
                        elif q_type_str.lower() in ['essay']:
                            q_type = QuestionType.ESSAY
                        else:
                            q_type = QuestionType.MULTIPLE_CHOICE
                        
                        options = q_data.get('options', [])
                        correct_answer = q_data.get('correct_answer', q_data.get('answer'))
                        points = q_data.get('points', 1)
                        
                        question = QuizQuestion(
                            resource_id=quiz_resource.id,
                            question_text=question_text,
                            question_type=q_type,
                            options=options if options else None,
                            correct_answer=str(correct_answer) if correct_answer else None,
                            points=points,
                            order_sequence=idx
                        )
                        db.add(question)
                        questions_created += 1
                    
                    print(f"  Added {len(questions) if isinstance(questions, list) else 0} quiz questions")
                    
                except Exception as e:
                    print(f"  Error reading quiz: {e}")
        
        db.commit()
        
        print(f"\n" + "="*50)
        print("Migration completed successfully!")
        print(f"  Courses created: {courses_created}")
        print(f"  Topics created: {topics_created}")
        print(f"  Resources created: {resources_created}")
        print(f"  Quiz questions created: {questions_created}")
        print("="*50)
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Migrating training materials to classroom database...")
    load_training_materials()
