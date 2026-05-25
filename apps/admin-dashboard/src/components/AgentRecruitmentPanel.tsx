import React, { useState, useEffect } from 'react';
import { listApplications, certifyAgent, verifyDocumentation, verifyEquipment, completeShadowing, submitApplication, request } from '../api';

export default function AgentRecruitmentPanel({ token }) {
 const [applications, setApplications] = useState([]);
 const [loading, setLoading] = useState(true);
 const [selectedApp, setSelectedApp] = useState(null);

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

 const handleAction = async (appId, action, extra = {}) => {
 try {
 if (action === 'DOCS') await verifyDocumentation(token, appId);
 if (action === 'GEAR') await verifyEquipment(token, appId);
 if (action === 'SHADOW') {
 const rating = prompt("Enter Shadowing Rating (1-5):", "5");
 if (rating) {
 // Use a valid supervisor ID (fallback to a likely admin ID if token decoding isn't available)
 const supervisorId = "00000000-0000-0000-0000-000000000000"; 
 await completeShadowing(token, appId, supervisorId, parseFloat(rating));
 }
 else return;
 }
 if (action === 'PRACTICAL') {
 const score = prompt("Enter Practical Assessment Score (0-100):", "95");
 if (!score) return;
 // Transition to next phase
 await request(`/recruitment/${appId}/practical?score=${score}`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
 }
 if (action === 'CERTIFY') {
 const res = await certifyAgent(token, appId);
 alert(`SUCCESS: Agent Certified! Account Created.\nTemporary PIN: ${res.temp_pin}\nAgent Code: ${res.agent_code}`);
 }
 if (action !== 'CERTIFY') alert(`SUCCESS: Phase ${action} updated.`);
 loadApplications();
 } catch (err) {
 alert(`ACTION_FAILURE: ${err.message}`);
 }
 };

 const getStatusWeight = (status) => {
 const weights = {
 'APPLIED': 1,
 'DOCS_VERIFIED': 2,
 'TRAINING_PHASE_1': 3,
 'TRAINING_PHASE_2': 4,
 'READY_FOR_EXAM': 5,
 'EXAM_PASSED': 6,
 'READY_FOR_PRACTICAL': 7,
 'READY_FOR_SHADOWING': 8,
 'SUPERVISED_INDEPENDENT': 9,
 'READY_FOR_CERTIFICATION': 10,
 'CERTIFIED': 11
 };
 return weights[status] || 0;
 };

 const openDocument = (doc) => {
 if (!doc?.data_url) return alert("Document file was not uploaded with this application.");
 const win = window.open();
 if (win) {
 win.document.write(`<iframe src="${doc.data_url}" style="width:100%;height:100%;border:0"></iframe>`);
 win.document.title = doc.name || "Application Document";
 }
 };

 if (loading) return (
 <div className="v4-loading-shimmer-full"><div className="shimmer-line heading"></div><div className="shimmer-line text"></div><div className="shimmer-grid"></div></div>);

 return (
 <div className="v4-recruitment-pipeline animate-fade-in"><header className="recruitment-hero-v4"><div className="hero-left"><div className="kicker"><i className="fas fa-users-gear"></i><span>RECRUITMENT PIPELINE ACTIVE</span></div><h1>Agent <span>Onboarding</span> Center.</h1><p>Qualifying, equipping, and certifying regional agents for the ZimAgritrust ecosystem. <strong>{applications.length}</strong> candidates in progress.</p><div className="hero-actions" style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>{/* Interactive operational controls will appear during live recruitment drives. */}
 </div></div><div className="hero-stats"><div className="stat-pill"><label>TOTAL APPLICATIONS</label><strong>{applications.length}</strong></div><div className="stat-pill"><label>READY FOR CERT</label><strong>{applications.filter(a => a.status === 'READY_FOR_CERTIFICATION').length}</strong></div></div></header>
<div className="v4-pipeline-grid">{applications.map(app => (
 <div key={app.id} className={`v4-applicant-card ${app.status === 'CERTIFIED' ? 'archived' : ''}`}><div className="card-top"><div className="candidate-info"><div className="c-av" style={{ background: 'var(--v4-primary-gradient)' }}>{app.full_name?.charAt(0)}</div><div className="c-meta"><strong>{app.full_name}</strong><span>{app.phone_number} // {app.province}</span></div></div><div className={`status-tag ${app.status?.toLowerCase()}`}>{app.status?.replace(/_/g, ' ')}</div></div>
<div className="pipeline-stepper" style={{ gap: '4px' }}>{[
 { id: 'APPLIED', icon: 'fa-id-card', label: 'Apply' },
 { id: 'DOCS_VERIFIED', icon: 'fa-file-shield', label: 'Docs' },
 { id: 'TRAINING_PHASE_1', icon: 'fa-book', label: 'Base' },
 { id: 'TRAINING_PHASE_2', icon: 'fa-book-open', label: 'Adv' },
 { id: 'READY_FOR_EXAM', icon: 'fa-graduation-cap', label: 'Exam' },
 { id: 'READY_FOR_PRACTICAL', icon: 'fa-flask', label: 'Lab' },
 { id: 'READY_FOR_SHADOWING', icon: 'fa-user-ninja', label: 'Shadow' },
 { id: 'SUPERVISED_INDEPENDENT', icon: 'fa-user-check', label: 'Super' },
 { id: 'CERTIFIED', icon: 'fa-certificate', label: 'Active' }
 ].map((step, idx) => {
 const weight = getStatusWeight(app.status);
 const currentWeight = idx + 1;
 const isDone = weight >= currentWeight;
 const isActive = weight === currentWeight - 1;

 return (
 <div key={step.id} className={`step-node ${isDone ? 'done' : ''} ${isActive ? 'active' : ''}`} style={{ width: '40px' }}><div className="node-icon" style={{ width: '24px', height: '24px', fontSize: '10px' }}><i className={`fas ${step.icon}`}></i></div><label style={{ fontSize: '7px' }}>{step.label}</label></div>);
 })}
 </div>
<div className="progress-details"><div className="p-item" style={{ marginBottom: 14 }}><label>IDENTITY & DOCUMENTS</label><span className="p-count">National ID: {app.national_id || 'Not supplied'}</span><div className="doc-chip-row">{[
 ['ID Front', app.documents?.id_front],
 ['ID Back', app.documents?.id_back],
 ['Proof of Address', app.documents?.proof_of_address],
 ['CV', app.documents?.cv],
 ].map(([label, doc]) => (
 <button key={label} type="button" className={`doc-chip ${doc?.data_url ? 'ready' : ''}`} onClick={() => openDocument(doc)}><i className={`fas ${doc?.data_url ? 'fa-eye' : 'fa-triangle-exclamation'}`}></i>{label}
 </button>))}
 </div></div><div className="p-item"><label>TRAINING CURRICULUM</label><div className="p-bar-v4"><div className="p-fill" style={{ width: `${Math.min(100, (app.training_modules_completed?.filter(m => m.startsWith('M')).length || 0) * 10)}%` }}></div></div><span className="p-count">{Math.min(10, (app.training_modules_completed?.filter(m => m.startsWith('M')).length || 0))}/10 MODULES</span></div></div>
<div className="card-actions">{app.status === 'APPLIED' && (
 <button className="v4-action-btn primary" onClick={() => handleAction(app.id, 'DOCS')}><i className="fas fa-file-signature"></i> VERIFY DOCS
 </button>)}
 {app.status === 'DOCS_VERIFIED' && (
 <div className="p-item" style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontStyle: 'italic' }}>Awaiting curriculum sync...
 </div>)}
 {app.status === 'DOCS_VERIFIED' && app.training_modules_completed?.length >= 5 && (
 <button className="v4-action-btn primary" onClick={() => handleAction(app.id, 'GEAR')}><i className="fas fa-microchip"></i> ISSUE EQUIPMENT
 </button>)}
 {app.status === 'EXAM_PASSED' && (
 <button className="v4-action-btn primary" onClick={() => handleAction(app.id, 'PRACTICAL')}><i className="fas fa-vial"></i> LOG PRACTICAL
 </button>)}
 {app.status === 'READY_FOR_SHADOWING' && (
 <button className="v4-action-btn warning" onClick={() => handleAction(app.id, 'SHADOW')}><i className="fas fa-user-ninja"></i> LOG SHADOWING
 </button>)}
 {app.status === 'SUPERVISED_INDEPENDENT' && (
 <button className="v4-action-btn success" onClick={() => handleAction(app.id, 'CERTIFY')}><i className="fas fa-check-double"></i> FINAL SIGN-OFF
 </button>)}
 {app.status === 'READY_FOR_CERTIFICATION' && (
 <button className="v4-action-btn success" onClick={() => handleAction(app.id, 'CERTIFY')}><i className="fas fa-certificate"></i> CERTIFY AGENT
 </button>)}
 {app.status === 'CERTIFIED' && (
 <div className="certified-badge"><i className="fas fa-check-double"></i> AGENT ACTIVATED
 </div>)}
 </div></div>))}
 </div>
<style>{`
 .v4-recruitment-pipeline { padding: 0px; height: 100%; display: flex; flex-direction: column; gap: 24px; }
 .recruitment-hero-v4 { background: var(--v4-primary-gradient); padding: 48px; border-radius: 24px; color: #fff; display: flex; justify-content: space-between; align-items: flex-end; position: relative; overflow: hidden; }
 .recruitment-hero-v4::after { content: ''; position: absolute; top: -50%; right: -10%; width: 500px; height: 500px; background: rgba(255,255,255,0.05); border-radius: 50%; }
 .hero-left h1 { font-size: 42px; margin: 12px 0; font-weight: 950; }
 .hero-left h1 span { color: #5eead4; }
 .hero-left p { opacity: 0.8; font-size: 16px; max-width: 500px; line-height: 1.6; }
 .kicker { display: flex; align-items: center; gap: 10px; font-size: 10px; font-weight: 900; letter-spacing: 2px; color: #5eead4; margin-bottom: 8px; }
 
 .hero-stats { display: flex; gap: 16px; }
 .stat-pill { background: rgba(0,0,0,0.3); padding: 16px 24px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); min-width: 140px; }
 .stat-pill label { display: block; font-size: 9px; font-weight: 800; color: #5eead4; margin-bottom: 4px; }
 .stat-pill strong { font-size: 24px; font-weight: 950; }

 .v4-pipeline-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 24px; }
 .v4-applicant-card { background: var(--v4-card-bg); border: 1.5px solid var(--v4-border); border-radius: 20px; padding: 24px; display: flex; flex-direction: column; gap: 20px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
 .v4-applicant-card:hover { border-color: var(--v4-primary); transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.1); }
 .v4-applicant-card.archived { opacity: 0.7; background: rgba(0,0,0,0.02); }

 .card-top { display: flex; justify-content: space-between; align-items: flex-start; }
 .candidate-info { display: flex; align-items: center; gap: 12px; }
 .c-av { width: 48px; height: 48px; border-radius: 14px; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 950; }
 .c-meta strong { display: block; font-size: 16px; color: var(--v4-text); }
 .c-meta span { font-size: 11px; color: var(--v4-text-dim); font-weight: 600; }

 .status-tag { padding: 4px 12px; border-radius: 10px; font-size: 9px; font-weight: 900; text-transform: uppercase; background: var(--v4-surface); border: 1.5px solid var(--v4-border); }
 .status-tag.applied { color: #3b82f6; border-color: #3b82f644; }
 .status-tag.docs_verified { color: #9333ea; border-color: #9333ea44; }
 .status-tag.ready_for_shadowing { color: #f59e0b; border-color: #f59e0b44; }
 .status-tag.ready_for_certification { color: #10b981; border-color: #10b98144; }
 .status-tag.certified { color: #0d9488; border-color: #0d948844; background: #ccfbf1; }

 .pipeline-stepper { display: flex; justify-content: space-between; position: relative; padding: 10px 0; }
 .pipeline-stepper::before { content: ''; position: absolute; top: 25px; left: 20px; right: 20px; height: 3px; background: var(--v4-border); z-index: 0; }
 .step-node { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; width: 50px; }
 .node-icon { width: 32px; height: 32px; border-radius: 50%; background: var(--v4-bg); border: 2px solid var(--v4-border); display: flex; align-items: center; justify-content: center; font-size: 12px; color: var(--v4-text-dim); transition: all 0.3s; }
 .step-node label { font-size: 8px; font-weight: 900; text-transform: uppercase; color: var(--v4-text-dim); text-align: center; }
 
 .step-node.done .node-icon { background: var(--v4-primary); border-color: var(--v4-primary); color: #fff; box-shadow: 0 0 10px var(--v4-primary-glow); }
 .step-node.done label { color: var(--v4-primary); }
 .step-node.active .node-icon { border-color: var(--v4-primary); color: var(--v4-primary); animation: step-pulse 2s infinite; }

 .progress-details { background: var(--v4-surface); padding: 16px; border-radius: 12px; border: 1px solid var(--v4-border); }
 .p-item label { display: block; font-size: 9px; font-weight: 900; color: var(--v4-text-dim); margin-bottom: 8px; }
 .p-bar-v4 { height: 6px; background: var(--v4-border); border-radius: 3px; overflow: hidden; margin-bottom: 6px; }
 .p-fill { height: 100%; background: var(--v4-primary-gradient); transition: width 1s ease-in-out; }
 .p-count { font-size: 10px; font-weight: 900; color: var(--v4-text); }
 .doc-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
 .doc-chip { border: 1.5px solid var(--v4-border); background: var(--v4-card-bg); color: var(--v4-text-dim); border-radius: 999px; padding: 7px 10px; font-size: 10px; font-weight: 900; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
 .doc-chip.ready { color: #10b981; border-color: #10b98155; background: #ecfdf5; }
 .doc-chip:hover { transform: translateY(-1px); border-color: var(--v4-primary); }

 .card-actions { display: flex; gap: 12px; }
 .v4-action-btn { flex: 1; padding: 12px; border-radius: 12px; border: none; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 12px; font-weight: 800; cursor: pointer; transition: all 0.2s; }
 .v4-action-btn.primary { background: var(--v4-primary); color: #fff; box-shadow: 0 4px 12px var(--v4-primary-glow); }
 .v4-action-btn.warning { background: #f59e0b; color: #fff; }
 .v4-action-btn.success { background: #10b981; color: #fff; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
 .v4-action-btn:hover { transform: scale(1.02); filter: brightness(1.1); }
 
 .certified-badge { flex: 1; text-align: center; padding: 12px; background: #ccfbf1; color: #0d9488; border-radius: 12px; font-size: 11px; font-weight: 900; border: 1.5px dashed #0d948844; }

 @keyframes step-pulse {
 0% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4); }
 70% { box-shadow: 0 0 0 10px rgba(79, 70, 229, 0); }
 100% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0); }
 }
 `}</style></div>);
}
 