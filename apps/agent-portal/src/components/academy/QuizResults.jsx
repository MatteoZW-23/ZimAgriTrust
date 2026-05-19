import React from "react";

export default function QuizResults({ quizResults, onBack }) {
  return (
    <div style={{ padding: '24px', maxWidth: '800px' }}>
      <button
        onClick={onBack}
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
      
      {quizResults && (
        <div>
          <div style={{
            background: quizResults.passed ? '#f0fdf4' : '#fef2f2',
            borderRadius: '12px',
            padding: '24px',
            border: quizResults.passed ? '1px solid #bbf7d0' : '1px solid #fecaca',
            marginBottom: '24px'
          }}>
            <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '8px', color: quizResults.passed ? '#166534' : '#991b1b' }}>
              {quizResults.passed ? '🎉 Quiz Passed!' : '❌ Quiz Failed'}
            </h2>
            <p style={{ fontSize: '16px', color: quizResults.passed ? '#166534' : '#991b1b', marginBottom: '16px' }}>
              {quizResults.message}
            </p>
            <div style={{ fontSize: '48px', fontWeight: 'bold', color: quizResults.passed ? '#166534' : '#991b1b' }}>
              {quizResults.score}%
            </div>
          </div>
          
          {quizResults.results && (
            <div style={{
              background: 'white',
              borderRadius: '12px',
              padding: '24px',
              border: '1px solid #e2e8f0'
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px', color: '#1e293b' }}>
                Detailed Results
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {quizResults.results.map((result, idx) => (
                  <div key={idx} style={{
                    padding: '12px',
                    background: result.is_correct ? '#f0fdf4' : '#fef2f2',
                    borderRadius: '8px',
                    border: result.is_correct ? '1px solid #bbf7d0' : '1px solid #fecaca',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}>
                    <i className={`fas ${result.is_correct ? 'fa-check-circle' : 'fa-times-circle'}`} style={{
                      fontSize: '20px',
                      color: result.is_correct ? '#166534' : '#991b1b'
                    }}></i>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>
                        Question {idx + 1}
                      </div>
                      {result.explanation && (
                        <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                          {result.explanation}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
