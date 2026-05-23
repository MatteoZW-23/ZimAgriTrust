/**
 * ZimAgritrust – Agent Training Academy (Google Classroom Style)
 * Agent Portal Screens
 */

import React, { useState, useEffect } from 'react';
import {
  getAcademyCourses,
  getAcademyCourseDetail,
  enrollInAcademyCourse,
  completeAcademyTopic,
  startAcademyQuiz,
  submitAcademyQuiz,
  getAcademyProgress,
  submitFinalExam,
  getCertificate,
} from '../api.ts';
import CourseList from './academy/CourseList';
import CourseDetail from './academy/CourseDetail';
import ReadingMaterial from './academy/ReadingMaterial';
import QuizTaking from './academy/QuizTaking';
import QuizResults from './academy/QuizResults';

const Academy = ({ token, agent, onCertified }) => {
  // Screen states
  const [currentScreen, setCurrentScreen] = useState('course-list');
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedResource, setSelectedResource] = useState(null);
  const [quizAttempt, setQuizAttempt] = useState(null);
  
  // Data states
  const [courses, setCourses] = useState([]);
  const [courseDetail, setCourseDetail] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [quizResults, setQuizResults] = useState(null);
  const [progress, setProgress] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  
  // Quiz states
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [quizTimer, setQuizTimer] = useState(null);
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Fetch courses
  const fetchCourses = async () => {
    setLoading(true);
    try {
      setCourses(await getAcademyCourses());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch course detail
  const fetchCourseDetail = async (courseId) => {
    setLoading(true);
    try {
      const data = await getAcademyCourseDetail(courseId);
      setCourseDetail(data);
      setAnnouncements(data.announcements || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Enroll in course
  const handleEnroll = async (courseId) => {
    setLoading(true);
    try {
      await enrollInAcademyCourse(courseId);
      setSuccess('Successfully enrolled!');
      fetchCourses();
      fetchCourseDetail(courseId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Complete topic
  const handleCompleteTopic = async (topicId) => {
    setLoading(true);
    try {
      await completeAcademyTopic(topicId);
      setSuccess('Topic marked as complete!');
      if (courseDetail) {
        fetchCourseDetail(courseDetail.id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Start quiz
  const handleStartQuiz = async (resourceId) => {
    setLoading(true);
    try {
      const data = await startAcademyQuiz(resourceId);
      setQuizData(data);
      setQuizAttempt({ id: data.attempt_id, resourceId });
      setAnswers({});
      setCurrentQuestionIndex(0);
      
      // Start timer
      if (data.time_limit_minutes) {
        setTimeRemaining(data.time_limit_minutes * 60);
        const timer = setInterval(() => {
          setTimeRemaining(prev => {
            if (prev <= 1) {
              clearInterval(timer);
              handleSubmitQuiz();
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
        setQuizTimer(timer);
      }
      
      setCurrentScreen('quiz-taking');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Submit quiz
  const handleSubmitQuiz = async () => {
    if (quizTimer) {
      clearInterval(quizTimer);
      setQuizTimer(null);
    }
    
    setLoading(true);
    try {
      const data = await submitAcademyQuiz(quizAttempt.resourceId, answers);
      setQuizResults(data);
      setCurrentScreen('quiz-results');
      // After any passed quiz refresh progress and check if all modules are now complete
      if (data?.passed && onCertified) {
        try {
          const freshProgress = await getAcademyProgress();
          const allDone = freshProgress.length > 0 &&
            freshProgress.every(p => p.status === 'COMPLETED');
          if (allDone) onCertified();
          else setProgress(freshProgress);
        } catch (_) {}
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch progress
  const fetchProgress = async () => {
    try {
      setProgress(await getAcademyProgress());
    } catch (err) {
      setError(err.message);
    }
  };
  
  
  useEffect(() => {
    fetchCourses();
    fetchProgress();
  }, []);
  
  useEffect(() => {
    return () => {
      if (quizTimer) clearInterval(quizTimer);
    };
  }, [quizTimer]);
  
  // Handle course selection — auto-enroll on first open (like Google Classroom)
  const handleCourseSelect = async (course, errorMsg) => {
    if (errorMsg) {
      setError(errorMsg);
      return;
    }
    setSelectedCourse(course);
    setCurrentScreen('course-detail');
    setLoading(true);
    try {
      // Silently enroll if not already enrolled; ignore "Already enrolled" 400
      await enrollInAcademyCourse(course.id);
    } catch (err) {
      if (!err.message?.toLowerCase().includes('already enrolled')) {
        // Real error (e.g. locked module) — surface it and stay on course list
        setError(err.message);
        setCurrentScreen('course-list');
        setSelectedCourse(null);
        setLoading(false);
        return;
      }
      // Already enrolled — fine, continue to load detail
    }
    try {
      const data = await getAcademyCourseDetail(course.id);
      setCourseDetail(data);
      setAnnouncements(data.announcements || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle back to courses
  const handleBackToCourses = () => {
    setCurrentScreen('course-list');
    setSelectedCourse(null);
    setCourseDetail(null);
  };

  // Handle read resource
  const handleReadResource = (resource) => {
    setSelectedResource(resource);
    setCurrentScreen('reading-material');
  };

  // Handle back to course detail
  const handleBackToCourseDetail = () => {
    setCurrentScreen('course-detail');
    setSelectedResource(null);
  };

  // Handle answer change
  const handleAnswerChange = (questionId, value) => {
    if (questionId === 'navigate') {
      setCurrentQuestionIndex(value);
    } else {
      setAnswers({ ...answers, [questionId]: value });
    }
  };

  // Handle navigation
  const handlePrevious = () => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1));
  const handleNext = () => setCurrentQuestionIndex(Math.min(quizData.questions.length - 1, currentQuestionIndex + 1));

  // Handle back from quiz results
  const handleBackFromResults = () => {
    setCurrentScreen('course-detail');
    setQuizResults(null);
    if (courseDetail) fetchCourseDetail(courseDetail.id);
  };

  // Render current screen
  const renderScreen = () => {
    switch (currentScreen) {
      case 'course-list':
        return <CourseList courses={courses} loading={loading} onCourseSelect={handleCourseSelect} />;
      case 'course-detail':
        return (
          <CourseDetail
            courseDetail={courseDetail}
            announcements={announcements}
            onBack={handleBackToCourses}
            onCompleteTopic={handleCompleteTopic}
            onStartQuiz={handleStartQuiz}
            onReadResource={handleReadResource}
          />
        );
      case 'reading-material':
        return <ReadingMaterial selectedResource={selectedResource} onBack={handleBackToCourseDetail} />;
      case 'quiz-taking':
        return (
          <QuizTaking
            quizData={quizData}
            currentQuestionIndex={currentQuestionIndex}
            answers={answers}
            timeRemaining={timeRemaining}
            onAnswerChange={handleAnswerChange}
            onPrevious={handlePrevious}
            onNext={handleNext}
            onSubmit={handleSubmitQuiz}
            loading={loading}
          />
        );
      case 'quiz-results':
        return <QuizResults quizResults={quizResults} onBack={handleBackFromResults} />;
      default:
        return <CourseList courses={courses} loading={loading} onCourseSelect={handleCourseSelect} />;
    }
  };

  const overallPct = progress.length > 0
    ? Math.round(progress.reduce((sum, p) => sum + (p.progress_percentage || 0), 0) / progress.length)
    : 0;

  return (
    <div className="page-content">
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 4 }}>
          <div>
            <h1 className="page-title"><i className="fas fa-graduation-cap" style={{ color: 'var(--primary)', marginRight: 10 }}></i>Academy</h1>
            <p className="page-sub">Agent Certification Programme — complete all modules to earn your Field Agent badge.</p>
          </div>
          <span className="badge badge-green" style={{ fontSize: 13, padding: '6px 14px' }}>
            <i className="fas fa-user-graduate"></i>
            {agent?.full_name || agent?.user?.full_name || 'Agent'}
          </span>
        </div>
      </div>

      {/* Hero progress banner — only on course list */}
      {currentScreen === 'course-list' && (
        <div className="training-hero" style={{ marginLeft: 0, marginRight: 0 }}>
          <div className="training-hero-content">
            <span className="eyebrow">Agent Certification Programme</span>
            <h2>Master ZimAgritrust Platform Operations</h2>
            <p>Complete all modules, pass the assessments, and earn your Field Agent certification.</p>
          </div>
          <div className="training-progress-card">
            <div
              className="academy-progress-ring"
              style={{ '--progress': `${overallPct * 3.6}deg` }}
            >
              <span>{overallPct}%</span>
            </div>
            <strong>{overallPct}%</strong>
            <span>Overall Progress</span>
          </div>
        </div>
      )}

      {/* Content */}
      {renderScreen()}

      {/* Notifications */}
      {error && (
        <div className="alert alert-error" style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1000, maxWidth: 360 }}>
          <i className="fas fa-exclamation-circle"></i>
          {error}
          <button onClick={() => setError(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}>
            <i className="fas fa-times"></i>
          </button>
        </div>
      )}

      {success && (
        <div className="alert alert-success" style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1000, maxWidth: 360 }}>
          <i className="fas fa-check-circle"></i>
          {success}
          <button onClick={() => setSuccess(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}>
            <i className="fas fa-times"></i>
          </button>
        </div>
      )}
    </div>
  );
};

export default Academy;
