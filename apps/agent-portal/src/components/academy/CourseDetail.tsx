import React from "react";

const resourceIcon = (type) => {
  switch (type) {
    case 'document': return 'fa-file-alt';
    case 'video':    return 'fa-video';
    case 'image':    return 'fa-image';
    case 'link':     return 'fa-link';
    case 'quiz':     return 'fa-question-circle';
    default:         return 'fa-file';
  }
};

export default function CourseDetail({ courseDetail, announcements, onBack, onCompleteTopic, onStartQuiz, onReadResource }) {
  return (
    <div style={{ paddingTop: 8 }}>
      <button className="btn btn-ghost btn-sm" onClick={onBack} style={{ marginBottom: 24 }}>
        <i className="fas fa-arrow-left"></i> Back to Courses
      </button>

      {courseDetail && (
        <div>
          {/* Course header */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ flex: 1 }}>
                <span className="eyebrow" style={{ fontSize: 10, fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '1.2px', display: 'block', marginBottom: 6 }}>
                  Module {courseDetail.module_number}
                </span>
                <h2 style={{ fontSize: 24, fontWeight: 900, color: 'var(--text)', marginBottom: 8 }}>
                  {courseDetail.title}
                </h2>
                <p style={{ fontSize: 14, color: 'var(--text-dim)', lineHeight: 1.6, maxWidth: 600 }}>
                  {courseDetail.description}
                </p>
              </div>
              <div style={{ minWidth: 160 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>
                  <span>Overall Progress</span>
                  <span style={{ fontWeight: 700, color: 'var(--text)' }}>{courseDetail.progress_percentage.toFixed(1)}%</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${courseDetail.progress_percentage}%`,
                      background: courseDetail.progress_percentage === 100
                        ? 'var(--primary)'
                        : 'linear-gradient(90deg, var(--info), var(--primary))'
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Announcements */}
          {announcements.length > 0 && (
            <div className="alert alert-info" style={{ marginBottom: 24 }}>
              <i className="fas fa-bullhorn"></i>
              <div>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>Announcements</div>
                {announcements.map(a => (
                  <div key={a.id} style={{ fontSize: 13, marginTop: 4 }}>{a.message}</div>
                ))}
              </div>
            </div>
          )}

          {/* Topics */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 800, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '.5px' }}>
              <i className="fas fa-list-ul" style={{ marginRight: 8, color: 'var(--primary)' }}></i>Classwork
            </h3>

            {courseDetail.topics && courseDetail.topics.length > 0 ? (
              courseDetail.topics.map(topic => (
                <div
                  key={topic.id}
                  className="card"
                  style={{ padding: 0, overflow: 'hidden' }}
                >
                  {/* Topic header */}
                  <div
                    style={{
                      padding: '14px 18px',
                      borderBottom: '1px solid var(--border)',
                      background: topic.is_completed
                        ? 'rgba(16,185,129,.08)'
                        : topic.is_locked
                          ? 'rgba(245,158,11,.05)'
                          : 'var(--surface2)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12
                    }}
                  >
                    {topic.is_completed
                      ? <i className="fas fa-check-circle" style={{ fontSize: 18, color: 'var(--success)' }}></i>
                      : topic.is_locked
                        ? <i className="fas fa-lock" style={{ fontSize: 18, color: 'var(--warning)' }}></i>
                        : <i className="fas fa-circle" style={{ fontSize: 18, color: 'var(--info)' }}></i>
                    }
                    <h4 style={{ flex: 1, fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>
                      {topic.title}
                    </h4>
                    {topic.is_completed && (
                      <span className="badge badge-green"><i className="fas fa-check"></i> Complete</span>
                    )}
                    {!topic.is_locked && !topic.is_completed && (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => onCompleteTopic?.(topic.id)}
                      >
                        <i className="fas fa-check"></i> Mark Complete
                      </button>
                    )}
                  </div>

                  {/* Resources */}
                  <div style={{ padding: '12px 18px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {topic.resources && topic.resources.length > 0 ? (
                      topic.resources.map(resource => (
                        <div
                          key={resource.id}
                          className="academy-topic-row"
                          style={{ opacity: resource.is_locked ? 0.5 : 1 }}
                        >
                          <button
                            className="academy-topic-open"
                            onClick={() => !resource.is_locked && resource.resource_type !== 'quiz' && onReadResource?.(resource)}
                            disabled={resource.is_locked}
                          >
                            <i
                              className={`fas ${resourceIcon(resource.resource_type)}`}
                              style={{ color: 'var(--primary)', width: 16 }}
                            ></i>
                            {resource.title}
                          </button>

                          {resource.resource_type === 'quiz' ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                              {resource.quiz_info && (
                                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                  {resource.quiz_info.question_count} Q
                                  {resource.quiz_info.time_limit_minutes ? ` · ${resource.quiz_info.time_limit_minutes} min` : ''}
                                  {resource.quiz_info.passing_score ? ` · Pass: ${resource.quiz_info.passing_score}%` : ''}
                                </span>
                              )}
                              <button
                                className="btn btn-sm"
                                onClick={() => !resource.is_locked && onStartQuiz?.(resource.id)}
                                disabled={resource.is_locked}
                                style={{ background: resource.is_locked ? 'var(--surface2)' : '#7c3aed', color: resource.is_locked ? 'var(--text-muted)' : '#fff' }}
                              >
                                <i className="fas fa-pencil-alt"></i> {resource.is_locked ? 'Locked' : 'Take Quiz'}
                              </button>
                            </div>
                          ) : (
                            <button
                              className="btn btn-sm"
                              onClick={() => !resource.is_locked && onReadResource?.(resource)}
                              disabled={resource.is_locked}
                              style={{ background: resource.is_locked ? 'var(--surface2)' : 'var(--info)', color: resource.is_locked ? 'var(--text-muted)' : '#fff' }}
                            >
                              <i className={`fas ${resource.resource_type === 'video' ? 'fa-play' : 'fa-book-open'}`}></i>
                              {resource.resource_type === 'video' ? 'Watch' : 'Read'}
                            </button>
                          )}
                        </div>
                      ))
                    ) : (
                      <p style={{ fontSize: 13, color: 'var(--text-muted)', padding: '4px 0' }}>No resources yet</p>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p style={{ fontSize: 14, color: 'var(--text-dim)', textAlign: 'center', padding: 32 }}>No topics yet</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
