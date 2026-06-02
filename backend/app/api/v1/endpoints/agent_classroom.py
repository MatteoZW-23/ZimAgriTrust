import uuid
import random
import json
import hashlib
import base64
import os
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, get_current_agent
from app.models.agent import Agent
from app.models.classroom import (
    Course, CourseTopic, Resource, QuizQuestion, Enrollment,
    TopicProgress, QuizAttempt, EssayAnswer, Announcement,
    ResourceType, QuestionType, EnrollmentStatus
)
from app.schemas.classroom import (
    AgentCourseResponse, AgentCourseDetailResponse, AgentTopicResponse,
    AgentResourceResponse, QuizSubmission, QuizResultResponse,
    AnnouncementResponse
)

router = APIRouter()


# ============ COURSE LIST ============

@router.get("/courses", response_model=List[AgentCourseResponse])
def list_courses(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get all courses for the agent with progress and locking status"""
    courses = db.query(Course).order_by(Course.module_number).all()
    
    response = []
    for course in courses:
        # Check if enrolled
        enrollment = db.query(Enrollment).filter(
            Enrollment.agent_id == current_agent.id,
            Enrollment.course_id == course.id
        ).first()
        
        # Calculate progress
        progress_percentage = 0.0
        grade = None
        is_locked = False
        lock_message = None
        
        if enrollment:
            total_topics = len(course.topics)
            completed_topics = db.query(TopicProgress).filter(
                TopicProgress.enrollment_id == enrollment.id,
                TopicProgress.is_completed == True
            ).count()
            progress_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
            grade = enrollment.overall_score
        
        # Progressive unlocking: Module N requires Module N-1 to be completed
        if course.module_number > 1:
            prev_course = db.query(Course).filter(
                Course.module_number == course.module_number - 1
            ).first()
            if prev_course:
                prev_enrollment = db.query(Enrollment).filter(
                    Enrollment.agent_id == current_agent.id,
                    Enrollment.course_id == prev_course.id
                ).first()
                if not prev_enrollment or prev_enrollment.status != EnrollmentStatus.COMPLETED:
                    is_locked = True
                    lock_message = f"Complete Module {course.module_number - 1} first"
        
        response.append(AgentCourseResponse(
            id=str(course.id),
            title=course.title,
            description=course.description,
            module_number=course.module_number,
            progress_percentage=progress_percentage,
            grade=grade,
            is_locked=is_locked,
            lock_message=lock_message
        ))
    
    return response


@router.get("/courses/{course_id}", response_model=AgentCourseDetailResponse)
def get_course_detail(
    course_id: uuid.UUID,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get detailed course information with topics and resources"""
    course = db.query(Course).options(
        joinedload(Course.topics).joinedload(CourseTopic.resources).joinedload(Resource.quiz_questions)
    ).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.agent_id == current_agent.id,
        Enrollment.course_id == course_id
    ).first()
    
    # Calculate progress
    progress_percentage = 0.0
    is_locked = False
    
    if enrollment:
        total_topics = len(course.topics)
        completed_topics = db.query(TopicProgress).filter(
            TopicProgress.enrollment_id == enrollment.id,
            TopicProgress.is_completed == True
        ).count()
        progress_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
    
    # Progressive unlocking
    if course.module_number > 1:
        prev_course = db.query(Course).filter(
            Course.module_number == course.module_number - 1
        ).first()
        if prev_course:
            prev_enrollment = db.query(Enrollment).filter(
                Enrollment.agent_id == current_agent.id,
                Enrollment.course_id == prev_course.id
            ).first()
            if not prev_enrollment or prev_enrollment.status != EnrollmentStatus.COMPLETED:
                is_locked = True
    
    if is_locked:
        raise HTTPException(status_code=403, detail=f"Complete Module {course.module_number - 1} first")
    
    # Get announcements
    announcements = db.query(Announcement).filter(
        Announcement.course_id == course_id
    ).order_by(Announcement.created_at.desc()).limit(10).all()
    
    # Build topics with locking status
    topic_responses = []
    for topic in course.topics:
        topic_completed = False
        if enrollment:
            topic_progress = db.query(TopicProgress).filter(
                TopicProgress.enrollment_id == enrollment.id,
                TopicProgress.topic_id == topic.id
            ).first()
            topic_completed = topic_progress.is_completed if topic_progress else False
        
        # Topic-level locking: all previous topics must be completed
        topic_locked = False
        if topic.order_sequence > 0:
            prev_topic = next((t for t in course.topics if t.order_sequence == topic.order_sequence - 1), None)
            if prev_topic and enrollment:
                prev_progress = db.query(TopicProgress).filter(
                    TopicProgress.enrollment_id == enrollment.id,
                    TopicProgress.topic_id == prev_topic.id
                ).first()
                if not prev_progress or not prev_progress.is_completed:
                    topic_locked = True
        
        # Build resources
        resource_responses = []
        for resource in topic.resources:
            resource_completed = False
            resource_locked = topic_locked
            
            # Quiz unlocks when the topic itself is not locked (i.e. topic is accessible).
            # Do NOT require topic_completed — that creates a circular deadlock where
            # you need to complete the topic to take the quiz but the quiz completes the topic.
            if resource.resource_type == ResourceType.QUIZ:
                resource_locked = topic_locked  # locked only if the whole topic is locked
            
            quiz_info = None
            if resource.resource_type == ResourceType.QUIZ:
                quiz_info = {
                    "time_limit_minutes": resource.time_limit_minutes,
                    "passing_score": resource.passing_score,
                    "question_count": len(resource.quiz_questions)
                }
            
            resource_responses.append(AgentResourceResponse(
                id=str(resource.id),
                resource_type=resource.resource_type,
                title=resource.title,
                content_url=resource.content_url,
                content_text=resource.content_text,
                is_completed=topic_completed,
                is_locked=resource_locked,
                quiz_info=quiz_info
            ))
        
        topic_responses.append(AgentTopicResponse(
            id=str(topic.id),
            title=topic.title,
            order_sequence=topic.order_sequence,
            is_completed=topic_completed,
            is_locked=topic_locked,
            resources=resource_responses
        ))
    
    return AgentCourseDetailResponse(
        id=str(course.id),
        title=course.title,
        description=course.description,
        module_number=course.module_number,
        passing_score=course.passing_score,
        progress_percentage=progress_percentage,
        is_locked=is_locked,
        announcements=announcements,
        topics=topic_responses
    )


@router.post("/courses/{course_id}/enroll")
def enroll_in_course(
    course_id: uuid.UUID,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Enroll the agent in a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing = db.query(Enrollment).filter(
        Enrollment.agent_id == current_agent.id,
        Enrollment.course_id == course_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
    
    # Check progressive unlocking
    if course.module_number > 1:
        prev_course = db.query(Course).filter(
            Course.module_number == course.module_number - 1
        ).first()
        if prev_course:
            prev_enrollment = db.query(Enrollment).filter(
                Enrollment.agent_id == current_agent.id,
                Enrollment.course_id == prev_course.id
            ).first()
            if not prev_enrollment or prev_enrollment.status != EnrollmentStatus.COMPLETED:
                raise HTTPException(status_code=403, detail=f"Complete Module {course.module_number - 1} first")
    
    enrollment = Enrollment(
        agent_id=current_agent.id,
        course_id=course_id,
        status=EnrollmentStatus.IN_PROGRESS
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    return {"message": "Successfully enrolled in course", "enrollment_id": str(enrollment.id)}


# ============ TOPIC COMPLETION ============

@router.post("/topics/{topic_id}/complete")
def complete_topic(
    topic_id: uuid.UUID,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Mark a topic as completed"""
    topic = db.query(CourseTopic).filter(CourseTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Get enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.agent_id == current_agent.id,
        Enrollment.course_id == topic.course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    
    # Check if previous topics are completed
    if topic.order_sequence > 0:
        prev_topic = db.query(CourseTopic).filter(
            CourseTopic.course_id == topic.course_id,
            CourseTopic.order_sequence == topic.order_sequence - 1
        ).first()
        if prev_topic:
            prev_progress = db.query(TopicProgress).filter(
                TopicProgress.enrollment_id == enrollment.id,
                TopicProgress.topic_id == prev_topic.id
            ).first()
            if not prev_progress or not prev_progress.is_completed:
                raise HTTPException(status_code=403, detail="Complete previous topic first")
    
    # Mark topic as completed
    progress = db.query(TopicProgress).filter(
        TopicProgress.enrollment_id == enrollment.id,
        TopicProgress.topic_id == topic_id
    ).first()
    
    if not progress:
        progress = TopicProgress(
            enrollment_id=enrollment.id,
            topic_id=topic_id,
            is_completed=True,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(progress)
    else:
        progress.is_completed = True
        progress.completed_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {"message": "Topic marked as completed"}


# ============ RESOURCES ============

@router.get("/resources/{resource_id}")
def get_resource(
    resource_id: uuid.UUID,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get a resource's content"""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Check enrollment and access
    enrollment = db.query(Enrollment).filter(
        Enrollment.agent_id == current_agent.id,
        Enrollment.course_id == resource.course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    
    return {
        "id": str(resource.id),
        "resource_type": resource.resource_type,
        "title": resource.title,
        "content_url": resource.content_url,
        "content_text": resource.content_text
    }


# ============ QUIZ ENGINE ============

@router.post("/quizzes/{resource_id}/start")
def start_quiz(
    resource_id: uuid.UUID,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Start a quiz - returns questions without correct answers and starts timer"""
    resource = db.query(Resource).options(
        joinedload(Resource.quiz_questions)
    ).filter(Resource.id == resource_id).first()
    
    if not resource or resource.resource_type != ResourceType.QUIZ:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.agent_id == current_agent.id,
        Enrollment.course_id == resource.course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    
    # Check if topic is accessible (topic-level lock, not completion requirement)
    if resource.topic_id:
        topic = db.query(CourseTopic).filter(CourseTopic.id == resource.topic_id).first()
        if topic and topic.order_sequence > 0:
            prev_topic = db.query(CourseTopic).filter(
                CourseTopic.course_id == topic.course_id,
                CourseTopic.order_sequence == topic.order_sequence - 1
            ).first()
            if prev_topic:
                prev_progress = db.query(TopicProgress).filter(
                    TopicProgress.enrollment_id == enrollment.id,
                    TopicProgress.topic_id == prev_topic.id
                ).first()
                if not prev_progress or not prev_progress.is_completed:
                    raise HTTPException(status_code=403, detail="Complete the previous topic first")
    
    # Create quiz attempt
    attempt = QuizAttempt(
        enrollment_id=enrollment.id,
        resource_id=resource_id,
        started_at=datetime.now(timezone.utc)
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    # ── Anti-cheat: randomize question subset + shuffle options per attempt ──
    all_questions = list(resource.quiz_questions)
    random.shuffle(all_questions)

    # Draw up to the quiz's question_count (default: all)
    quiz_info = {
        "time_limit_minutes": resource.time_limit_minutes,
        "passing_score": resource.passing_score,
        "question_count": len(all_questions)
    }
    pool_size = len(all_questions)  # use all available; admin can set more in DB than shown
    selected = all_questions[:pool_size]

    # For each question: shuffle options and record a mapping so grading still works.
    # shuffle_map: { question_id: { "shuffled_options": [...], "correct_index": int } }
    shuffle_map = {}
    questions = []
    for idx, q in enumerate(selected):
        q_type = q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type)
        original_options = list(q.options or [])
        correct_answer = q.correct_answer or ""

        if q_type == "multiple_choice" and original_options:
            shuffled = original_options[:]
            random.shuffle(shuffled)
            # Store the index of the correct answer in the shuffled list
            correct_idx = str(shuffled.index(correct_answer)) if correct_answer in shuffled else None
            shuffle_map[str(q.id)] = {
                "shuffled_options": shuffled,
                "correct_index": correct_idx,
                "original_correct": correct_answer
            }
            display_options = shuffled
        else:
            # true_false / essay — no shuffle needed
            shuffle_map[str(q.id)] = {
                "shuffled_options": original_options,
                "correct_index": correct_answer,
                "original_correct": correct_answer
            }
            display_options = original_options

        questions.append({
            "id": str(q.id),
            "question_text": q.question_text or f"Question {idx + 1}",
            "question_type": q_type,
            "options": display_options,
            "points": q.points,
            "order_sequence": idx  # re-sequence after shuffle
        })

    # Persist shuffle map in attempt.answers field (prefixed key so submit can read it)
    attempt.answers = {"__shuffle_map__": shuffle_map}
    db.commit()

    return {
        "attempt_id": str(attempt.id),
        "time_limit_minutes": resource.time_limit_minutes,
        "passing_score": resource.passing_score,
        "questions": questions,
        "started_at": attempt.started_at,
        "expires_at": attempt.started_at + timedelta(minutes=resource.time_limit_minutes) if resource.time_limit_minutes else None
    }


@router.post("/quizzes/{resource_id}/submit", response_model=QuizResultResponse)
def submit_quiz(
    resource_id: uuid.UUID,
    submission: QuizSubmission,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get auto-graded results"""
    resource = db.query(Resource).options(
        joinedload(Resource.quiz_questions)
    ).filter(Resource.id == resource_id).first()
    
    if not resource or resource.resource_type != ResourceType.QUIZ:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Get enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.agent_id == current_agent.id,
        Enrollment.course_id == resource.course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    
    # Get the latest attempt for this resource
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.enrollment_id == enrollment.id,
        QuizAttempt.resource_id == resource_id,
        QuizAttempt.submitted_at.is_(None)
    ).order_by(QuizAttempt.started_at.desc()).first()
    
    if not attempt:
        raise HTTPException(status_code=400, detail="No active quiz attempt found")
    
    # Check time limit
    if resource.time_limit_minutes:
        elapsed = datetime.now(timezone.utc) - attempt.started_at
        if elapsed > timedelta(minutes=resource.time_limit_minutes + 2):  # 2 minute grace period
            attempt.submitted_at = datetime.now(timezone.utc)
            attempt.passed = False
            db.commit()
            raise HTTPException(status_code=403, detail="Quiz time limit exceeded")
    
    # Retrieve shuffle map stored during start_quiz
    stored = attempt.answers or {}
    shuffle_map = stored.get("__shuffle_map__", {})

    # Grade the quiz — only grade questions that were actually shown in this attempt
    correct_count = 0
    total_points = 0
    earned_points = 0
    results = []

    # Only grade questions present in the shuffle map (i.e. shown to this agent)
    shown_question_ids = set(shuffle_map.keys())
    questions_to_grade = [q for q in resource.quiz_questions if str(q.id) in shown_question_ids] \
        if shown_question_ids else list(resource.quiz_questions)

    for question in questions_to_grade:
        q_id_str = str(question.id)
        total_points += question.points

        user_answer = submission.answers.get(q_id_str)
        is_correct = False
        q_map = shuffle_map.get(q_id_str, {})

        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # user_answer is the index into the shuffled options list
            original_correct = q_map.get("original_correct") or question.correct_answer
            shuffled_options = q_map.get("shuffled_options", question.options or [])
            if user_answer is not None and original_correct:
                try:
                    chosen_option = shuffled_options[int(user_answer)]
                    is_correct = chosen_option == original_correct
                except (IndexError, ValueError, TypeError):
                    is_correct = False

        elif question.question_type == QuestionType.TRUE_FALSE:
            is_correct = str(user_answer).lower() == str(question.correct_answer).lower()

        elif question.question_type == QuestionType.ESSAY:
            is_correct = None
            if user_answer:
                db.add(EssayAnswer(
                    quiz_attempt_id=attempt.id,
                    question_id=question.id,
                    answer=user_answer
                ))

        if is_correct:
            correct_count += 1
            earned_points += question.points

        results.append({
            "id": q_id_str,
            "is_correct": is_correct,
            # Never reveal the correct answer text — only tell pass/fail per question
            "points": question.points
        })
    
    # Calculate score
    score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    passed = score_percentage >= (resource.passing_score or 80)
    
    # Update attempt — preserve shuffle_map alongside submitted answers
    attempt.score = score_percentage
    attempt.answers = {"__shuffle_map__": shuffle_map, **submission.answers}
    attempt.passed = passed
    attempt.submitted_at = datetime.now(timezone.utc)
    
    # If quiz passed: auto-complete the parent topic and check if course is fully done
    if passed and resource.topic_id:
        topic_prog = db.query(TopicProgress).filter(
            TopicProgress.enrollment_id == enrollment.id,
            TopicProgress.topic_id == resource.topic_id
        ).first()
        if not topic_prog:
            topic_prog = TopicProgress(
                enrollment_id=enrollment.id,
                topic_id=resource.topic_id,
                is_completed=True,
                completed_at=datetime.now(timezone.utc)
            )
            db.add(topic_prog)
        else:
            topic_prog.is_completed = True
            topic_prog.completed_at = datetime.now(timezone.utc)

        # Flush so the new TopicProgress row is visible to the count query below
        db.flush()

        # Check if all topics in the course are now completed → mark enrollment COMPLETED
        course = db.query(Course).filter(Course.id == resource.course_id).first()
        if course:
            total = db.query(CourseTopic).filter(CourseTopic.course_id == course.id).count()
            completed = db.query(TopicProgress).join(CourseTopic, TopicProgress.topic_id == CourseTopic.id).filter(
                CourseTopic.course_id == course.id,
                TopicProgress.enrollment_id == enrollment.id,
                TopicProgress.is_completed == True
            ).count()
            if total > 0 and completed >= total:
                enrollment.status = EnrollmentStatus.COMPLETED
                enrollment.overall_score = score_percentage
                enrollment.completed_at = datetime.now(timezone.utc)
    
    db.commit()
    
    message = "✅ Quiz Passed!" if passed else "❌ Quiz Failed. Review the materials and try again."
    
    return QuizResultResponse(
        passed=passed,
        score=score_percentage,
        results=results,
        message=message
    )


@router.get("/quizzes/{resource_id}/results")
def get_quiz_results(
    resource_id: uuid.UUID,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get quiz results for a specific resource"""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    enrollment = db.query(Enrollment).filter(
        Enrollment.agent_id == current_agent.id,
        Enrollment.course_id == resource.course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.enrollment_id == enrollment.id,
        QuizAttempt.resource_id == resource_id
    ).order_by(QuizAttempt.submitted_at.desc()).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="No quiz attempt found")
    
    return {
        "attempt_id": str(attempt.id),
        "score": attempt.score,
        "passed": attempt.passed,
        "submitted_at": attempt.submitted_at,
        "answers": attempt.answers
    }


# ============ PROGRESS ============

@router.get("/progress")
def get_progress(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get overall progress across all courses"""
    enrollments = db.query(Enrollment).options(
        joinedload(Enrollment.course)
    ).filter(Enrollment.agent_id == current_agent.id).all()
    
    response = []
    for enrollment in enrollments:
        course = enrollment.course
        total_topics = len(course.topics)
        completed_topics = db.query(TopicProgress).filter(
            TopicProgress.enrollment_id == enrollment.id,
            TopicProgress.is_completed == True
        ).count()
        
        progress_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        
        response.append({
            "course_id": str(course.id),
            "course_title": course.title,
            "module_number": course.module_number,
            "status": enrollment.status,
            "progress_percentage": progress_percentage,
            "overall_score": enrollment.overall_score,
            "enrolled_at": enrollment.enrolled_at,
            "completed_at": enrollment.completed_at
        })
    
    return response


# ============ CERTIFICATE ============

@router.get("/certificate")
def get_certificate(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Check if all modules are completed and return certificate data + downloadable HTML"""
    all_courses = db.query(Course).order_by(Course.module_number).all()
    total_modules = len(all_courses)

    if total_modules == 0:
        raise HTTPException(status_code=404, detail="No courses configured")

    completed_enrollments = []
    for course in all_courses:
        enr = db.query(Enrollment).filter(
            Enrollment.agent_id == current_agent.id,
            Enrollment.course_id == course.id,
            Enrollment.status == EnrollmentStatus.COMPLETED
        ).first()
        if enr:
            completed_enrollments.append(enr)

    if len(completed_enrollments) < total_modules:
        raise HTTPException(
            status_code=403,
            detail=f"Academy not complete. {len(completed_enrollments)}/{total_modules} modules completed."
        )

    # All modules done — gather certificate details
    agent_name = current_agent.user.full_name if current_agent.user else "Field Agent"
    agent_code = current_agent.agent_code
    avg_score = round(
        sum(e.overall_score for e in completed_enrollments if e.overall_score) / total_modules, 1
    )
    certified_at = max(e.completed_at for e in completed_enrollments if e.completed_at)
    cert_id = hashlib.sha256(f"{agent_code}-{certified_at.isoformat()}".encode()).hexdigest()[:12].upper()
    expiry = certified_at.replace(year=certified_at.year + 1)

    # Also flip agent status to ACTIVE if still trainee
    try:
        from app.models.agent import AgentStatus
        if current_agent.status.value in ("trainee", "TRAINEE", "pending"):
            current_agent.status = AgentStatus.ACTIVE
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update agent status to ACTIVE after certification: {e}")

    issued_str = certified_at.strftime("%d %B %Y")
    expiry_str = expiry.strftime("%d %B %Y")

    # Embed logo as base64 so it works in Blob-URL context
    logo_b64 = ""
    logo_candidates = [
        os.path.join(os.path.dirname(__file__), "../../static/logo.png"),
        "/app/app/static/logo.png",
        os.path.join(os.path.dirname(__file__), "../../../../apps/agent-portal/public/logo.png"),
    ]
    for path in logo_candidates:
        try:
            with open(os.path.abspath(path), "rb") as f:
                logo_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()
            break
        except Exception:
            continue

    logo_html = (
        f'<img src="{logo_b64}" alt="ZimAgriTrust" style="height:64px;width:auto;"/>'
        if logo_b64 else
        '<div class="logo-icon-fallback"><i>ZAT</i></div>'
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>ZimAgritrust Field Agent Certificate — {agent_name}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap');
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{background:#0a1628;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:'Inter',sans-serif;padding:24px;}}
  .cert{{background:#fff;width:900px;max-width:100%;border-radius:4px;overflow:hidden;box-shadow:0 32px 80px rgba(0,0,0,.5);position:relative;}}
  .cert-border{{border:12px solid transparent;background:linear-gradient(#fff,#fff) padding-box,linear-gradient(135deg,#10b981,#059669,#047857,#065f46) border-box;border-radius:4px;padding:56px 64px;}}
  .header{{text-align:center;margin-bottom:40px;}}
  .logo-row{{display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:20px;}}
  .logo-icon-fallback{{width:52px;height:52px;background:linear-gradient(135deg,#10b981,#059669);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;color:#fff;}}
  .logo-text{{text-align:left;}}
  .logo-name{{font-size:22px;font-weight:700;color:#065f46;letter-spacing:-.3px;}}
  .logo-sub{{font-size:11px;color:#6b7280;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;}}
  .divider-gold{{height:2px;background:linear-gradient(90deg,transparent,#10b981,transparent);margin:20px 0;}}
  .cert-title{{font-family:'Playfair Display',serif;font-size:13px;font-weight:400;letter-spacing:4px;text-transform:uppercase;color:#6b7280;margin-bottom:8px;}}
  .cert-headline{{font-family:'Playfair Display',serif;font-size:44px;font-weight:900;color:#0a1628;line-height:1.1;}}
  .cert-headline span{{color:#10b981;}}
  .body{{text-align:center;padding:0 40px;}}
  .certify-text{{font-size:14px;color:#6b7280;margin:28px 0 12px;letter-spacing:.3px;}}
  .agent-name{{font-family:'Playfair Display',serif;font-size:42px;font-weight:700;color:#0a1628;margin:8px 0;border-bottom:2px solid #10b981;display:inline-block;padding-bottom:6px;}}
  .agent-code{{font-size:13px;color:#6b7280;letter-spacing:2px;text-transform:uppercase;margin-top:8px;}}
  .description{{font-size:14px;color:#374151;line-height:1.7;margin:28px auto;max-width:560px;}}
  .modules-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:28px 0;}}
  .module-chip{{background:#f0fdf4;border:1px solid #a7f3d0;border-radius:8px;padding:10px 14px;text-align:left;}}
  .module-chip .num{{font-size:10px;font-weight:700;color:#10b981;text-transform:uppercase;letter-spacing:1px;margin-bottom:2px;}}
  .module-chip .title{{font-size:12px;font-weight:600;color:#065f46;}}
  .stats-row{{display:flex;justify-content:center;gap:48px;margin:32px 0;}}
  .stat{{text-align:center;}}
  .stat-val{{font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:#10b981;}}
  .stat-label{{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-top:4px;}}
  .footer{{display:flex;justify-content:space-between;align-items:flex-end;margin-top:40px;padding-top:24px;border-top:1px solid #e5e7eb;}}
  .sig-block{{text-align:center;}}
  .sig-line{{width:160px;height:1px;background:#374151;margin:0 auto 6px;}}
  .sig-name{{font-size:13px;font-weight:600;color:#374151;}}
  .sig-role{{font-size:11px;color:#9ca3af;}}
  .cert-meta{{text-align:right;}}
  .cert-id{{font-size:10px;font-family:monospace;background:#f3f4f6;padding:6px 12px;border-radius:6px;color:#374151;display:block;margin-bottom:6px;}}
  .cert-dates{{font-size:11px;color:#9ca3af;line-height:1.8;}}
  .watermark{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg);font-family:'Playfair Display',serif;font-size:80px;font-weight:900;color:rgba(16,185,129,.04);pointer-events:none;white-space:nowrap;z-index:0;}}
  .print-btn{{display:block;text-align:center;margin-top:20px;}}
  .print-btn button{{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;padding:12px 32px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;letter-spacing:.3px;}}
  @media print{{body{{background:#fff;padding:0;}}.print-btn{{display:none;}}.cert{{box-shadow:none;}}}}
</style>
</head>
<body>
<div>
  <div class="cert">
    <div class="cert-border">
      <div class="watermark">ZimAgritrust</div>

      <div class="header">
        <div class="logo-row">
          {logo_html}
        </div>
        <div class="divider-gold"></div>
        <div class="cert-title">This is to certify that</div>
        <div class="cert-headline">Field Agent<br/><span>Certification</span></div>
      </div>

      <div class="body">
        <div class="certify-text">has been awarded to</div>
        <div class="agent-name">{agent_name}</div>
        <div class="agent-code">Agent Code: {agent_code}</div>

        <p class="description">
          Having successfully completed all six modules of the <strong>ZimAgritrust Agent Academy</strong>
          and demonstrated mastery of platform operations, crop verification, escrow & payment systems,
          dispute resolution, trust & reputation management, and marketplace ethics.
        </p>

        <div class="modules-grid">
          <div class="module-chip"><div class="num">Module 1</div><div class="title">Platform Operations</div></div>
          <div class="module-chip"><div class="num">Module 2</div><div class="title">Escrow &amp; Payment</div></div>
          <div class="module-chip"><div class="num">Module 3</div><div class="title">Crop Verification &amp; Quality</div></div>
          <div class="module-chip"><div class="num">Module 4</div><div class="title">Dispute Resolution</div></div>
          <div class="module-chip"><div class="num">Module 5</div><div class="title">Trust &amp; Reputation</div></div>
          <div class="module-chip"><div class="num">Module 6</div><div class="title">Ethics &amp; Integrity</div></div>
        </div>

        <div class="stats-row">
          <div class="stat"><div class="stat-val">{avg_score}%</div><div class="stat-label">Average Score</div></div>
          <div class="stat"><div class="stat-val">6/6</div><div class="stat-label">Modules Passed</div></div>
          <div class="stat"><div class="stat-val">80%</div><div class="stat-label">Pass Threshold</div></div>
        </div>

        <div class="footer">
          <div class="sig-block">
            <div class="sig-line"></div>
            <div class="sig-name">ZimAgritrust Academy</div>
            <div class="sig-role">Certification Authority</div>
          </div>
          <div class="cert-meta">
            <span class="cert-id">CERT-ID: ZAT-{cert_id}</span>
            <div class="cert-dates">
              Issued: <strong>{issued_str}</strong><br/>
              Valid Until: <strong>{expiry_str}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="print-btn">
    <button onclick="window.print()">🖨️ &nbsp;Print / Save as PDF</button>
  </div>
</div>
</body>
</html>"""

    return HTMLResponse(
        content=html,
        headers={
            "Content-Disposition": f'inline; filename="ZimAgritrust_Certificate_{agent_code}.html"',
            "Cache-Control": "no-store"
        }
    )


# ============ ANNOUNCEMENTS ============

@router.get("/announcements", response_model=List[AnnouncementResponse])
def get_announcements(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get announcements for all enrolled courses"""
    # Get all enrolled course IDs
    enrollments = db.query(Enrollment).filter(
        Enrollment.agent_id == current_agent.id
    ).all()
    
    course_ids = [e.course_id for e in enrollments]
    
    if not course_ids:
        return []
    
    announcements = db.query(Announcement).filter(
        Announcement.course_id.in_(course_ids)
    ).order_by(Announcement.created_at.desc()).limit(20).all()
    
    return announcements
