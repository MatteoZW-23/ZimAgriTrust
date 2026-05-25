/**
 * ZimAgritrust – Agent Training Academy
 * Agent Portal Screens - Direct Backend Integration
 */

import React, { useState, useEffect } from 'react';
import {
  getAcademyProgress,
  getAcademyCourseDetail,
  completeAcademyTopic,
  submitAcademyQuiz,
  submitFinalExam,
  getCertificate,
  request,
} from '../api.ts';

interface Topic {
  id: string;
  title: string;
  abstract?: string;
  content?: string;
  is_completed: boolean;
}

interface Module {
  id: string;
  module_number: number;
  title: string;
  description: string;
  status: string;
  score?: number;
  is_locked: boolean;
  topics: Topic[];
}

interface ProgressData {
  agent_id: string;
  agent_name: string;
  certification_level: string;
  overall_progress: number;
  modules_completed: number;
  modules: Module[];
  certification_expires_at?: string;
  days_until_expiry?: number;
}

interface ModuleDetail {
  module_number: number;
  title: string;
  description: string;
  topics: Topic[];
  quiz_questions: { questions: any[] };
  topics_progress: Record<string, boolean>;
  quiz_passing_score: number;
}

interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
}

interface ExamResponse {
  questions: QuizQuestion[];
}

interface AcademyProps {
  token?: string;
  agent?: any;
  onCertified?: () => void;
}

const Academy: React.FC<AcademyProps> = ({ token, agent, onCertified }) => {
  // Screen states
  const [currentScreen, setCurrentScreen] = useState<string>('module-list');
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);

  // Data states
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [moduleDetail, setModuleDetail] = useState<ModuleDetail | null>(null);
  const [quizData, setQuizData] = useState<ExamResponse | null>(null);
  const [quizResults, setQuizResults] = useState<any | null>(null);
  const [finalExamQuestions, setFinalExamQuestions] = useState<ExamResponse | null>(null);

  // Quiz states
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [quizTimer, setQuizTimer] = useState<NodeJS.Timeout | null>(null);

  // UI states
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Fetch progress
  const fetchProgress = async () => {
    setLoading(true);
    try {
      const data = await getAcademyProgress();
      setProgress(data);

      // Check if certified
      if (data.certification_level === 'certified' && onCertified) {
        onCertified();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Fetch module detail
  const fetchModuleDetail = async (moduleNumber: number) => {
    setLoading(true);
    try {
      const data = await getAcademyCourseDetail(moduleNumber);
      setModuleDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Complete topic
  const handleCompleteTopic = async (topicId: string) => {
    setLoading(true);
    try {
      if (!selectedModule) return;
      await completeAcademyTopic(selectedModule.module_number, topicId);
      setSuccess('Topic marked as complete!');
      fetchModuleDetail(selectedModule.module_number);
      fetchProgress();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Submit module quiz
  const handleSubmitQuiz = async () => {
    if (quizTimer) {
      clearInterval(quizTimer);
      setQuizTimer(null);
    }

    setLoading(true);
    try {
      if (!selectedModule) return;
      const data = await submitAcademyQuiz(selectedModule.module_number, answers);
      setQuizResults(data);
      setCurrentScreen('quiz-results');

      if (data.passed) {
        fetchProgress();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Start final exam
  const handleStartFinalExam = async () => {
    setLoading(true);
    try {
      // Use the correct endpoint for final exam questions
      const response = await request('/academy/exam/final/questions');
      setFinalExamQuestions(response);
      setAnswers({});
      setTimeRemaining(60 * 60); // 60 minutes

      // Start timer
      const timer = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            handleSubmitFinalExam();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      setQuizTimer(timer);

      setCurrentScreen('final-exam');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Submit final exam
  const handleSubmitFinalExam = async () => {
    if (quizTimer) {
      clearInterval(quizTimer);
      setQuizTimer(null);
    }

    setLoading(true);
    try {
      const data = await submitFinalExam(answers);
      setQuizResults(data);
      setCurrentScreen('exam-results');

      if (data.passed) {
        fetchProgress();
        if (onCertified) {
          onCertified();
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchProgress();
  }, []);
  
  useEffect(() => {
    return () => {
      if (quizTimer) clearInterval(quizTimer);
    };
  }, [quizTimer]);
  
  // Handle module selection
  const handleModuleSelect = (module: Module) => {
    setSelectedModule(module);
    setCurrentScreen('module-detail');
    fetchModuleDetail(module.module_number);
  };

  // Handle back to modules
  const handleBackToModules = () => {
    setCurrentScreen('module-list');
    setSelectedModule(null);
    setModuleDetail(null);
  };

  // Handle topic selection
  const handleTopicSelect = (topic: Topic) => {
    setSelectedTopic(topic);
    setCurrentScreen('topic-content');
  };

  // Handle back to module detail
  const handleBackToModuleDetail = () => {
    setCurrentScreen('module-detail');
    setSelectedTopic(null);
  };

  // Handle answer change
  const handleAnswerChange = (questionId: string, value: any) => {
    setAnswers({ ...answers, [questionId]: value });
  };

  // Handle back from quiz results
  const handleBackFromResults = () => {
    setCurrentScreen('module-detail');
    setQuizResults(null);
    fetchProgress();
  };

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Render current screen
  const renderScreen = () => {
    if (!progress) return <div>Loading...</div>;

    switch (currentScreen) {
      case 'module-list':
        return (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
            {progress.modules?.map((module: Module, idx: number) => (
              <div
                key={module.module_number}
                onClick={() => !module.is_locked && handleModuleSelect(module)}
                style={{
                  background: 'var(--card-bg)',
                  border: '1px solid var(--border)',
                  borderRadius: 12,
                  padding: 20,
                  cursor: module.is_locked ? 'not-allowed' : 'pointer',
                  opacity: module.is_locked ? 0.6 : 1,
                  transition: 'all 0.2s'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--primary)' }}>Module {module.module_number}</span>
                  <span style={{
                    fontSize: 10,
                    padding: '4px 8px',
                    borderRadius: 10,
                    background: module.status === 'completed' ? '#10b981' : module.status === 'in_progress' ? '#f59e0b' : '#64748b',
                    color: '#fff'
                  }}>{module.status}</span>
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>{module.title}</h3>
                <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 12 }}>{module.description}</p>
                {module.score !== null && (
                  <div style={{ fontSize: 12, fontWeight: 600 }}>Score: {module.score}%</div>
                )}
                {module.is_locked && (
                  <div style={{ fontSize: 11, color: '#ef4444', marginTop: 8 }}>
                    <i className="fas fa-lock"></i> Complete previous module first
                  </div>
                )}
              </div>
            ))}

            {/* Final Exam Card */}
            {progress.modules_completed >= 10 && (
              <div
                onClick={handleStartFinalExam}
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: 12,
                  padding: 20,
                  cursor: 'pointer',
                  color: '#fff'
                }}
              >
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Final Certification Exam</h3>
                <p style={{ fontSize: 12, opacity: 0.9, marginBottom: 12 }}>200 questions • 60 minutes • 80% to pass</p>
                <div style={{ fontSize: 12, fontWeight: 600 }}>
                  <i className="fas fa-graduation-cap"></i> Take Exam
                </div>
              </div>
            )}
          </div>
        );

      case 'module-detail':
        return (
          <div>
            <button onClick={handleBackToModules} style={{ marginBottom: 20, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer' }}>
              <i className="fas fa-arrow-left"></i> Back to Modules
            </button>

            {moduleDetail && (
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
                <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Module {moduleDetail.module_number}: {moduleDetail.title}</h2>
                <p style={{ fontSize: 14, color: 'var(--text-dim)', marginBottom: 24 }}>{moduleDetail.description}</p>

                {/* Topics */}
                <div style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Topics</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {moduleDetail.topics?.map((topic: Topic, idx: number) => (
                      <div
                        key={topic.id}
                        onClick={() => handleTopicSelect(topic)}
                        style={{
                          background: 'var(--surface)',
                          border: '1px solid var(--border)',
                          borderRadius: 8,
                          padding: 16,
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 600, marginBottom: 4 }}>{topic.title}</div>
                          <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{topic.abstract}</div>
                        </div>
                        {topic.is_completed && (
                          <i className="fas fa-check-circle" style={{ color: '#10b981', fontSize: 20 }}></i>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Quiz */}
                {moduleDetail.quiz_questions && moduleDetail.quiz_questions.questions && (
                  <button
                    onClick={() => {
                      setQuizData(moduleDetail.quiz_questions);
                      setAnswers({});
                      setCurrentScreen('quiz-taking');
                    }}
                    style={{
                      padding: '12px 24px',
                      background: 'var(--primary)',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 8,
                      cursor: 'pointer',
                      fontWeight: 600
                    }}
                  >
                    <i className="fas fa-question-circle"></i> Take Quiz
                  </button>
                )}
              </div>
            )}
          </div>
        );
        
      case 'topic-content':
        return (
          <div>
            <button onClick={handleBackToModuleDetail} style={{ marginBottom: 20, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer' }}>
              <i className="fas fa-arrow-left"></i> Back to Module
            </button>
            
            {selectedTopic && (
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
                <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>{selectedTopic.title}</h2>
                <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text)' }}>{selectedTopic.content}</div>
                
                <button
                  onClick={() => handleCompleteTopic(selectedTopic.id)}
                  style={{
                    marginTop: 24,
                    padding: '12px 24px',
                    background: '#10b981',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    cursor: 'pointer',
                    fontWeight: 600
                  }}
                >
                  <i className="fas fa-check"></i> Mark as Complete
                </button>
              </div>
            )}
          </div>
        );
        
      case 'quiz-taking':
        return (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h2 style={{ fontSize: 24, fontWeight: 700 }}>Module Quiz</h2>
              {timeRemaining > 0 && (
                <div style={{ fontSize: 18, fontWeight: 700, color: timeRemaining < 300 ? '#ef4444' : '#10b981' }}>
                  <i className="fas fa-clock"></i> {formatTime(timeRemaining)}
                </div>
              )}
            </div>
            
            {quizData && quizData.questions && (
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
                {quizData.questions.map((q: QuizQuestion, idx: number) => (
                  <div key={q.id} style={{ marginBottom: 24, paddingBottom: 24, borderBottom: '1px solid var(--border)' }}>
                    <div style={{ fontWeight: 600, marginBottom: 12 }}>{idx + 1}. {q.question}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {q.options.map((opt: string, optIdx: number) => (
                        <label
                          key={optIdx}
                          style={{
                            padding: '12px',
                            background: answers[q.id] === optIdx ? 'var(--primary)' : 'var(--surface)',
                            border: '1px solid var(--border)',
                            borderRadius: 8,
                            cursor: 'pointer',
                            color: answers[q.id] === optIdx ? '#fff' : 'var(--text)'
                          }}
                        >
                          <input
                            type="radio"
                            name={`q-${q.id}`}
                            value={optIdx}
                            checked={answers[q.id] === optIdx}
                            onChange={() => handleAnswerChange(q.id, optIdx)}
                            style={{ marginRight: 8 }}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                
                <button
                  onClick={handleSubmitQuiz}
                  disabled={loading}
                  style={{
                    padding: '12px 24px',
                    background: 'var(--primary)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    cursor: 'pointer',
                    fontWeight: 600,
                    opacity: loading ? 0.6 : 1
                  }}
                >
                  {loading ? 'Submitting...' : 'Submit Quiz'}
                </button>
              </div>
            )}
          </div>
        );
        
      case 'quiz-results':
        return (
          <div>
            <button onClick={handleBackFromResults} style={{ marginBottom: 20, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer' }}>
              <i className="fas fa-arrow-left"></i> Back to Module
            </button>
            
            {quizResults && (
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, textAlign: 'center' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>
                  {quizResults.passed ? '🎉' : '❌'}
                </div>
                <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
                  {quizResults.passed ? 'Quiz Passed!' : 'Quiz Failed'}
                </h2>
                <p style={{ fontSize: 18, marginBottom: 16 }}>Score: {quizResults.score}%</p>
                <p style={{ fontSize: 14, color: 'var(--text-dim)' }}>{quizResults.message}</p>
              </div>
            )}
          </div>
        );
        
      case 'final-exam':
        return (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h2 style={{ fontSize: 24, fontWeight: 700 }}>Final Certification Exam</h2>
              {timeRemaining > 0 && (
                <div style={{ fontSize: 18, fontWeight: 700, color: timeRemaining < 300 ? '#ef4444' : '#10b981' }}>
                  <i className="fas fa-clock"></i> {formatTime(timeRemaining)}
                </div>
              )}
            </div>
            
            <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
              <p style={{ marginBottom: 20, color: 'var(--text-dim)' }}>Answer all 200 questions. You need 80% to pass.</p>
              
              {finalExamQuestions && finalExamQuestions.questions && (
                <div>
                  {finalExamQuestions.questions.map((q: QuizQuestion, idx: number) => (
                    <div key={q.id} style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid var(--border)' }}>
                      <div style={{ fontWeight: 600, marginBottom: 8 }}>{idx + 1}. {q.question}</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {q.options.map((opt: string, optIdx: number) => (
                          <label
                            key={optIdx}
                            style={{
                              padding: '8px',
                              background: answers[q.id] === optIdx ? 'var(--primary)' : 'var(--surface)',
                              border: '1px solid var(--border)',
                              borderRadius: 6,
                              cursor: 'pointer',
                              fontSize: 13,
                              color: answers[q.id] === optIdx ? '#fff' : 'var(--text)'
                            }}
                          >
                            <input
                              type="radio"
                              name={`final-q-${q.id}`}
                              value={optIdx}
                              checked={answers[q.id] === optIdx}
                              onChange={() => handleAnswerChange(q.id, optIdx)}
                              style={{ marginRight: 8 }}
                            />
                            {opt}
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              <button
                onClick={handleSubmitFinalExam}
                disabled={loading}
                style={{
                  marginTop: 20,
                  padding: '12px 24px',
                  background: '#10b981',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontWeight: 600,
                  opacity: loading ? 0.6 : 1
                }}
              >
                {loading ? 'Submitting...' : 'Submit Final Exam'}
              </button>
            </div>
          </div>
        );
        
      case 'exam-results':
        return (
          <div>
            {quizResults && (
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, textAlign: 'center' }}>
                <div style={{ fontSize: 64, marginBottom: 16 }}>
                  {quizResults.passed ? '🎓' : '❌'}
                </div>
                <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
                  {quizResults.passed ? 'Congratulations!' : 'Exam Failed'}
                </h2>
                <p style={{ fontSize: 20, marginBottom: 16 }}>Score: {quizResults.score}%</p>
                <p style={{ fontSize: 16, color: 'var(--text-dim)', marginBottom: 24 }}>{quizResults.message}</p>
                
                {quizResults.passed && (
                  <button
                    onClick={() => {
                      const certUrl = window.prompt('Certificate URL:', quizResults.certificate_url);
                      if (certUrl) window.open(certUrl, '_blank');
                    }}
                    style={{
                      padding: '12px 24px',
                      background: '#10b981',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 8,
                      cursor: 'pointer',
                      fontWeight: 600
                    }}
                  >
                    <i className="fas fa-certificate"></i> Download Certificate
                  </button>
                )}
              </div>
            )}
          </div>
        );
        
      default:
        return <div>Loading...</div>;
    }
  };

  const overallPct = progress?.overall_progress || 0;

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

      {/* Progress banner */}
      {currentScreen === 'module-list' && progress && (
        <div className="training-hero" style={{ marginLeft: 0, marginRight: 0 }}>
          <div className="training-hero-content">
            <span className="eyebrow">Agent Certification Programme</span>
            <h2>Master ZimAgritrust Platform Operations</h2>
            <p>Complete all modules, pass the assessments, and earn your Field Agent certification.</p>
          </div>
          <div className="training-progress-card">
            <div
              className="academy-progress-ring"
              style={{ '--progress': `${overallPct * 3.6}deg` } as React.CSSProperties}
            >
              <span>{Math.round(overallPct)}%</span>
            </div>
            <strong>{Math.round(overallPct)}%</strong>
            <span>Overall Progress</span>
          </div>
        </div>
      )}

      {/* Content */}
      {renderScreen()}

      {/* Notifications */}
      {error && (
        <div className="alert alert-error" style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1000, maxWidth: 360 }}>
          <i className="fas fa-exclamation-circle"></i> {error}
          <button onClick={() => setError(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}>
            <i className="fas fa-times"></i>
          </button>
        </div>
      )}

      {success && (
        <div className="alert alert-success" style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1000, maxWidth: 360 }}>
          <i className="fas fa-check-circle"></i> {success}
          <button onClick={() => setSuccess(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}>
            <i className="fas fa-times"></i>
          </button>
        </div>
      )}
    </div>
  );
};

export default Academy;
