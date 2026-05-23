import React from "react";

export default function QuizTaking({ quizData, currentQuestionIndex, answers, timeRemaining, onAnswerChange, onPrevious, onNext, onSubmit, loading }) {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const urgent = timeRemaining > 0 && timeRemaining < 60;
  const q = quizData?.questions?.[currentQuestionIndex];
  const qId = q?.id;
  const answered = (id) => !!answers[id];

  return (
    <div style={{ maxWidth: 800, paddingTop: 8 }}>
      {/* Quiz header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 900, color: 'var(--text)' }}>
            <i className="fas fa-pencil-alt" style={{ color: 'var(--primary)', marginRight: 10 }}></i>
            {quizData?.title || 'Quiz'}
          </h2>
          {quizData?.questions && (
            <p style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 4 }}>
              {quizData.questions.filter(q2 => answered(q2.id)).length} of {quizData.questions.length} answered
            </p>
          )}
        </div>
        {timeRemaining > 0 && (
          <div className={`badge ${urgent ? 'badge-red' : 'badge-blue'}`} style={{ fontSize: 16, padding: '8px 16px', fontVariantNumeric: 'tabular-nums' }}>
            <i className={`fas fa-clock${urgent ? ' fa-beat' : ''}`}></i>
            {formatTime(timeRemaining)}
          </div>
        )}
      </div>

      {quizData && quizData.questions && (
        <div>
          {/* Question navigator */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
            {quizData.questions.map((q2, idx) => (
              <button
                key={idx}
                onClick={() => onAnswerChange?.('navigate', idx)}
                style={{
                  width: 36, height: 36,
                  borderRadius: '50%',
                  border: currentQuestionIndex === idx
                    ? '2px solid var(--primary)'
                    : '1px solid var(--border)',
                  background: currentQuestionIndex === idx
                    ? 'var(--primary)'
                    : answered(q2.id)
                      ? 'rgba(16,185,129,.15)'
                      : 'var(--surface2)',
                  color: currentQuestionIndex === idx ? '#fff' : answered(q2.id) ? 'var(--primary)' : 'var(--text-dim)',
                  cursor: 'pointer',
                  fontWeight: 700,
                  fontSize: 13,
                  transition: 'all .15s',
                }}
              >
                {idx + 1}
              </button>
            ))}
          </div>

          {/* Current question */}
          {q && (
            <div className="card" style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 20 }}>
                <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.8px', display: 'block', marginBottom: 8 }}>
                  Question {currentQuestionIndex + 1} of {quizData.questions.length}
                </span>
                <h3 style={{ fontSize: 17, fontWeight: 700, color: 'var(--text)', lineHeight: 1.5 }}>
                  {q.question_text}
                </h3>
              </div>

              {/* Multiple choice */}
              {q.question_type === 'multiple_choice' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {q.options && q.options.map((option, idx) => {
                    const selected = answers[qId] === String(idx);
                    return (
                      <label
                        key={idx}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 12,
                          padding: '12px 16px',
                          background: selected ? 'rgba(16,185,129,.12)' : 'var(--surface2)',
                          borderRadius: 10,
                          cursor: 'pointer',
                          border: selected ? '1.5px solid var(--primary)' : '1.5px solid var(--border)',
                          transition: 'all .15s',
                        }}
                      >
                        <input
                          type="radio"
                          name={`question-${qId}`}
                          value={idx}
                          checked={selected}
                          onChange={(e) => onAnswerChange?.(qId, e.target.value)}
                          style={{ accentColor: 'var(--primary)', width: 16, height: 16 }}
                        />
                        <span style={{ fontSize: 14, color: selected ? 'var(--text)' : 'var(--text-dim)', fontWeight: selected ? 600 : 400 }}>
                          {option}
                        </span>
                      </label>
                    );
                  })}
                </div>
              )}

              {/* True / False */}
              {q.question_type === 'true_false' && (
                <div style={{ display: 'flex', gap: 12 }}>
                  {['true', 'false'].map((val) => {
                    const selected = answers[qId] === val;
                    return (
                      <label
                        key={val}
                        style={{
                          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                          padding: '14px 24px',
                          background: selected ? 'rgba(16,185,129,.12)' : 'var(--surface2)',
                          borderRadius: 10,
                          cursor: 'pointer',
                          border: selected ? '1.5px solid var(--primary)' : '1.5px solid var(--border)',
                          transition: 'all .15s',
                          fontWeight: 700,
                          fontSize: 14,
                          color: selected ? 'var(--primary)' : 'var(--text-dim)',
                        }}
                      >
                        <input
                          type="radio"
                          name={`question-${qId}`}
                          value={val}
                          checked={selected}
                          onChange={(e) => onAnswerChange?.(qId, e.target.value)}
                          style={{ accentColor: 'var(--primary)', width: 16, height: 16 }}
                        />
                        <i className={`fas fa-${val === 'true' ? 'check' : 'times'}`}></i>
                        {val.charAt(0).toUpperCase() + val.slice(1)}
                      </label>
                    );
                  })}
                </div>
              )}

              {/* Essay */}
              {q.question_type === 'essay' && (
                <textarea
                  className="form-textarea"
                  value={answers[qId] || ''}
                  onChange={(e) => onAnswerChange?.(qId, e.target.value)}
                  placeholder="Type your answer here…"
                  rows={6}
                />
              )}
            </div>
          )}

          {/* Navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
            <button
              className="btn btn-ghost"
              onClick={onPrevious}
              disabled={currentQuestionIndex === 0}
            >
              <i className="fas fa-arrow-left"></i> Previous
            </button>

            {currentQuestionIndex === quizData.questions.length - 1 ? (
              <button
                className="btn btn-primary btn-lg"
                onClick={onSubmit}
                disabled={loading}
              >
                {loading
                  ? <><i className="fas fa-spinner fa-spin"></i> Submitting…</>
                  : <><i className="fas fa-check"></i> Submit Quiz</>
                }
              </button>
            ) : (
              <button
                className="btn btn-primary"
                onClick={onNext}
              >
                Next <i className="fas fa-arrow-right"></i>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
