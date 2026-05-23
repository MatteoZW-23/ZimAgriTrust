import React, { useState, useRef } from 'react';
import { analyzeCrop, detectDisease, trainDiseaseModel } from '../api';

export function CropScanner({ token }) {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [analysis, setAnalysis] = useState(null);
    const [diseaseResult, setDiseaseResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [mode, setMode] = useState('classify'); // 'classify' | 'disease'
    const [trainingMsg, setTrainingMsg] = useState('');
    const fileInputRef = useRef();

    const handleFileChange = (e) => {
        const selected = e.target.files[0];
        if (selected) {
            setFile(selected);
            setPreview(URL.createObjectURL(selected));
            setAnalysis(null);
            setDiseaseResult(null);
        }
    };

    const runAI = async () => {
        if (!file) return;
        setLoading(true);
        try {
            if (mode === 'classify') {
                const result = await analyzeCrop(token, file);
                if (!result || result.success === false) {
                    alert('Analysis failed: ' + (result?.error || 'Could not identify the crop.'));
                    return;
                }
                setAnalysis(result);
            } else {
                const result = await detectDisease(token, file);
                setDiseaseResult(result);
            }
        } catch (err) {
            alert((mode === 'classify' ? 'Vision' : 'Disease') + ' analysis failed: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleTrainModel = async () => {
        setTrainingMsg('Launching training job...');
        try {
            const res = await trainDiseaseModel(token);
            setTrainingMsg(res.message || 'Training started in background.');
        } catch (err) {
            setTrainingMsg('Error: ' + err.message);
        }
    };

    const SEVERITY_COLORS = {
        None:     '#16a34a',
        Moderate: '#f59e0b',
        High:     '#ef4444',
        Critical: '#7f1d1d',
        Unknown:  '#94a3b8',
    };

    return (
        <div className="v4-glass-card-premium animate-fade-in" style={{ padding: '32px' }}>
            <div className="v4-card-header" style={{ marginBottom: '24px' }}>
                <div>
                    <h3 style={{ fontSize: '20px', fontWeight: 950 }}>Produce <span style={{ color: '#818cf8' }}>Deep Scan</span>.</h3>
                    <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', fontWeight: 600 }}>YOLOv8 Crop Classification + Disease Detection.</p>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    {(analysis || diseaseResult) && (
                        <div className="v4-badge-outline sm success" style={{ background: '#20963D10', borderColor: '#20963D33', color: '#20963D' }}>
                            <i className="fas fa-check-double"></i> VERIFIED
                        </div>
                    )}
                    <button
                        onClick={handleTrainModel}
                        style={{ fontSize: '10px', fontWeight: 900, padding: '6px 14px', borderRadius: '8px', border: '1.5px solid #818cf8', background: 'transparent', color: '#818cf8', cursor: 'pointer' }}
                        title="Train disease model on local dataset"
                    >
                        <i className="fas fa-brain" style={{ marginRight: '6px' }}></i>TRAIN MODEL
                    </button>
                </div>
            </div>

            {trainingMsg && (
                <div style={{ marginBottom: '16px', padding: '12px 16px', borderRadius: '12px', background: '#818cf810', border: '1px solid #818cf833', fontSize: '12px', fontWeight: 700, color: '#818cf8' }}>
                    <i className="fas fa-circle-notch fa-spin" style={{ marginRight: '8px' }}></i>{trainingMsg}
                </div>
            )}

            {/* Mode tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
                {[
                    { id: 'classify', label: 'Crop Classifier', icon: 'fa-seedling' },
                    { id: 'disease',  label: 'Disease Detector', icon: 'fa-virus' },
                ].map(tab => (
                    <button key={tab.id} onClick={() => { setMode(tab.id); setAnalysis(null); setDiseaseResult(null); }} style={{
                        padding: '8px 20px', borderRadius: '10px', border: 'none', cursor: 'pointer', fontWeight: 900, fontSize: '12px',
                        background: mode === tab.id ? '#818cf8' : 'var(--v4-surface)',
                        color: mode === tab.id ? '#fff' : 'var(--v4-text-dim)',
                    }}>
                        <i className={`fas ${tab.icon}`} style={{ marginRight: '8px' }}></i>{tab.label}
                    </button>
                ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 0.8fr)', gap: '40px' }}>
                {/* Upload zone */}
                <div className="upload-zone" style={{ border: '2px dashed var(--v4-border)', borderRadius: '24px', position: 'relative', overflow: 'hidden', minHeight: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--v4-bg)' }}>
                    {preview ? (
                        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                            <img src={preview} alt="Crop" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            {(analysis || diseaseResult) && (
                                <div className="vision-overlay" style={{ position: 'absolute', inset: 0, border: '4px solid #818cf8', opacity: 0.3, pointerEvents: 'none' }}>
                                    <div style={{ position: 'absolute', top: '50%', width: '100%', height: '1.5px', background: '#818cf8aa' }}></div>
                                    <div style={{ position: 'absolute', left: '50%', height: '100%', width: '1.5px', background: '#818cf8aa' }}></div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '40px' }}>
                            <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'var(--v4-surface)', display: 'grid', placeItems: 'center', margin: '0 auto 24px', border: '1.5px solid var(--v4-border)' }}>
                                <i className={`fas ${mode === 'disease' ? 'fa-virus' : 'fa-camera-viewfinder'}`} style={{ fontSize: '32px', color: '#818cf8' }}></i>
                            </div>
                            <p style={{ fontWeight: 800, color: 'var(--v4-text-main)', marginBottom: '16px' }}>
                                {mode === 'disease' ? 'Upload a leaf / crop image' : 'Zero-Trust Image Intake'}
                            </p>
                            <button className="q-btn ghost small" onClick={() => fileInputRef.current.click()}>Select Field Image</button>
                        </div>
                    )}
                    <input type="file" ref={fileInputRef} onChange={handleFileChange} style={{ display: 'none' }} accept="image/*" />
                </div>

                {/* Results zone */}
                <div className="analysis-zone">
                    {!analysis && !diseaseResult && !loading && (
                        <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--v4-text-dim)' }}>
                            <div style={{ background: 'var(--v4-bg)', padding: '24px', borderRadius: '20px', border: '1.5px solid var(--v4-border)', marginBottom: '24px' }}>
                                <div style={{ fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px', opacity: 0.6 }}>
                                    {mode === 'disease' ? 'DISEASE MODEL' : 'ENGINE PROTOCOL'}
                                </div>
                                <strong style={{ color: 'var(--v4-text-main)', fontSize: '13px' }}>
                                    {mode === 'disease' ? 'YOLOv8-cls — 14 Disease Classes' : 'YOLOv8 Crop Classification'}
                                </strong>
                                <p style={{ fontSize: '11px', marginTop: '8px' }}>
                                    {mode === 'disease'
                                        ? 'Corn, Potato, Rice, Wheat — rust, blight, blast & more.'
                                        : 'Classifies crop type, grade, and health status.'}
                                </p>
                            </div>
                            <button className="q-btn primary-btn full-w" style={{ background: '#818cf8', color: '#fff' }} onClick={runAI} disabled={!file}>
                                {mode === 'disease' ? 'Detect Disease' : 'Initiate Scan'}
                            </button>
                        </div>
                    )}

                    {loading && (
                        <div style={{ padding: '40px 0', textAlign: 'center' }}>
                            <div className="v4-cv-loader">
                                <div className="matrix-dot"></div>
                                <div className="matrix-dot"></div>
                                <div className="matrix-dot"></div>
                            </div>
                            <strong style={{ display: 'block', fontSize: '12px', letterSpacing: '0.2em', marginTop: '24px', color: '#818cf8' }}>
                                {mode === 'disease' ? 'SCANNING FOR PATHOGENS' : 'CONVOLVING PIXEL MATRICES'}
                            </strong>
                        </div>
                    )}

                    {/* Crop classification result */}
                    {analysis && mode === 'classify' && (
                        <div className="animate-slide-up">
                            <div style={{ background: analysis.grade?.grade === 'Grade A' ? '#20963D08' : '#f59e0b08', padding: '24px', borderRadius: '24px', border: `2px solid ${analysis.grade?.grade === 'Grade A' ? '#20963D' : '#f59e0b'}` }}>
                                <label style={{ display: 'block', fontSize: '9px', fontWeight: 900, opacity: 0.5, marginBottom: '4px', letterSpacing: '0.1em' }}>DETECTED CROP</label>
                                <strong style={{ fontSize: '28px', color: 'var(--v4-text-main)', fontWeight: 1000 }}>{analysis.crop?.name || analysis.crop?.type || 'Unknown'}</strong>
                                <div style={{ marginTop: '8px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                                    <span style={{ fontSize: '13px', fontWeight: 900, color: '#20963D', background: '#20963D10', padding: '4px 12px', borderRadius: 100 }}>{analysis.grade?.grade || 'Standard'}</span>
                                    <span style={{ fontSize: '12px', fontWeight: 700, color: '#818cf8' }}>Confidence: {((analysis.crop?.confidence ?? 0) * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                            <div style={{ marginTop: '16px', padding: '16px', background: 'var(--v4-bg)', borderRadius: '16px', border: '1.5px solid var(--v4-border)' }}>
                                <label style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5, display: 'block', marginBottom: '6px' }}>HEALTH STATUS</label>
                                <div style={{ fontSize: '13px', fontWeight: 800 }}>{analysis.health?.status || 'Unknown'}</div>
                            </div>
                            {analysis.recommendations?.length > 0 && (
                                <div style={{ marginTop: '16px', padding: '16px', background: '#3b82f605', borderRadius: '16px', border: '1.5px solid #3b82f622' }}>
                                    <label style={{ fontSize: '10px', fontWeight: 900, color: '#3b82f6', display: 'block', marginBottom: '8px' }}><i className="fas fa-lightbulb"></i> RECOMMENDATIONS</label>
                                    {analysis.recommendations.map((r, i) => (
                                        <div key={i} style={{ fontSize: '11px', fontWeight: 700, display: 'flex', gap: '6px', marginBottom: '4px' }}>
                                            <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#3b82f6', marginTop: '5px', flexShrink: 0 }}></div>{r}
                                        </div>
                                    ))}
                                </div>
                            )}
                            <button className="q-btn ghost full-w" style={{ marginTop: '20px' }} onClick={() => { setAnalysis(null); setFile(null); setPreview(null); }}>Clear Session</button>
                        </div>
                    )}

                    {/* Disease detection result */}
                    {diseaseResult && mode === 'disease' && (
                        <div className="animate-slide-up">
                            <div style={{
                                padding: '24px', borderRadius: '24px',
                                border: `2px solid ${SEVERITY_COLORS[diseaseResult.severity] || '#94a3b8'}`,
                                background: `${SEVERITY_COLORS[diseaseResult.severity] || '#94a3b8'}08`,
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                    <label style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em' }}>
                                        {diseaseResult.disease_detected ? 'DISEASE DETECTED' : 'CROP STATUS'}
                                    </label>
                                    <span style={{
                                        padding: '4px 12px', borderRadius: '100px', fontSize: '10px', fontWeight: 950,
                                        background: SEVERITY_COLORS[diseaseResult.severity] || '#94a3b8',
                                        color: '#fff',
                                    }}>{diseaseResult.severity || 'Unknown'}</span>
                                </div>
                                <strong style={{ fontSize: '22px', fontWeight: 1000, display: 'block', marginBottom: '4px' }}>
                                    {diseaseResult.disease_name || 'Unknown'}
                                </strong>
                                <div style={{ fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>
                                    Crop: {diseaseResult.crop} &nbsp;•&nbsp; Confidence: {((diseaseResult.confidence || 0) * 100).toFixed(1)}%
                                </div>
                            </div>

                            {diseaseResult.description && (
                                <div style={{ marginTop: '12px', padding: '14px 16px', background: 'var(--v4-bg)', borderRadius: '14px', border: '1.5px solid var(--v4-border)', fontSize: '12px', fontWeight: 600, color: 'var(--v4-text-dim)', lineHeight: 1.6 }}>
                                    {diseaseResult.description}
                                </div>
                            )}

                            {diseaseResult.disease_detected && (
                                <>
                                    <div style={{ marginTop: '12px', padding: '14px 16px', background: '#fee2e210', borderRadius: '14px', border: '1.5px solid #ef444433' }}>
                                        <label style={{ fontSize: '9px', fontWeight: 900, color: '#ef4444', display: 'block', marginBottom: '6px' }}>TREATMENT</label>
                                        <div style={{ fontSize: '12px', fontWeight: 700 }}>{diseaseResult.treatment}</div>
                                    </div>
                                    <div style={{ marginTop: '12px', padding: '14px 16px', background: '#dcfce710', borderRadius: '14px', border: '1.5px solid #16a34a33' }}>
                                        <label style={{ fontSize: '9px', fontWeight: 900, color: '#16a34a', display: 'block', marginBottom: '6px' }}>PREVENTION</label>
                                        <div style={{ fontSize: '12px', fontWeight: 700 }}>{diseaseResult.prevention}</div>
                                    </div>
                                </>
                            )}

                            {diseaseResult.top_predictions?.length > 0 && (
                                <div style={{ marginTop: '12px', padding: '14px 16px', background: 'var(--v4-bg)', borderRadius: '14px', border: '1.5px solid var(--v4-border)' }}>
                                    <label style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5, display: 'block', marginBottom: '8px' }}>TOP PREDICTIONS</label>
                                    {diseaseResult.top_predictions.map((p, i) => (
                                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 800, marginBottom: '6px' }}>
                                            <span>{p.display || p.class}</span>
                                            <span style={{ color: '#818cf8' }}>{(p.confidence * 100).toFixed(1)}%</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {diseaseResult.requires_agent_review && (
                                <div style={{ marginTop: '12px', padding: '10px 14px', background: '#fef3c7', borderRadius: '10px', fontSize: '11px', fontWeight: 800, color: '#92400e' }}>
                                    <i className="fas fa-triangle-exclamation" style={{ marginRight: '6px' }}></i>
                                    Low confidence — agent field review recommended.
                                </div>
                            )}

                            <div style={{ marginTop: '8px', fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 600 }}>
                                Model: {diseaseResult.model}
                            </div>

                            <button className="q-btn ghost full-w" style={{ marginTop: '16px' }} onClick={() => { setDiseaseResult(null); setFile(null); setPreview(null); }}>Clear Session</button>
                        </div>
                    )}
                </div>
            </div>

            <style>{`
                .matrix-dot { width: 10px; height: 10px; background: #818cf8; border-radius: 2px; animation: matrix-pulse 1s infinite alternate; }
                .v4-cv-loader { display: flex; gap: 8px; justify-content: center; }
                @keyframes matrix-pulse { 0% { transform: scale(1); opacity: 0.2; } 100% { transform: scale(1.5); opacity: 1; } }
                .matrix-dot:nth-child(2) { animation-delay: 0.2s; }
                .matrix-dot:nth-child(3) { animation-delay: 0.4s; }
                .upload-zone:hover { border-color: #818cf8; background: #818cf805; }
                .vision-overlay { background: repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(129,140,248,0.05) 10px, rgba(129,140,248,0.05) 20px); }
            `}</style>
        </div>
    );
}
