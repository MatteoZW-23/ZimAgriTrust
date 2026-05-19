import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.agent import Agent
from app.models.classroom import (
    Course, CourseTopic, Resource, QuizQuestion, Enrollment,
    TopicProgress, QuizAttempt, EssayAnswer, Announcement,
    ResourceType, QuestionType, EnrollmentStatus
)
from app.schemas.classroom import (
    CourseCreate, CourseUpdate, CourseResponse, CourseDetailResponse,
    ResourceCreate, ResourceResponse,
    QuizQuestionCreate,
    AnnouncementCreate, AnnouncementResponse,
    StudentProgressResponse, EssayGrade, EssayAnswerResponse
)

router = APIRouter()


# ============ COURSE MANAGEMENT ============

@router.post("/courses", response_model=CourseResponse)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Create a new course"""
    new_course = Course(**course.model_dump())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


@router.get("/courses", response_model=List[CourseResponse])
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """List all courses with enrollment and resource counts"""
    courses = db.query(Course).options(
        joinedload(Course.enrollments),
        joinedload(Course.topics).joinedload(CourseTopic.resources)
    ).all()
    
    response = []
    for course in courses:
        students_enrolled = len([e for e in course.enrollments if e.status != EnrollmentStatus.NOT_ENROLLED])
        resources_count = sum(len(topic.resources) for topic in course.topics)
        quiz_count = sum(
            len([r for r in topic.resources if r.resource_type == ResourceType.QUIZ])
            for topic in course.topics
        )
        
        course_dict = {
            "id": str(course.id),
            "title": course.title,
            "description": course.description,
            "module_number": course.module_number,
            "passing_score": course.passing_score,
            "estimated_hours": course.estimated_hours,
            "is_active": course.is_active,
            "created_at": course.created_at,
            "updated_at": course.updated_at,
            "students_enrolled": students_enrolled,
            "resources_count": resources_count,
            "quiz_count": quiz_count
        }
        response.append(CourseResponse(**course_dict))
    
    return response


@router.get("/courses/{course_id}", response_model=CourseDetailResponse)
def get_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Get detailed course information with topics"""
    course = db.query(Course).options(
        joinedload(Course.topics).joinedload(CourseTopic.resources)
    ).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    students_enrolled = len([e for e in course.enrollments if e.status != EnrollmentStatus.NOT_ENROLLED])
    resources_count = sum(len(topic.resources) for topic in course.topics)
    quiz_count = sum(
        len([r for r in topic.resources if r.resource_type == ResourceType.QUIZ])
        for topic in course.topics
    )
    
    return CourseDetailResponse(
        id=str(course.id),
        title=course.title,
        description=course.description,
        module_number=course.module_number,
        passing_score=course.passing_score,
        estimated_hours=course.estimated_hours,
        is_active=course.is_active,
        created_at=course.created_at,
        updated_at=course.updated_at,
        students_enrolled=students_enrolled,
        resources_count=resources_count,
        quiz_count=quiz_count,
        topics=course.topics
    )


@router.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: uuid.UUID,
    course_update: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Update a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    update_data = course_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Delete a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}


# ============ RESOURCE MANAGEMENT ============

@router.post("/courses/{course_id}/resources", response_model=ResourceResponse)
def add_resource(
    course_id: uuid.UUID,
    resource: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Add a resource to a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_resource = Resource(**resource.model_dump())
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    return new_resource


@router.post("/courses/{course_id}/resources/upload")
async def upload_resource_file(
    course_id: uuid.UUID,
    topic_id: Optional[uuid.UUID] = None,
    resource_type: ResourceType = ResourceType.DOCUMENT,
    title: str = "",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Upload a file as a resource"""
    import os
    import shutil
    from pathlib import Path
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Create upload directory if it doesn't exist
    upload_dir = Path("uploads/classroom")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_extension = Path(file.filename).suffix
    file_path = upload_dir / f"{uuid.uuid4()}{file_extension}"
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create resource record
    new_resource = Resource(
        course_id=course_id,
        topic_id=topic_id,
        resource_type=resource_type,
        title=title or file.filename,
        content_url=str(file_path),
        order_sequence=0
    )
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    
    return new_resource


# ============ ANNOUNCEMENTS ============

@router.post("/courses/{course_id}/announcements", response_model=AnnouncementResponse)
def create_announcement(
    course_id: uuid.UUID,
    announcement: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Create an announcement for a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_announcement = Announcement(
        course_id=course_id,
        admin_id=current_user.id,
        message=announcement.message
    )
    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)
    
    return AnnouncementResponse(
        id=str(new_announcement.id),
        course_id=str(new_announcement.course_id),
        admin_id=str(new_announcement.admin_id),
        admin_name=current_user.full_name,
        message=new_announcement.message,
        created_at=new_announcement.created_at
    )


# ============ STUDENT MANAGEMENT ============

@router.get("/courses/{course_id}/students", response_model=List[StudentProgressResponse])
def get_course_students(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Get all students enrolled in a course with their progress"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    enrollments = db.query(Enrollment).options(
        joinedload(Enrollment.agent).joinedload(Agent.user)
    ).filter(Enrollment.course_id == course_id).all()
    
    response = []
    for enrollment in enrollments:
        # Calculate progress
        total_topics = len(course.topics)
        completed_topics = db.query(TopicProgress).filter(
            TopicProgress.enrollment_id == enrollment.id,
            TopicProgress.is_completed == True
        ).count()
        
        progress_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        
        # Get latest quiz score
        latest_attempt = db.query(QuizAttempt).filter(
            QuizAttempt.enrollment_id == enrollment.id
        ).order_by(QuizAttempt.submitted_at.desc()).first()
        
        response.append(StudentProgressResponse(
            agent_id=str(enrollment.agent_id),
            agent_name=enrollment.agent.user.full_name if enrollment.agent and enrollment.agent.user else "Unknown",
            course_id=str(course_id),
            course_title=course.title,
            progress_percentage=progress_percentage,
            quiz_score=latest_attempt.score if latest_attempt else None,
            status=enrollment.status,
            enrolled_at=enrollment.enrolled_at,
            completed_at=enrollment.completed_at
        ))
    
    return response


@router.post("/courses/{course_id}/invite")
def invite_students(
    course_id: uuid.UUID,
    agent_ids: List[uuid.UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Invite multiple agents to enroll in a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    enrolled_count = 0
    for agent_id in agent_ids:
        # Check if agent exists
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            continue
        
        # Check if already enrolled
        existing = db.query(Enrollment).filter(
            Enrollment.agent_id == agent_id,
            Enrollment.course_id == course_id
        ).first()
        
        if not existing:
            enrollment = Enrollment(
                agent_id=agent_id,
                course_id=course_id,
                status=EnrollmentStatus.ENROLLED
            )
            db.add(enrollment)
            enrolled_count += 1
    
    db.commit()
    return {"message": f"Invited {enrolled_count} agents to the course"}


@router.get("/students/{agent_id}/progress")
def get_student_progress(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Get detailed progress for a specific student across all courses"""
    enrollments = db.query(Enrollment).options(
        joinedload(Enrollment.course),
        joinedload(Enrollment.topic_progress),
        joinedload(Enrollment.quiz_attempts)
    ).filter(Enrollment.agent_id == agent_id).all()
    
    if not enrollments:
        raise HTTPException(status_code=404, detail="No enrollments found for this agent")
    
    response = []
    for enrollment in enrollments:
        course = enrollment.course
        total_topics = len(course.topics)
        completed_topics = len([tp for tp in enrollment.topic_progress if tp.is_completed])
        progress_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        
        response.append({
            "course_id": str(course.id),
            "course_title": course.title,
            "module_number": course.module_number,
            "status": enrollment.status,
            "progress_percentage": progress_percentage,
            "overall_score": enrollment.overall_score,
            "enrolled_at": enrollment.enrolled_at,
            "completed_at": enrollment.completed_at,
            "topic_progress": [
                {
                    "topic_id": str(tp.topic_id),
                    "is_completed": tp.is_completed,
                    "completed_at": tp.completed_at
                }
                for tp in enrollment.topic_progress
            ],
            "quiz_attempts": [
                {
                    "resource_id": str(qa.resource_id),
                    "score": qa.score,
                    "passed": qa.passed,
                    "submitted_at": qa.submitted_at
                }
                for qa in enrollment.quiz_attempts
            ]
        })
    
    return response


# ============ QUIZ QUESTION MANAGEMENT ============

@router.post("/resources/{resource_id}/questions")
def add_quiz_question(
    resource_id: uuid.UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Add a question to a quiz resource"""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource or resource.resource_type != ResourceType.QUIZ:
        raise HTTPException(status_code=404, detail="Quiz resource not found")
    
    q_type_str = payload.get("question_type", "multiple_choice")
    try:
        q_type = QuestionType(q_type_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid question_type: {q_type_str}")
    
    existing_count = db.query(QuizQuestion).filter(QuizQuestion.resource_id == resource_id).count()
    
    question = QuizQuestion(
        resource_id=resource_id,
        question_text=payload.get("question_text", ""),
        question_type=q_type,
        options=payload.get("options"),
        correct_answer=payload.get("correct_answer"),
        points=payload.get("points", 1),
        order_sequence=payload.get("order_sequence", existing_count)
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return {
        "id": str(question.id),
        "question_text": question.question_text,
        "question_type": question.question_type.value,
        "options": question.options,
        "correct_answer": question.correct_answer,
        "points": question.points,
        "order_sequence": question.order_sequence
    }


@router.patch("/questions/{question_id}")
def update_quiz_question(
    question_id: uuid.UUID,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Update a quiz question (including question_text)"""
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if "question_text" in payload:
        question.question_text = payload["question_text"]
    if "options" in payload:
        question.options = payload["options"]
    if "correct_answer" in payload:
        question.correct_answer = payload["correct_answer"]
    if "points" in payload:
        question.points = payload["points"]
    if "question_type" in payload:
        try:
            question.question_type = QuestionType(payload["question_type"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question_type")
    
    db.commit()
    db.refresh(question)
    return {
        "id": str(question.id),
        "question_text": question.question_text,
        "question_type": question.question_type.value,
        "options": question.options,
        "correct_answer": question.correct_answer,
        "points": question.points
    }


@router.get("/resources/{resource_id}/questions")
def list_quiz_questions(
    resource_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """List all questions for a quiz resource"""
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.resource_id == resource_id
    ).order_by(QuizQuestion.order_sequence).all()
    return [
        {
            "id": str(q.id),
            "question_text": q.question_text,
            "question_type": q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
            "options": q.options,
            "correct_answer": q.correct_answer,
            "points": q.points,
            "order_sequence": q.order_sequence
        }
        for q in questions
    ]


@router.delete("/questions/{question_id}")
def delete_quiz_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Delete a quiz question"""
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(question)
    db.commit()
    return {"message": "Question deleted"}


# ============ ESSAY GRADING ============

@router.post("/essays/{essay_id}/grade", response_model=EssayAnswerResponse)
def grade_essay(
    essay_id: uuid.UUID,
    grade_data: EssayGrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """Grade an essay answer"""
    essay = db.query(EssayAnswer).filter(EssayAnswer.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    
    essay.grade = grade_data.grade
    essay.feedback = grade_data.feedback
    essay.graded_by = current_user.id
    essay.graded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(essay)
    
    return essay
