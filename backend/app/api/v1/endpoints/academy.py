from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
import json
import os

from app.api.deps import get_db, get_current_agent
from app.core.security import decode_token, create_access_token, verify_password
from app.models.agent import Agent
from app.models.user import User
from app.models.academy import AgentTraining, AcademyModule, ExamAttempt, ModuleStatus
from app.schemas.academy import (
    ModuleProgressUpdate, ExamSubmission, CertificationRequest, TraineeLogin, TraineeToken
)




router = APIRouter(tags=["academy"])


@router.post("/login", response_model=TraineeToken)
def academy_login(payload: TraineeLogin, db: Session = Depends(get_db)):
    """Authenticate a Trainee or Agent using their official Code and PIN"""
    agent = db.query(Agent).filter(Agent.agent_code == payload.agent_code).first()
    if not agent or not agent.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_AGENT_CODE: Profile not discovered in the AgriTrust ledger."
        )
    
    if agent.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACADEMY_DISMISSAL: This profile has been terminated due to failure to meet certification standards."
        )
    
    # Verify PIN (which is the user's password)
    if not verify_password(payload.pin, agent.user.password_hash):
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_PIN: The security PIN provided does not match our records."
        )
    
    # Generate JWT using project-specific signature (subject, role)
    access_token = create_access_token(subject=str(agent.user.id), role="agent")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "agent_code": agent.agent_code
    }


@router.get("/my-progress")
def get_my_progress(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get agent's training progress with full curriculum content"""
    
    training = db.query(AgentTraining).filter(
        AgentTraining.agent_id == current_agent.id
    ).first()
    
    if not training:
        training = AgentTraining(agent_id=current_agent.id)
        db.add(training)
        db.commit()
        db.refresh(training)
    
    # Fetch all curriculum modules
    academy_content = db.query(AcademyModule).order_by(AcademyModule.module_number).all()
    
    # Merge content with agent progress
    modules_list = []
    for mod in academy_content:
        num = mod.module_number
        status = getattr(training, f"module_{num}_status")
        
        # (Assuming topics are tracked in training.topics_progress which is a dict of {topic_id: bool})
        topics_progress = training.topics_progress or {}
        
        topics_data = []
        if mod.topics:
            for topic in mod.topics:
                t_id = str(topic.get("id"))
                topics_data.append({
                    "id": t_id,
                    "title": topic.get("title"),
                    "is_completed": topics_progress.get(t_id, False)
                })

        modules_list.append({
            "id": str(mod.id),
            "module_number": num,
            "title": mod.title,
            "description": mod.description,
            "status": status,
            "score": getattr(training, f"module_{num}_score"),
            "is_locked": num > 1 and getattr(training, f"module_{num-1}_status") != ModuleStatus.COMPLETED,
            "topics": topics_data
        })

    modules_completed = sum([1 for m in modules_list if m["status"] == ModuleStatus.COMPLETED])
    overall_progress = (modules_completed / len(academy_content)) * 100 if academy_content else 0
    
    agent_name = "Agent Name"
    if current_agent.user:
        agent_name = current_agent.user.full_name
    
    return {
        "agent_id": current_agent.id,
        "agent_name": agent_name,
        "certification_level": training.certification_level,
        "overall_progress": overall_progress,
        "modules_completed": modules_completed,
        "modules": modules_list
    }

@router.get("/modules/{module_number}/content")
def get_module_content(
    module_number: int,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get module content - enforced strict sequence"""
    
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == current_agent.id).first()
    if not training:
        training = AgentTraining(agent_id=current_agent.id)
        db.add(training)
        db.commit()
        db.refresh(training)

    # Check sequence lock
    if module_number > 1:
        prev_status = getattr(training, f"module_{module_number-1}_status")
        if prev_status != ModuleStatus.COMPLETED:
            raise HTTPException(
                status_code=403, 
                detail=f"🔒 Module {module_number} is locked. Complete Module {module_number-1} first."
            )
    
    module = db.query(AcademyModule).filter(AcademyModule.module_number == module_number).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
        
    # Security: Strip correct_index before sending to client for high-stakes assessment
    questions = []
    if module.quiz_questions and "questions" in module.quiz_questions:
        for q in module.quiz_questions["questions"]:
            q_copy = q.copy()
            if "correct_index" in q_copy:
                del q_copy["correct_index"]
            questions.append(q_copy)

    return {
        "module_number": module.module_number,
        "title": module.title,
        "description": module.description,
        "topics": module.topics,
        "quiz_questions": {"questions": questions},
        "topics_progress": training.topics_progress or {},
        "quiz_passing_score": module.passing_score
    }


@router.get("/modules/{module_number}/topics/{topic_id}/content")
def get_topic_content(
    module_number: int,
    topic_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Read individual topic content with access verification"""
    
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == current_agent.id).first()
    if not training:
        raise HTTPException(status_code=403, detail="Academy registration required.")

    # Sequence Enforcement
    if module_number > 1:
        prev_status = getattr(training, f"module_{module_number-1}_status")
        if prev_status != ModuleStatus.COMPLETED:
             raise HTTPException(status_code=403, detail=f"🔒 Module {module_number} is locked.")

    module = db.query(AcademyModule).filter(AcademyModule.module_number == module_number).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
        
    topic = next((t for t in (module.topics or []) if str(t.get("id")) == topic_id), None)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found within this module")
        
    return {
        "module_number": module_number,
        "topic_id": topic_id,
        "title": topic.get("title"),
        "abstract": topic.get("abstract") or (topic.get("content", "")[:150] + "..." if topic.get("content") else "Confidential Field Intelligence."),
        "content": topic.get("content", "Content restricted or currently being updated.")
    }


@router.post("/modules/{module_number}/topics/{topic_id}/complete")
def complete_topic(
    module_number: int,
    topic_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Mark a specific topic as completed"""
    
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == current_agent.id).first()
    if not training:
        training = AgentTraining(agent_id=current_agent.id)
        db.add(training)
    
    # Check sequence lock
    if module_number > 1:
        prev_status = getattr(training, f"module_{module_number-1}_status")
        if prev_status != ModuleStatus.COMPLETED:
            raise HTTPException(status_code=403, detail="Module is locked.")

    # Update progress
    progress = dict(training.topics_progress or {})
    progress[topic_id] = True
    training.topics_progress = progress
    
    # Update module status to in_progress
    m_status_attr = f"module_{module_number}_status"
    if getattr(training, m_status_attr) == ModuleStatus.NOT_STARTED:
        setattr(training, m_status_attr, ModuleStatus.IN_PROGRESS)
        
    db.commit()
    
    return {"message": f"Topic {topic_id} marked as completed", "topics_progress": training.topics_progress}


@router.post("/modules/{module_number}/quiz/submit")
def submit_module_quiz(
    module_number: int,
    submission: ExamSubmission,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Securely grade module quiz on the server"""
    module = db.query(AcademyModule).filter(AcademyModule.module_number == module_number).first()
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == current_agent.id).first()
    
    if not module or not training:
        raise HTTPException(status_code=400, detail="Data error")

    # Grade the answers
    correct_count = 0
    total = len(module.quiz_questions.get("questions", []))
    results = []
    
    for q in module.quiz_questions.get("questions", []):
        q_id = str(q["id"])
        user_ans = submission.answers.get(q_id)
        if user_ans is None:
             user_ans = submission.answers.get(q["id"]) # Fallback for non-string keys
             
        is_correct = user_ans == q["correct_index"]
        if is_correct:
            correct_count += 1
        results.append({
            "id": q["id"],
            "is_correct": is_correct,
            "explanation": q["options"][q["correct_index"]] if not is_correct and q["options"] else "Correct"
        })

    score = (correct_count / total) * 100 if total > 0 else 0
    passed = score >= module.passing_score

    if passed:
        setattr(training, f"module_{module_number}_status", ModuleStatus.COMPLETED)
        setattr(training, f"module_{module_number}_score", score)
        db.commit()
    
    return {
        "passed": passed,
        "score": round(score, 1),
        "results": results,
        "message": "✅ Module Passed!" if passed else "❌ Score too low. Please retry."
    }


@router.post("/exam/mid/submit")
def submit_mid_exam(
    submission: ExamSubmission,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Submit mid-academy exam (100 questions, after Module 5)"""
    
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == current_agent.id).first()
    if not training or training.module_5_status != ModuleStatus.COMPLETED:
        raise HTTPException(status_code=403, detail="Complete first 5 modules before taking the Mid Exam")
    
    if training.mid_exam_attempts >= 2 and (not training.mid_exam_score or training.mid_exam_score < 75):
        raise HTTPException(status_code=403, detail="Maximum attempts reached for Mid Exam")
    
    score = (submission.correct_answers / 100) * 100
    
    attempt = ExamAttempt(
        agent_id=current_agent.id,
        exam_type="mid",
        score=score,
        answers=submission.answers,
        passed=score >= 75
    )
    db.add(attempt)
    
    training.mid_exam_score = score
    training.mid_exam_attempts += 1
    db.commit()
    
    if score >= 75:
        return {"passed": True, "score": score, "message": "✅ MID-ACADEMY EXAM PASSED! You may proceed to Module 6."}
    else:
        return {"passed": False, "score": score, "message": f"❌ Failed Mid Exam. {2 - training.mid_exam_attempts} attempts remaining."}


@router.get("/exam/final/questions")
def get_final_exam_questions(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Securely generate 200 random questions from the 1000-item pool and start 1-hour timer"""
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == current_agent.id).first()
    if not training or training.module_10_status != ModuleStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Prerequisite Violation: Complete all 10 learning modules before attempting the Final Exam."
        )

    # Load master pool from the physical assets
    pool_path = "data/training-materials/final_exam/master_question_pool_1000.json"
    if not os.path.exists(pool_path):
         pool_path = os.path.join(os.getcwd(), pool_path) # Absolute path fallback
         
    try:
        with open(pool_path, 'r', encoding='utf-8') as f:
            pool_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load master pool: {str(e)}")
    
    all_questions = pool_data.get("questions", [])
    if len(all_questions) < 200:
        raise HTTPException(status_code=500, detail="Incomplete question pool detected.")

    # Select 200 random questions for this session
    selected_questions = random.sample(all_questions, 200)
    
    # Store session state in DB
    training.last_exam_started_at = datetime.utcnow()
    training.active_exam_question_ids = [str(q["id"]) for q in selected_questions]
    db.commit()

    # Strip correct answers for transmission
    safe_questions = []
    for q in selected_questions:
        q_copy = q.copy()
        if "correct_index" in q_copy: del q_copy["correct_index"]
        if "rational" in q_copy: del q_copy["rational"]
        safe_questions.append(q_copy)

    return {
        "exam_id": "CERT-FINAL-LIVE",
        "total_questions": 200,
        "time_limit_minutes": 60,
        "started_at": training.last_exam_started_at,
        "expires_at": training.last_exam_started_at + timedelta(minutes=60),
        "questions": safe_questions
    }


@router.post("/exam/final/submit")
def submit_final_exam(
    submission: ExamSubmission,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Grade final certification exam with strict 1-hour time verification"""
    
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == current_agent.id).first()
    if not training or training.module_10_status != ModuleStatus.COMPLETED:
        raise HTTPException(status_code=403, detail="Prerequisite Violation")
    
    # Check Time Limit (1 Hour + 5 Min Grace for latency)
    if not training.last_exam_started_at:
        raise HTTPException(status_code=400, detail="Exam session not started. Call GET /questions first.")
    
    elapsed = datetime.utcnow() - training.last_exam_started_at
    if elapsed > timedelta(minutes=65):
        training.final_exam_attempts += 1
        db.commit()
        raise HTTPException(status_code=403, detail="⌛ Session Expired: The 60-minute time limit has been exceeded.")
    
    if training.final_exam_attempts >= 2 and (not training.final_exam_score or training.final_exam_score < 80):
        raise HTTPException(status_code=403, detail="Maximum of 2 attempts reached.")

    # Load master pool to verify answers server-side
    pool_path = "data/training-materials/final_exam/master_question_pool_1000.json"
    with open(pool_path, 'r', encoding='utf-8') as f:
        pool_data = json.load(f)
    
    pool_dict = {str(q["id"]): q for q in pool_data["questions"]}
    
    correct_count = 0
    total = 200
    results = []
    
    # Grade only against the questions issued for this session
    if not training.active_exam_question_ids:
         raise HTTPException(status_code=400, detail="Active question list missing.")

    for q_id in training.active_exam_question_ids:
        q_id_str = str(q_id)
        master_q = pool_dict.get(q_id_str)
        if not master_q: continue
        
        user_ans = submission.answers.get(q_id_str)
        is_correct = user_ans == master_q["correct_index"]
        
        if is_correct:
            correct_count += 1
        
        results.append({
            "id": q_id_str,
            "is_correct": is_correct,
            "rational": master_q.get("rational", "Refer to handbook.")
        })

    score = (correct_count / total) * 100
    passed = score >= 80
    
    attempt = ExamAttempt(
        agent_id=current_agent.id,
        exam_type="final",
        score=score,
        answers=submission.answers,
        passed=passed
    )
    db.add(attempt)
    
    training.final_exam_score = score
    training.final_exam_attempts += 1
    
    if passed:
        training.certification_level = "certified"
        training.certified_at = datetime.utcnow()
        training.certification_expires_at = datetime.utcnow() + timedelta(days=365)
        
        agent = db.query(Agent).filter(Agent.id == current_agent.id).first()
        agent.status = "active"
        db.commit()
        
        return {"passed": True, "score": score, "message": "🎉 CONGRATULATIONS! You are now a Certified AgriTrust Field Agent."}
    else:
        # If this was the last attempt, permanently fail the trainee
        if training.final_exam_attempts >= 2:
            agent = db.query(Agent).filter(Agent.id == current_agent.id).first()
            agent.status = "failed" # This boots them from the system
            db.commit()
            return {
                "passed": False, 
                "score": score, 
                "attempts_remaining": 0,
                "message": "🚫 ACADEMY DISMISSAL: You have failed your final attempt. Your candidacy has been terminated."
            }
            
        db.commit()
        return {
            "passed": False, 
            "score": score, 
            "attempts_remaining": 2 - training.final_exam_attempts,
            "message": f"❌ FAILED: You did not meet the 80% threshold. You have {2 - training.final_exam_attempts} attempt remaining."
        }



@router.get("/certificate")
def download_certificate(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Generate and download certification PDF with QR verification"""
    training = db.query(AgentTraining).filter(AgentTraining.agent_id == current_agent.id).first()
    if not training or training.certification_level == "trainee":
        raise HTTPException(status_code=403, detail="Not certified yet")
    
    from app.services.certificate_service import certificate_service
    
    cert_url = certificate_service.generate_agent_certificate(
        agent_name=current_agent.user.full_name,
        agent_id=current_agent.id,
        agent_code=current_agent.agent_code,
        issue_date=training.certified_at or datetime.utcnow(),
        expiry_date=training.certification_expires_at
    )
    
    return {"certificate_url": cert_url, "valid_until": training.certification_expires_at}

