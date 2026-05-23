/**
 * ZimAgritrust – Agent Training Academy (Google Classroom Style)
 * Admin Portal Screens
 * 
 * Screens:
 * 1. Course Management - List all courses
 * 2. Course Detail - View/edit course with topics, resources, students
 * 3. Create Course - Form to create new course
 * 4. Add Resource - Add resources (documents, videos, quizzes) to topics
 * 5. Grade Essay - Grade essay submissions
 */

import React, { useState, useEffect } from 'react';

const AcademyManagement = ({ token }) => {
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  
  // Screen states
  const [currentScreen, setCurrentScreen] = useState('course-list');
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [selectedEssay, setSelectedEssay] = useState(null);
  
  // Data states
  const [courses, setCourses] = useState([]);
  const [courseTopics, setCourseTopics] = useState([]);
  const [students, setStudents] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [agents, setAgents] = useState([]);
  
  // Form states
  const [courseForm, setCourseForm] = useState({
    title: '',
    description: '',
    module_number: 1,
    passing_score: 80,
    estimated_hours: 2,
    is_active: true
  });
  
  const [resourceForm, setResourceForm] = useState({
    topic_id: '',
    resource_type: 'document',
    title: '',
    content_url: '',
    content_text: '',
    order_sequence: 0,
    time_limit_minutes: null,
    passing_score: 80
  });
  
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [newQuestion, setNewQuestion] = useState({
    question_text: '',
    question_type: 'multiple_choice',
    options: ['', '', '', ''],
    correct_answer: '0',
    points: 1,
    order_sequence: 0
  });
  
  const [announcementForm, setAnnouncementForm] = useState({ message: '' });
  const [essayGrade, setEssayGrade] = useState({ grade: 0, feedback: '' });
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Fetch courses
  const fetchCourses = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/classroom/courses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch courses');
      const data = await response.json();
      setCourses(data);
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
      const response = await fetch(`${API_BASE}/api/v1/admin/classroom/courses/${courseId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch course detail');
      const data = await response.json();
      setSelectedCourse(data);
      setCourseTopics(data.topics || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch students for a course
  const fetchStudents = async (courseId) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/classroom/courses/${courseId}/students`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch students');
      const data = await response.json();
      setStudents(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch all agents for invitation
  const fetchAgents = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/agents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch agents');
      const data = await response.json();
      setAgents(data.agents || []);
    } catch (err) {
      setError(err.message);
    }
  };
  
  // Create course
  const createCourse = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/classroom/courses`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(courseForm)
      });
      if (!response.ok) throw new Error('Failed to create course');
      setSuccess('Course created successfully!');
      setCourseForm({
        title: '',
        description: '',
        module_number: 1,
        passing_score: 80,
        estimated_hours: 2,
        is_active: true
      });
      setCurrentScreen('course-list');
      fetchCourses();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Add resource
  const addResource = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...resourceForm,
        course_id: selectedCourse.id,
        topic_id: resourceForm.topic_id || null
      };
      
      const response = await fetch(`${API_BASE}/api/v1/admin/classroom/courses/${selectedCourse.id}/resources`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) throw new Error('Failed to add resource');
      
      // If it's a quiz, add questions
      if (resourceForm.resource_type === 'quiz' && quizQuestions.length > 0) {
        const resourceData = await response.json();
        for (const question of quizQuestions) {
          await fetch(`${API_BASE}/api/v1/admin/classroom/courses/${selectedCourse.id}/resources`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              resource_id: resourceData.id,
              question_text: question.question_text,
              question_type: question.question_type,
              options: question.options,
              correct_answer: question.correct_answer,
              points: question.points,
              order_sequence: question.order_sequence
            })
          });
        }
      }
      
      setSuccess('Resource added successfully!');
      setResourceForm({
        topic_id: '',
        resource_type: 'document',
        title: '',
        content_url: '',
        content_text: '',
        order_sequence: 0,
        time_limit_minutes: null,
        passing_score: 80
      });
      setQuizQuestions([]);
      fetchCourseDetail(selectedCourse.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Add quiz question
  const addQuizQuestion = () => {
    setQuizQuestions([...quizQuestions, { ...newQuestion, order_sequence: quizQuestions.length }]);
    setNewQuestion({
      question_text: '',
      question_type: 'multiple_choice',
      options: ['', '', '', ''],
      correct_answer: '0',
      points: 1,
      order_sequence: quizQuestions.length + 1
    });
  };
  
  // Create announcement
  const createAnnouncement = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/classroom/courses/${selectedCourse.id}/announcements`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          course_id: selectedCourse.id,
          message: announcementForm.message
        })
      });
      if (!response.ok) throw new Error('Failed to create announcement');
      setSuccess('Announcement created successfully!');
      setAnnouncementForm({ message: '' });
      fetchCourseDetail(selectedCourse.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Invite students
  const inviteStudents = async (selectedAgentIds) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/classroom/courses/${selectedCourse.id}/invite`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ agent_ids: selectedAgentIds })
      });
      if (!response.ok) throw new Error('Failed to invite students');
      setSuccess('Students invited successfully!');
      fetchStudents(selectedCourse.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Grade essay
  const gradeEssay = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/classroom/essays/${selectedEssay.id}/grade`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(essayGrade)
      });
      if (!response.ok) throw new Error('Failed to grade essay');
      setSuccess('Essay graded successfully!');
      setSelectedEssay(null);
      setEssayGrade({ grade: 0, feedback: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchCourses();
  }, []);
  
  // Screen: Course List
  const renderCourseList = () => (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#1e293b' }}>My Courses</h2>
        <button
          onClick={() => setCurrentScreen('create-course')}
          style={{
            padding: '10px 20px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          <i className="fas fa-plus" style={{ marginRight: '8px' }}></i>
          Create Course
        </button>
      </div>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px' }}>Loading...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
          {courses.map(course => (
            <div
              key={course.id}
              style={{
                background: 'white',
                borderRadius: '12px',
                padding: '20px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                border: '1px solid #e2e8f0'
              }}
            >
              <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px', color: '#1e293b' }}>
                {course.title}
              </h3>
              <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '12px' }}>
                Module {course.module_number}
              </p>
              <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
                <span><i className="fas fa-users" style={{ marginRight: '4px' }}></i>{course.students_enrolled} students</span>
                <span><i className="fas fa-file" style={{ marginRight: '4px' }}></i>{course.resources_count} resources</span>
                <span><i className="fas fa-question-circle" style={{ marginRight: '4px' }}></i>{course.quiz_count} quizzes</span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => {
                    setSelectedCourse(course);
                    fetchCourseDetail(course.id);
                    setCurrentScreen('course-detail');
                  }}
                  style={{
                    flex: 1,
                    padding: '8px',
                    background: '#f1f5f9',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    color: '#475569'
                  }}
                >
                  View
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
  
  // Screen: Create Course
  const renderCreateCourse = () => (
    <div style={{ padding: '24px', maxWidth: '600px' }}>
      <button
        onClick={() => setCurrentScreen('course-list')}
        style={{
          padding: '8px 16px',
          background: '#f1f5f9',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          marginBottom: '24px'
        }}
      >
        <i className="fas fa-arrow-left" style={{ marginRight: '8px' }}></i>
        Back to Courses
      </button>
      
      <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', color: '#1e293b' }}>
        Create Course
      </h2>
      
      <form onSubmit={createCourse} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
            Course Title
          </label>
          <input
            type="text"
            value={courseForm.title}
            onChange={(e) => setCourseForm({ ...courseForm, title: e.target.value })}
            required
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          />
        </div>
        
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
            Description
          </label>
          <textarea
            value={courseForm.description}
            onChange={(e) => setCourseForm({ ...courseForm, description: e.target.value })}
            rows={3}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          />
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
              Module Number
            </label>
            <input
              type="number"
              value={courseForm.module_number}
              onChange={(e) => setCourseForm({ ...courseForm, module_number: parseInt(e.target.value) })}
              min="1"
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>
          
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
              Passing Score (%)
            </label>
            <input
              type="number"
              value={courseForm.passing_score}
              onChange={(e) => setCourseForm({ ...courseForm, passing_score: parseFloat(e.target.value) })}
              min="0"
              max="100"
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>
        </div>
        
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
            Estimated Hours
          </label>
          <input
            type="number"
            value={courseForm.estimated_hours}
            onChange={(e) => setCourseForm({ ...courseForm, estimated_hours: parseFloat(e.target.value) })}
            min="0.5"
            step="0.5"
            required
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          />
        </div>
        
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '12px 24px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Creating...' : 'Create Course'}
        </button>
      </form>
    </div>
  );
  
  // Screen: Course Detail
  const renderCourseDetail = () => (
    <div style={{ padding: '24px' }}>
      <button
        onClick={() => {
          setCurrentScreen('course-list');
          setSelectedCourse(null);
        }}
        style={{
          padding: '8px 16px',
          background: '#f1f5f9',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          marginBottom: '24px'
        }}
      >
        <i className="fas fa-arrow-left" style={{ marginRight: '8px' }}></i>
        Back to Courses
      </button>
      
      {selectedCourse && (
        <div>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '8px', color: '#1e293b' }}>
              {selectedCourse.title}
            </h2>
            <p style={{ fontSize: '16px', color: '#64748b', marginBottom: '16px' }}>
              {selectedCourse.description}
            </p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setCurrentScreen('add-resource')}
                style={{
                  padding: '10px 20px',
                  background: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                <i className="fas fa-plus" style={{ marginRight: '8px' }}></i>
                Add Resource
              </button>
              <button
                onClick={() => {
                  fetchStudents(selectedCourse.id);
                  fetchAgents();
                  setCurrentScreen('invite-students');
                }}
                style={{
                  padding: '10px 20px',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                <i className="fas fa-user-plus" style={{ marginRight: '8px' }}></i>
                Invite Students
              </button>
            </div>
          </div>
          
          {/* Tabs */}
          <div style={{ borderBottom: '2px solid #e2e8f0', marginBottom: '24px' }}>
            <div style={{ display: 'flex', gap: '24px' }}>
              <button style={{ padding: '12px 0', borderBottom: '2px solid #3b82f6', color: '#3b82f6', fontWeight: '600', background: 'none', border: 'none' }}>
                Classwork
              </button>
              <button
                onClick={() => {
                  fetchStudents(selectedCourse.id);
                  setCurrentScreen('view-students');
                }}
                style={{ padding: '12px 0', color: '#64748b', fontWeight: '500', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Students
              </button>
            </div>
          </div>
          
          {/* Topics */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {courseTopics.map(topic => (
              <div
                key={topic.id}
                style={{
                  background: 'white',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  overflow: 'hidden'
                }}
              >
                <div style={{ padding: '16px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
                  <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b' }}>
                    Topic {topic.topic_number}: {topic.title}
                  </h4>
                </div>
                <div style={{ padding: '16px' }}>
                  {topic.resources && topic.resources.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {topic.resources.map(resource => (
                        <div
                          key={resource.id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            padding: '12px',
                            background: '#f8fafc',
                            borderRadius: '8px',
                            gap: '12px'
                          }}
                        >
                          <i
                            className={`fas ${
                              resource.resource_type === 'document' ? 'fa-file-alt' :
                              resource.resource_type === 'video' ? 'fa-video' :
                              resource.resource_type === 'quiz' ? 'fa-question-circle' :
                              'fa-link'
                            }`}
                            style={{ fontSize: '18px', color: '#64748b' }}
                          ></i>
                          <span style={{ flex: 1, fontSize: '14px', color: '#374151' }}>{resource.title}</span>
                          <span style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'capitalize' }}>
                            {resource.resource_type}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ fontSize: '14px', color: '#94a3b8' }}>No resources yet</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
  
  // Screen: Add Resource
  const renderAddResource = () => (
    <div style={{ padding: '24px', maxWidth: '800px' }}>
      <button
        onClick={() => setCurrentScreen('course-detail')}
        style={{
          padding: '8px 16px',
          background: '#f1f5f9',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          marginBottom: '24px'
        }}
      >
        <i className="fas fa-arrow-left" style={{ marginRight: '8px' }}></i>
        Back to Course
      </button>
      
      <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', color: '#1e293b' }}>
        Add Resource
      </h2>
      
      <form onSubmit={addResource} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
            Resource Type
          </label>
          <select
            value={resourceForm.resource_type}
            onChange={(e) => setResourceForm({ ...resourceForm, resource_type: e.target.value })}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          >
            <option value="document">Document</option>
            <option value="video">Video</option>
            <option value="image">Image</option>
            <option value="link">Link</option>
            <option value="quiz">Quiz</option>
          </select>
        </div>
        
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
            Title
          </label>
          <input
            type="text"
            value={resourceForm.title}
            onChange={(e) => setResourceForm({ ...resourceForm, title: e.target.value })}
            required
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          />
        </div>
        
        {resourceForm.resource_type !== 'quiz' && (
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
              Content URL
            </label>
            <input
              type="text"
              value={resourceForm.content_url}
              onChange={(e) => setResourceForm({ ...resourceForm, content_url: e.target.value })}
              placeholder="https://..."
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>
        )}
        
        {resourceForm.resource_type === 'quiz' && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
                  Time Limit (minutes)
                </label>
                <input
                  type="number"
                  value={resourceForm.time_limit_minutes || ''}
                  onChange={(e) => setResourceForm({ ...resourceForm, time_limit_minutes: parseInt(e.target.value) })}
                  min="1"
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '6px', color: '#374151' }}>
                  Passing Score (%)
                </label>
                <input
                  type="number"
                  value={resourceForm.passing_score}
                  onChange={(e) => setResourceForm({ ...resourceForm, passing_score: parseFloat(e.target.value) })}
                  min="0"
                  max="100"
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                />
              </div>
            </div>
            
            {/* Quiz Questions */}
            <div style={{ marginTop: '16px', padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
              <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#1e293b' }}>
                Quiz Questions ({quizQuestions.length})
              </h4>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
                {quizQuestions.map((q, idx) => (
                  <div key={idx} style={{ padding: '12px', background: 'white', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                    <p style={{ fontSize: '14px', fontWeight: '500', marginBottom: '8px', color: '#374151' }}>
                      {idx + 1}. {q.question_text}
                    </p>
                    <p style={{ fontSize: '12px', color: '#64748b' }}>
                      Type: {q.question_type} | Points: {q.points}
                    </p>
                  </div>
                ))}
              </div>
              
              <div style={{ padding: '16px', background: 'white', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <input
                  type="text"
                  placeholder="Question text"
                  value={newQuestion.question_text}
                  onChange={(e) => setNewQuestion({ ...newQuestion, question_text: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px',
                    marginBottom: '12px'
                  }}
                />
                
                <select
                  value={newQuestion.question_type}
                  onChange={(e) => setNewQuestion({ ...newQuestion, question_type: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px',
                    marginBottom: '12px'
                  }}
                >
                  <option value="multiple_choice">Multiple Choice</option>
                  <option value="true_false">True/False</option>
                  <option value="essay">Essay</option>
                </select>
                
                {newQuestion.question_type === 'multiple_choice' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                    {newQuestion.options.map((opt, idx) => (
                      <input
                        key={idx}
                        type="text"
                        placeholder={`Option ${idx + 1}`}
                        value={opt}
                        onChange={(e) => {
                          const newOptions = [...newQuestion.options];
                          newOptions[idx] = e.target.value;
                          setNewQuestion({ ...newQuestion, options: newOptions });
                        }}
                        style={{
                          width: '100%',
                          padding: '8px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '14px'
                        }}
                      />
                    ))}
                  </div>
                )}
                
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="number"
                    placeholder="Points"
                    value={newQuestion.points}
                    onChange={(e) => setNewQuestion({ ...newQuestion, points: parseInt(e.target.value) })}
                    min="1"
                    style={{
                      flex: 1,
                      padding: '8px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}
                  />
                  <button
                    type="button"
                    onClick={addQuizQuestion}
                    style={{
                      padding: '8px 16px',
                      background: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: '500'
                    }}
                  >
                    Add Question
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
        
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '12px 24px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Adding...' : 'Add Resource'}
        </button>
      </form>
    </div>
  );
  
  // Screen: Invite Students
  const renderInviteStudents = () => (
    <div style={{ padding: '24px', maxWidth: '800px' }}>
      <button
        onClick={() => setCurrentScreen('course-detail')}
        style={{
          padding: '8px 16px',
          background: '#f1f5f9',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          marginBottom: '24px'
        }}
      >
        <i className="fas fa-arrow-left" style={{ marginRight: '8px' }}></i>
        Back to Course
      </button>
      
      <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', color: '#1e293b' }}>
        Invite Students
      </h2>
      
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
          Enrolled Students ({students.length})
        </h3>
        {students.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {students.map(student => (
              <div
                key={student.agent_id}
                style={{
                  padding: '12px',
                  background: 'white',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <span style={{ fontSize: '14px', color: '#374151' }}>{student.agent_name}</span>
                <span style={{ fontSize: '12px', color: '#64748b' }}>
                  Progress: {student.progress_percentage.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: '14px', color: '#94a3b8' }}>No students enrolled yet</p>
        )}
      </div>
      
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#1e293b' }}>
          Available Agents
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {agents.filter(agent => !students.find(s => s.agent_id === agent.id)).map(agent => (
            <div
              key={agent.id}
              style={{
                padding: '12px',
                background: 'white',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <span style={{ fontSize: '14px', color: '#374151' }}>{agent.user?.full_name || 'Unknown'}</span>
              <button
                onClick={() => inviteStudents([agent.id])}
                style={{
                  padding: '6px 12px',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: '500'
                }}
              >
                Invite
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
  
  // Render current screen
  const renderScreen = () => {
    switch (currentScreen) {
      case 'course-list':
        return renderCourseList();
      case 'create-course':
        return renderCreateCourse();
      case 'course-detail':
        return renderCourseDetail();
      case 'add-resource':
        return renderAddResource();
      case 'invite-students':
        return renderInviteStudents();
      default:
        return renderCourseList();
    }
  };
  
  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
      {/* Header */}
      <div style={{
        background: 'white',
        borderBottom: '1px solid #e2e8f0',
        padding: '16px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <i className="fas fa-graduation-cap" style={{ fontSize: '24px', color: '#3b82f6' }}></i>
          <h1 style={{ fontSize: '20px', fontWeight: 'bold', color: '#1e293b' }}>
            ZimAgriTrust Academy
          </h1>
        </div>
      </div>
      
      {/* Content */}
      {renderScreen()}
      
      {/* Notifications */}
      {error && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          padding: '16px 24px',
          background: '#ef4444',
          color: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 1000
        }}>
          {error}
        </div>
      )}
      
      {success && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          padding: '16px 24px',
          background: '#10b981',
          color: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          zIndex: 1000
        }}>
          {success}
        </div>
      )}
    </div>
  );
};

export default AcademyManagement;
