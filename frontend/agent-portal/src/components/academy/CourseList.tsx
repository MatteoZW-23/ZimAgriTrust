import React from "react";

export default function CourseList({ courses, loading, onCourseSelect }) {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-dim)' }}>
        <div className="spinner" style={{ margin: '0 auto 16px', width: 36, height: 36, border: '3px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin .7s linear infinite' }}></div>
        Loading courses…
      </div>
    );
  }

  if (!courses.length) {
    return (
      <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-dim)' }}>
        <i className="fas fa-graduation-cap" style={{ fontSize: 48, marginBottom: 16, color: 'var(--primary)', opacity: .4 }}></i>
        <p>No courses available yet.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
        {courses.map(course => (
          <div
            key={course.id}
            className={`academy-module-card${course.is_locked ? ' locked' : ''}`}
          >
            <div className="academy-module-head">
              <div>
                <span className="eyebrow">Module {course.module_number}</span>
                <div className="card-title">{course.title}</div>
              </div>
              {course.is_locked
                ? <span className="badge badge-yellow"><i className="fas fa-lock"></i></span>
                : course.progress_percentage === 100
                  ? <span className="badge badge-green"><i className="fas fa-check"></i> Done</span>
                  : <span className="badge badge-blue">In Progress</span>
              }
            </div>

            <div className="academy-module-meta">
              <i className="fas fa-book-open"></i>
              {course.topic_count ?? '—'} topics
            </div>

            <div className="academy-topic-progress">
              <div style={{ width: `${course.progress_percentage}%` }}></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-dim)', marginBottom: 16 }}>
              <span>Progress</span>
              <span style={{ fontWeight: 700, color: course.progress_percentage === 100 ? 'var(--primary)' : 'var(--text)' }}>
                {course.progress_percentage.toFixed(1)}%
              </span>
            </div>

            {course.grade != null && (
              <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 14 }}>
                Grade:{' '}
                <strong style={{ color: course.grade >= 80 ? 'var(--success)' : 'var(--warning)' }}>
                  {course.grade.toFixed(1)}%
                </strong>
              </div>
            )}

            <button
              className={`btn btn-full${course.is_locked ? ' btn-ghost' : ' btn-primary'}`}
              onClick={() => {
                if (course.is_locked) {
                  onCourseSelect?.(course, course.lock_message || 'This course is locked');
                } else {
                  onCourseSelect?.(course);
                }
              }}
              disabled={course.is_locked}
            >
              {course.is_locked
                ? <><i className="fas fa-lock"></i> {course.lock_message || 'Locked'}</>
                : course.progress_percentage === 100
                  ? <><i className="fas fa-redo"></i> Review</>
                  : <><i className="fas fa-play"></i> Continue</>
              }
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
