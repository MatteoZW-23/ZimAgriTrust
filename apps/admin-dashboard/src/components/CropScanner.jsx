import React, { useState, useRef } from 'react';
import { analyzeCrop } from '../api';

export function CropScanner({ token }) {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef();

    const handleFileChange = (e) => {
        const selected = e.target.files[0];
        if (selected) {
            setFile(selected);
            setPreview(URL.createObjectURL(selected));
            setAnalysis(null);
        }
    };

    const runAI = async () => {
        if (!file) return;
        setLoading(true);
        
        try {
            const result = await analyzeCrop(token, file);
            setAnalysis(result);
        } catch (err) {
            console.error(err);
            alert("AI Inference Pipeline Failure: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="v4-glass-card-premium animate-fade-in" style={{ padding: '32px' }}>
            <div className="v4-card-header" style={{ marginBottom: '24px' }}>
                <div>
                    <h3 style={{ fontSize: '20px', fontWeight: 950 }}>Produce <span style={{ color: '#818cf8' }}>Deep Scan</span>.</h3>
                    <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', fontWeight: 600 }}>Sovereign Computer Vision (NumPy Matrix Core).</p>
                </div>
                {analysis && (
                    <div className="v4-badge-outline sm success" style={{ background: '#20963D10', borderColor: '#20963D33', color: '#20963D' }}>
                        <i className="fas fa-check-double"></i> ANALYSIS VERIFIED
                    </div>
                )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 0.8fr)', gap: '40px' }}>
                <div className="upload-zone" style={{ border: '2px dashed var(--v4-border)', borderRadius: '24px', position: 'relative', overflow: 'hidden', minHeight: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--v4-bg)' }}>
                    {preview ? (
                        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                            <img src={preview} alt="Crop" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            {analysis && (
                                <div className="vision-overlay" style={{ position: 'absolute', inset: 0, border: '4px solid #818cf8', opacity: 0.3, pointerEvents: 'none' }}>
                                    <div className="v-grid-line" style={{ position: 'absolute', top: '50%', width: '100%', height: '1.5px', background: '#818cf8aa' }}></div>
                                    <div className="v-grid-line" style={{ position: 'absolute', left: '50%', height: '100%', width: '1.5px', background: '#818cf8aa' }}></div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '40px' }}>
                            <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'var(--v4-surface)', display: 'grid', placeItems: 'center', margin: '0 auto 24px', border: '1.5px solid var(--v4-border)' }}>
                                <i className="fas fa-camera-viewfinder" style={{ fontSize: '32px', color: '#818cf8' }}></i>
                            </div>
                            <p style={{ fontWeight: 800, color: 'var(--v4-text-main)', marginBottom: '16px' }}>Zero-Trust Image Intake</p>
                            <button className="q-btn ghost small" onClick={() => fileInputRef.current.click()}>Select Field Image</button>
                        </div>
                    )}
                    <input type="file" ref={fileInputRef} onChange={handleFileChange} style={{ display: 'none' }} accept="image/*" />
                </div>

                <div className="analysis-zone">
                    {!analysis && !loading && (
                        <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--v4-text-dim)' }}>
                            <div className="proof-notice" style={{ background: 'var(--v4-bg)', padding: '24px', borderRadius: '20px', border: '1.5px solid var(--v4-border)', marginBottom: '24px' }}>
                                <div style={{ fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px', opacity: 0.6 }}>ENGINE PROTOCOL</div>
                                <strong style={{ color: 'var(--v4-text-main)', fontSize: '13px' }}>Deterministic 3x3 Convolution Sharpening</strong>
                                <p style={{ fontSize: '11px', marginTop: '8px' }}>Proving foundational matrix density checks on produce pixels.</p>
                            </div>
                            <button className="q-btn primary-btn full-w" style={{ background: '#818cf8', color: '#fff' }} onClick={runAI} disabled={!file}>Initiate Mathematical Scan</button>
                        </div>
                    )}

                    {loading && (
                        <div style={{ padding: '40px 0', textAlign: 'center' }}>
                            <div className="v4-cv-loader">
                                <div className="matrix-dot"></div>
                                <div className="matrix-dot"></div>
                                <div className="matrix-dot"></div>
                            </div>
                            <strong style={{ display: 'block', fontSize: '12px', letterSpacing: '0.2em', marginTop: '24px', color: '#818cf8' }}>CONVOLVING PIXEL MATRICES</strong>
                            <p style={{ fontSize: '11px', color: 'var(--v4-text-dim)', marginTop: '8px', fontWeight: 700 }}>Performing NumPy-backed Feature Extraction...</p>
                        </div>
                    )}

                    {analysis && (
                        <div className="animate-slide-up">
                            <div style={{ background: analysis.grade === 'GRADE_A' ? '#20963D08' : '#f59e0b08', padding: '24px', borderRadius: '24px', border: `2px solid ${analysis.grade === 'GRADE_A' ? '#20963D' : '#f59e0b'}`, position: 'relative', overflow: 'hidden' }}>
                                <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, opacity: 0.5, marginBottom: '4px', letterSpacing: '0.1em' }}>DERIVED GRADE</label>
                                <strong style={{ fontSize: '38px', color: analysis.grade === 'GRADE_A' ? '#20963D' : '#f59e0b', fontWeight: 1000 }}>{analysis.grade?.replace('_', ' ')}</strong>
                                <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '11px', fontWeight: 900 }}>Inference Confidence</span>
                                    <strong style={{ fontSize: '15px', color: '#818cf8' }}>{(analysis.confidence * 100).toFixed(1)}%</strong>
                                </div>
                            </div>

                            <div className="cv-proof-grid" style={{ marginTop: '24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                <div className="proof-card" style={{ padding: '16px', background: 'var(--v4-bg)', borderRadius: '16px', border: '1.5px solid var(--v4-border)' }}>
                                    <label style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5 }}>FEATURE DENSITY</label>
                                    <div style={{ fontSize: '14px', fontWeight: 950, color: 'var(--v4-text-main)', marginTop: '4px' }}>{analysis.cv_metrics?.feature_density.toFixed(4)}</div>
                                </div>
                                <div className="proof-card" style={{ padding: '16px', background: 'var(--v4-bg)', borderRadius: '16px', border: '1.5px solid var(--v4-border)' }}>
                                    <label style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5 }}>ENTROPY INDEX</label>
                                    <div style={{ fontSize: '14px', fontWeight: 950, color: 'var(--v4-text-main)', marginTop: '4px' }}>{analysis.cv_metrics?.entropy_index.toFixed(2)}</div>
                                </div>
                            </div>

                            <div className="anomalies-box" style={{ marginTop: '20px', padding: '16px', background: '#3b82f605', borderRadius: '16px', border: '1.5px solid #3b82f622' }}>
                                <label style={{ fontSize: '10px', fontWeight: 900, color: '#3b82f6', display: 'block', marginBottom: '8px' }}><i className="fas fa-microscope"></i> STRUCTURAL ANOMALIES</label>
                                {analysis.anomalies.map((a, i) => (
                                    <div key={i} style={{ fontSize: '11px', fontWeight: 700, color: 'var(--v4-text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#3b82f6' }}></div>
                                        {a}
                                    </div>
                                ))}
                            </div>

                            <button className="q-btn ghost full-w" style={{ marginTop: '24px' }} onClick={() => { setAnalysis(null); setFile(null); setPreview(null); }}>Clear Session</button>
                        </div>
                    )}
                </div>
            </div>

            <style>{`
                .matrix-dot { width: 10px; height: 10px; background: #818cf8; border-radius: 2px; animation: matrix-pulse 1s infinite alternate; }
                .v4-cv-loader { display: flex; gap: 8px; justify-content: center; }
                @keyframes matrix-pulse { 
                    0% { transform: scale(1); opacity: 0.2; }
                    100% { transform: scale(1.5); opacity: 1; }
                }
                .matrix-dot:nth-child(2) { animation-delay: 0.2s; }
                .matrix-dot:nth-child(3) { animation-delay: 0.4s; }
                .upload-zone:hover { border-color: #818cf8; background: #818cf805; }
                .vision-overlay { background: repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(129, 140, 248, 0.05) 10px, rgba(129, 140, 248, 0.05) 20px); }
            `}</style>
        </div>
    );
}
