import React, { useState, useEffect } from 'react';
import { fetchModelStatuses, triggerModelTraining } from '../api';

// ── Model registry ─────────────────────────────────────────────────────────────
const MODELS = [
  {
    id: 'disease',
    name: 'Crop Disease Detector',
    description: 'YOLOv8-cls — 14 disease classes across Corn, Potato, Rice & Wheat.',
    icon: 'fa-virus',
    color: '#ef4444',
    endpoint: '/ai/train/disease',
    weightsFile: 'ml_weights/disease_classifier.pt',
    dataSource: 'data/training/disease/dataset',
    category: 'Vision',
    metrics: ['Top-1 Accuracy', 'Top-5 Accuracy'],
  },
  {
    id: 'vision',
    name: 'Crop Classifier',
    description: 'YOLOv8-cls — identifies crop type, grade and health from images.',
    icon: 'fa-seedling',
    color: '#22c55e',
    endpoint: '/ai/train/vision',
    weightsFile: 'ml_weights/crop_classifier.pt',
    dataSource: 'data/training/data/kaggle_crops',
    category: 'Vision',
    metrics: ['Top-1 Accuracy', 'Precision'],
  },
  {
    id: 'price',
    name: 'Price Forecaster',
    description: 'Hybrid ARIMA-LSTM — predicts commodity prices from market dynamics.',
    icon: 'fa-chart-line',
    color: '#3b82f6',
    endpoint: '/ai/train/price',
    weightsFile: 'ml_weights/deep_price_engine.pkl',
    dataSource: 'Live DB — listings & transactions',
    category: 'Forecasting',
    metrics: ['MAPE', 'R²'],
  },
  {
    id: 'demand',
    name: 'Demand Forecaster',
    description: 'Random Forest — predicts regional crop demand over 30-day windows.',
    icon: 'fa-arrow-trend-up',
    color: '#f59e0b',
    endpoint: '/ai/train/demand',
    weightsFile: 'ml_weights/demand_forecaster_v4.pkl',
    dataSource: 'Live DB — completed orders',
    category: 'Forecasting',
    metrics: ['MAPE', 'Ensemble Score'],
  },
  {
    id: 'risk',
    name: 'Risk Scorer',
    description: 'Isolation Forest + RF — detects fraud and scores user trust.',
    icon: 'fa-shield-halved',
    color: '#8b5cf6',
    endpoint: '/ai/train/risk',
    weightsFile: 'ml_weights/risk_scorer_v4.pkl',
    dataSource: 'Live DB — user behaviour logs',
    category: 'Security',
    metrics: ['Precision', 'Recall', 'F1'],
  },
  {
    id: 'fraud',
    name: 'Fraud Detector',
    description: 'Isolation Forest — flags anomalous transactions in real-time.',
    icon: 'fa-triangle-exclamation',
    color: '#f97316',
    endpoint: '/ai/train/fraud',
    weightsFile: 'ml_weights/fraud_model_v1.pkl',
    dataSource: 'Live DB — transaction features',
    category: 'Security',
    metrics: ['Anomaly Score', 'Contamination Rate'],
  },
  {
    id: 'calibrate',
    name: 'Full System Calibration',
    description: 'Runs price + risk + demand calibration in one pass from live DB data.',
    icon: 'fa-gears',
    color: '#06b6d4',
    endpoint: '/ai/train/calibrate',
    weightsFile: 'ml_weights/last_train_date.txt',
    dataSource: 'Live DB — all tables',
    category: 'System',
    metrics: ['Price RMSE', 'Risk F1', 'Demand MAPE'],
  },
];

const CATEGORY_COLORS = {
  Vision:      '#818cf8',
  Forecasting: '#f59e0b',
  Security:    '#ef4444',
  System:      '#06b6d4',
};

// ── Component ──────────────────────────────────────────────────────────────────
export default function AIModelPanel({ token }) {
  const [jobs, setJobs]         = useState({});   // { modelId: { status, message, startedAt } }
  const [statuses, setStatuses] = useState({});   // { modelId: { exists, lastTrained } }
  const [activeTab, setActiveTab] = useState('All');

  // Poll model weight file existence via a lightweight status endpoint
  useEffect(() => {
    fetchStatuses();
  }, []);

  const fetchStatuses = async () => {
    try {
      const data = await fetchModelStatuses(token);
      setStatuses(data || {});
    } catch {
      // endpoint may not exist yet — silently ignore
    }
  };

  const handleTrain = async (model) => {
    setJobs(prev => ({
      ...prev,
      [model.id]: { status: 'launching', message: 'Launching training job…', startedAt: new Date() },
    }));
    try {
      const res = await triggerModelTraining(token, model.id);
      setJobs(prev => ({
        ...prev,
        [model.id]: {
          status: res.status || 'started',
          message: res.message || 'Training started in background.',
          startedAt: new Date(),
        },
      }));
    } catch (err) {
      setJobs(prev => ({
        ...prev,
        [model.id]: { status: 'error', message: err.message, startedAt: new Date() },
      }));
    }
  };

  const categories = ['All', ...new Set(MODELS.map(m => m.category))];
  const visible = activeTab === 'All' ? MODELS : MODELS.filter(m => m.category === activeTab);

  const getJobColor = (status) => {
    if (!status) return null;
    if (status === 'error') return '#ef4444';
    if (status === 'training_started' || status === 'started') return '#22c55e';
    if (status === 'launching') return '#f59e0b';
    return '#3b82f6';
  };

  return (
    <div className="v4-dashboard-container animate-fade-in">

      {/* HERO */}
      <header style={{
        background: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
        borderRadius: '32px', padding: '48px', color: '#fff',
        display: 'grid', gridTemplateColumns: '1fr auto', gap: '40px', alignItems: 'center',
      }}>
        <div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
            <span style={{ background: 'rgba(129,140,248,0.2)', color: '#818cf8', fontSize: '10px', fontWeight: 900, padding: '4px 14px', borderRadius: '6px', letterSpacing: '0.1em' }}>AI OPERATIONS CENTER</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', fontWeight: 900, opacity: 0.6 }}>
              <div style={{ width: '6px', height: '6px', background: '#22c55e', borderRadius: '50%', boxShadow: '0 0 8px #22c55e' }}></div>
              {MODELS.length} MODELS REGISTERED
            </div>
          </div>
          <h1 style={{ fontSize: '42px', fontWeight: 950, margin: '0 0 12px', letterSpacing: '-0.04em' }}>
            Sovereign <span style={{ color: '#818cf8' }}>AI Engine</span>.
          </h1>
          <p style={{ fontSize: '15px', opacity: 0.7, maxWidth: '560px', lineHeight: 1.7, fontWeight: 600, margin: 0 }}>
            Train, calibrate and monitor every machine learning model powering the ZimAgritrust platform — from crop disease detection to fraud prevention.
          </p>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: '24px', padding: '32px', minWidth: '200px', textAlign: 'center' }}>
          <div style={{ fontSize: '10px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '8px' }}>ACTIVE JOBS</div>
          <div style={{ fontSize: '48px', fontWeight: 950, color: '#818cf8' }}>
            {Object.values(jobs).filter(j => j.status === 'training_started' || j.status === 'launching').length}
          </div>
          <div style={{ fontSize: '11px', opacity: 0.5, fontWeight: 700, marginTop: '4px' }}>running in background</div>
        </div>
      </header>

      {/* CATEGORY TABS */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {categories.map(cat => (
          <button key={cat} onClick={() => setActiveTab(cat)} style={{
            padding: '10px 24px', borderRadius: '12px', border: 'none', cursor: 'pointer',
            fontWeight: 900, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em',
            background: activeTab === cat ? (CATEGORY_COLORS[cat] || '#818cf8') : 'var(--v4-surface)',
            color: activeTab === cat ? '#fff' : 'var(--v4-text-dim)',
            transition: '0.2s',
          }}>
            {cat}
          </button>
        ))}
        <button onClick={fetchStatuses} style={{
          marginLeft: 'auto', padding: '10px 20px', borderRadius: '12px', border: '1.5px solid var(--v4-border)',
          background: 'transparent', cursor: 'pointer', fontWeight: 900, fontSize: '11px', color: 'var(--v4-text-dim)',
        }}>
          <i className="fas fa-sync" style={{ marginRight: '6px' }}></i>Refresh Status
        </button>
      </div>

      {/* MODEL CARDS GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '24px' }}>
        {visible.map(model => {
          const job    = jobs[model.id];
          const status = statuses[model.id];
          const jobColor = getJobColor(job?.status);

          return (
            <div key={model.id} style={{
              background: 'var(--v4-surface)', borderRadius: '28px',
              border: `1.5px solid ${job ? jobColor + '44' : 'var(--v4-border)'}`,
              padding: '32px', display: 'flex', flexDirection: 'column', gap: '20px',
              transition: '0.2s', position: 'relative', overflow: 'hidden',
            }}>
              {/* Glow accent */}
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
                background: model.color, borderRadius: '28px 28px 0 0',
              }} />

              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{
                    width: '52px', height: '52px', borderRadius: '16px',
                    background: model.color + '15', display: 'grid', placeItems: 'center',
                    border: `1.5px solid ${model.color}33`,
                  }}>
                    <i className={`fas ${model.icon}`} style={{ fontSize: '22px', color: model.color }}></i>
                  </div>
                  <div>
                    <strong style={{ fontSize: '16px', fontWeight: 950, display: 'block' }}>{model.name}</strong>
                    <span style={{
                      fontSize: '9px', fontWeight: 900, padding: '2px 8px', borderRadius: '4px',
                      background: (CATEGORY_COLORS[model.category] || '#818cf8') + '20',
                      color: CATEGORY_COLORS[model.category] || '#818cf8',
                      letterSpacing: '0.08em',
                    }}>{model.category}</span>
                  </div>
                </div>

                {/* Weight file status indicator */}
                <div style={{ textAlign: 'right' }}>
                  {status?.exists ? (
                    <span style={{ fontSize: '10px', fontWeight: 900, color: '#22c55e', display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 6px #22c55e' }}></div>
                      WEIGHTS LOADED
                    </span>
                  ) : (
                    <span style={{ fontSize: '10px', fontWeight: 900, color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f59e0b' }}></div>
                      NOT TRAINED
                    </span>
                  )}
                  {status?.lastTrained && (
                    <div style={{ fontSize: '9px', color: 'var(--v4-text-dim)', fontWeight: 700, marginTop: '4px' }}>
                      Last: {status.lastTrained}
                    </div>
                  )}
                </div>
              </div>

              {/* Description */}
              <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', fontWeight: 600, margin: 0, lineHeight: 1.6 }}>
                {model.description}
              </p>

              {/* Data source */}
              <div style={{ padding: '12px 16px', background: 'var(--v4-bg)', borderRadius: '12px', border: '1px solid var(--v4-border)' }}>
                <div style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '4px' }}>DATA SOURCE</div>
                <div style={{ fontSize: '11px', fontWeight: 800, fontFamily: 'monospace', color: 'var(--v4-text-main)', wordBreak: 'break-all' }}>
                  {model.dataSource}
                </div>
              </div>

              {/* Metrics tags */}
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {model.metrics.map(m => (
                  <span key={m} style={{
                    fontSize: '10px', fontWeight: 900, padding: '4px 10px', borderRadius: '6px',
                    background: 'var(--v4-bg)', border: '1px solid var(--v4-border)', color: 'var(--v4-text-dim)',
                  }}>{m}</span>
                ))}
              </div>

              {/* Job status message */}
              {job && (
                <div style={{
                  padding: '12px 16px', borderRadius: '12px', fontSize: '12px', fontWeight: 700,
                  background: jobColor + '15', border: `1px solid ${jobColor}33`, color: jobColor,
                  display: 'flex', alignItems: 'center', gap: '8px',
                }}>
                  {(job.status === 'launching' || job.status === 'training_started') && (
                    <i className="fas fa-circle-notch fa-spin"></i>
                  )}
                  {job.status === 'error' && <i className="fas fa-triangle-exclamation"></i>}
                  {job.status !== 'launching' && job.status !== 'training_started' && job.status !== 'error' && (
                    <i className="fas fa-check-circle"></i>
                  )}
                  <span style={{ flex: 1 }}>{job.message}</span>
                  {job.startedAt && (
                    <span style={{ fontSize: '10px', opacity: 0.7 }}>
                      {job.startedAt.toLocaleTimeString()}
                    </span>
                  )}
                </div>
              )}

              {/* Train button */}
              <button
                onClick={() => handleTrain(model)}
                disabled={job?.status === 'launching'}
                style={{
                  padding: '16px', borderRadius: '16px', border: 'none', cursor: job?.status === 'launching' ? 'not-allowed' : 'pointer',
                  background: job?.status === 'launching' ? 'var(--v4-border)' : model.color,
                  color: '#fff', fontWeight: 950, fontSize: '13px', letterSpacing: '0.05em',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                  transition: '0.2s', opacity: job?.status === 'launching' ? 0.6 : 1,
                  boxShadow: job?.status === 'launching' ? 'none' : `0 8px 24px ${model.color}40`,
                }}
              >
                {job?.status === 'launching' ? (
                  <><i className="fas fa-circle-notch fa-spin"></i> LAUNCHING…</>
                ) : (
                  <><i className="fas fa-brain"></i> TRAIN MODEL</>
                )}
              </button>
            </div>
          );
        })}
      </div>

      {/* TRAINING LOG */}
      {Object.keys(jobs).length > 0 && (
        <div className="v4-glass-card-premium">
          <div className="v4-card-header">
            <div>
              <h3>Training Log</h3>
              <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0', fontWeight: 600 }}>
                All training jobs dispatched this session.
              </p>
            </div>
            <button onClick={() => setJobs({})} style={{ fontSize: '11px', fontWeight: 900, padding: '6px 14px', borderRadius: '8px', border: '1.5px solid var(--v4-border)', background: 'transparent', cursor: 'pointer', color: 'var(--v4-text-dim)' }}>
              Clear Log
            </button>
          </div>
          <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {Object.entries(jobs).map(([id, job]) => {
              const model = MODELS.find(m => m.id === id);
              const color = getJobColor(job.status);
              return (
                <div key={id} style={{
                  display: 'flex', alignItems: 'center', gap: '16px',
                  padding: '16px 20px', borderRadius: '14px',
                  background: 'var(--v4-bg)', border: `1.5px solid ${color}33`,
                }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: (model?.color || '#818cf8') + '20', display: 'grid', placeItems: 'center' }}>
                    <i className={`fas ${model?.icon || 'fa-brain'}`} style={{ color: model?.color || '#818cf8', fontSize: '16px' }}></i>
                  </div>
                  <div style={{ flex: 1 }}>
                    <strong style={{ fontSize: '13px', fontWeight: 950 }}>{model?.name || id}</strong>
                    <div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700, marginTop: '2px' }}>{job.message}</div>
                  </div>
                  <span style={{ fontSize: '10px', fontWeight: 900, padding: '4px 10px', borderRadius: '6px', background: color + '20', color }}>
                    {job.status.toUpperCase().replace('_', ' ')}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>
                    {job.startedAt?.toLocaleTimeString()}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <style>{`
        .v4-dashboard-container { display: flex; flex-direction: column; gap: 40px; padding-bottom: 80px; }
      `}</style>
    </div>
  );
}
