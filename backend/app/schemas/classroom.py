from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EnrollmentStatus(str, Enum):
    NOT_ENROLLED = "not_enrolled"
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResourceType(str, Enum):
    DOCUMENT = "document"
    VIDEO = "video"
    IMAGE = "image"
    LINK = "link"
    QUIZ = "quiz"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    ESSAY = "essay"


# ============ COURSE SCHEMAS ============

class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    module_number: int = Field(..., gt=0)
    passing_score: float = Field(default=80.0, ge=0, le=100)
    estimated_hours: float = Field(default=2.0, gt=0)
    is_active: bool = True


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    module_number: Optional[int] = Field(None, gt=0)
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    estimated_hours: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    students_enrolled: int = 0
    resources_count: int = 0
    quiz_count: int = 0

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    topics: List["TopicResponse"] = []


# ============ TOPIC SCHEMAS ============

class TopicBase(BaseModel):
    topic_number: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    order_sequence: int = Field(..., ge=0)


class TopicCreate(BaseModel):
    course_id: str
    topic_number: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    order_sequence: int = Field(..., ge=0)


class TopicUpdate(BaseModel):
    topic_number: Optional[int] = Field(None, gt=0)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    order_sequence: Optional[int] = Field(None, ge=0)


class TopicResponse(TopicBase):
    id: str
    course_id: str
    resources: List["ResourceResponse"] = []

    class Config:
        from_attributes = True


# ============ RESOURCE SCHEMAS ============

class ResourceBase(BaseModel):
    resource_type: ResourceType
    title: str = Field(..., min_length=1, max_length=200)
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    order_sequence: int = Field(..., ge=0)
    time_limit_minutes: Optional[int] = Field(None, gt=0)
    passing_score: Optional[float] = Field(None, ge=0, le=100)


class ResourceCreate(BaseModel):
    course_id: str
    topic_id: str
    resource_type: ResourceType
    title: str = Field(..., min_length=1)
    content: Optional[str] = None
    file_path: Optional[str] = None
    video_url: Optional[str] = None
    external_link: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, ge=0)
    passing_score: Optional[float] = Field(None, ge=0, le=100)


class ResourceResponse(ResourceBase):
    id: str
    course_id: str
    topic_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    quiz_questions: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


# ============ QUIZ QUESTION SCHEMAS ============

class QuizQuestionBase(BaseModel):
    question_text: str = Field(..., min_length=1)
    question_type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    points: int = Field(default=1, gt=0)
    order_sequence: int = Field(..., ge=0)


class QuizQuestionCreate(BaseModel):
    resource_id: str
    question_text: str = Field(..., min_length=1)
    question_type: QuestionType
    options: Optional[List[str]] = None


# ============ ENROLLMENT SCHEMAS ============

class EnrollmentResponse(BaseModel):
    id: str
    agent_id: str
    course_id: str
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: Optional[datetime]
    overall_score: Optional[float]
    course_title: Optional[str] = None
    agent_name: Optional[str] = None
    progress_percentage: float = 0.0

    class Config:
        from_attributes = True


class QuizSubmission(BaseModel):
    answers: Dict[str, Any]


class QuizResultResponse(BaseModel):
    passed: bool
    score: float
    results: List[Dict[str, Any]]
    message: str


# ============ ESSAY ANSWER SCHEMAS ============

class EssayGrade(BaseModel):
    grade: float = Field(..., ge=0)
    feedback: Optional[str] = None


class EssayAnswerResponse(BaseModel):
    id: str
    quiz_attempt_id: str
    question_id: str
    answer: str
    grade: Optional[float]
    feedback: Optional[str]
    graded_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ ANNOUNCEMENT SCHEMAS ============

class AnnouncementCreate(BaseModel):
    course_id: str
    message: str = Field(..., min_length=1)


class AnnouncementResponse(BaseModel):
    id: str
    course_id: str
    admin_id: str
    admin_name: Optional[str] = None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ STUDENT PROGRESS SCHEMAS ============

class StudentProgressResponse(BaseModel):
    agent_id: str
    agent_name: str
    course_id: str
    course_title: str
    progress_percentage: float
    quiz_score: Optional[float]
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: Optional[datetime]


# ============ AGENT COURSE LIST SCHEMAS ============

class AgentCourseResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    module_number: int
    progress_percentage: float
    grade: Optional[float]
    is_locked: bool
    lock_message: Optional[str] = None

    class Config:
        from_attributes = True


class AgentCourseDetailResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    module_number: int
    passing_score: float
    progress_percentage: float
    is_locked: bool
    announcements: List[AnnouncementResponse] = []
    topics: List["AgentTopicResponse"] = []

    class Config:
        from_attributes = True


class AgentTopicResponse(BaseModel):
    id: str
    title: str
    order_sequence: int
    is_completed: bool
    is_locked: bool
    resources: List["AgentResourceResponse"] = []

    class Config:
        from_attributes = True


class AgentResourceResponse(BaseModel):
    id: str
    resource_type: ResourceType
    title: str
    content_url: Optional[str]
    content_text: Optional[str]
    is_completed: bool
    is_locked: bool
    quiz_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Update forward references
CourseDetailResponse.model_rebuild()
TopicResponse.model_rebuild()
ResourceResponse.model_rebuild()
AgentCourseDetailResponse.model_rebuild()
AgentTopicResponse.model_rebuild()
