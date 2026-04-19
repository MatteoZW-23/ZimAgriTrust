import React, { useState, useEffect } from 'react';
import { listApplications, certifyAgent, verifyDocumentation, verifyEquipment } from '../api';

export default function AgentRecruitmentPanel({ token }) {
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadApplications = async () => {
        try {
            const data = await listApplications(token);
            setApplications(data || []);
        } catch (err) {
            console.error("Recruitment Sync Failed", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadApplications();
    }, [token]);

    const handleAction = async (appId, action) => {
        try {
            if (action === 'DOCS') await verifyDocumentation(token, appId);
            if (action === 'GEAR') await verifyEquipment(token, appId);
            if (action === 'CERTIFY') await certifyAgent(token, appId);
            alert(`SUCCESS: Recruitment phase ${action} committed for ${appId.slice(0,8)}.`);
            loadApplications();
        } catch (err) {
            alert(`ACTION_FAILURE: ${err.message}`);
        }
    };

    if (loading) return <div className="p-40">Syncing Agent Recruitment Pipeline...</div>;

    return (
        <div className="v4-dashboard-container animate-fade-in compact-mode">
            <header className="v4-hero-professional theme-admin" style={{ background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)' }}>
                <div className="hero-content-v4">
                    <div className="kicker">
                        <span className="pill" style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc' }}>MANAGEMENT</span>
                        <div className="sync-pulse"><div className="p-dot" style={{ background: '#a5b4fc' }}></div>RECRUITMENT ACTIVE</div>
                    </div>
                    <h1>Agent <span>Recruitment</span>.</h1>
                    <p>Managing the next generation of AgriTrust Field Agents. Multi-phase verification and certification oversight.</p>
                </div>
                <div className="hero-visual">
                    <div className="v4-glass-card-mini">
                        <label>PIPELINE UNITS</label>
                        <strong>{applications.length} Applicants</strong>
                        <div className="v4-progress-bar">
                            <div style={{ width: `${(applications.filter(a => a.status === 'CERTIFIED').length / Math.max(1, applications.length)) * 100}%`, background: '#a5b4fc' }}></div>
                        </div>
                    </div>
                </div>
            </header>

            <div className="v4-main-panel">
                <div className="v4-glass-card-premium">
                    <div className="v4-card-header">
                        <h3>Applicant Overview</h3>
                        <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', marginTop: '4px', fontWeight: 600 }}>Manage applicant phase transitions across regional hubs.</p>
                    </div>

                    <div className="v4-table-shell" style={{ marginTop: '24px' }}>
                        <table className="v4-data-table">
                            <thead>
                                <tr>
                                    <th>CANDIDATE</th>
                                    <th>REGION</th>
                                    <th>CURRENT PHASE</th>
                                    <th>COMPLIANCE</th>
                                    <th>GOVERNANCE</th>
                                </tr>
                            </thead>
                            <tbody>
                                {applications.map(app => (
                                    <tr key={app.id}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                                <div className="u-av-small" style={{ background: '#e0e7ff', color: '#4338ca' }}>{app.full_name?.charAt(0)}</div>
                                                <div>
                                                    <strong style={{ display: 'block', fontSize: '14px' }}>{app.full_name}</strong>
                                                    <span style={{ fontSize: '11px', color: 'var(--v4-text-dim)' }}>{app.phone_number}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td><span className="v4-status-pill ghost" style={{ borderColor: 'var(--v4-border)' }}>{app.region || 'PENDING'}</span></td>
                                        <td>
                                            <div className="phase-indicator">
                                                <span className={`phase-tag ${app.status.toLowerCase()}`}>{app.status.replace('_', ' ')}</span>
                                                <div style={{ fontSize: '9px', fontWeight: 900, color: 'var(--v4-text-dim)', marginTop: '4px' }}>LEVEL {app.training_progress?.length || 0}/5</div>
                                            </div>
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '4px' }}>
                                                <div className={`check-dot ${app.documentation_verified ? 'ok' : 'pending'}`} title="Docs"></div>
                                                <div className={`check-dot ${app.equipment_verified ? 'ok' : 'pending'}`} title="Gear"></div>
                                                <div className={`check-dot ${app.shadowing_completed ? 'ok' : 'pending'}`} title="Shadow"></div>
                                            </div>
                                        </td>
                                        <td>
                                            <div className="v4-action-strip">
                                                {!app.documentation_verified && <button className="a-btn" onClick={() => handleAction(app.id, 'DOCS')} title="Verify Docs"><i className="fas fa-file-signature"></i></button>}
                                                {app.documentation_verified && !app.equipment_verified && <button className="a-btn" onClick={() => handleAction(app.id, 'GEAR')} title="Issue Equipment"><i className="fas fa-microchip"></i></button>}
                                                {app.status === 'READY_FOR_CERTIFICATION' && (
                                                    <button className="q-btn primary-btn small" onClick={() => handleAction(app.id, 'CERTIFY')} style={{ background: '#4338ca', color: '#fff' }}>
                                                        CERTIFY AGENT
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {!applications.length && <div className="p-40 text-center opacity-50">No active applications in the recruitment pipeline.</div>}
                    </div>
                </div>
            </div>

            <style>{`
                .phase-tag { padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 1000; text-transform: uppercase; background: var(--v4-surface); border: 1.5px solid var(--v4-border); }
                .phase-tag.applied { color: #3b82f6; }
                .phase-tag.certified { background: #dcfce7; color: #16a34a; border-color: #16a34a33; }
                .check-dot { width: 8px; height: 8px; border-radius: 50%; background: #e2e8f0; }
                .check-dot.ok { background: #16a34a; box-shadow: 0 0 6px #16a34a88; }
                .check-dot.pending { background: #f59e0b; }
            `}</style>
        </div>
    );
}
