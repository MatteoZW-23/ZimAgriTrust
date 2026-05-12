import React, { useState, useEffect, useRef } from "react";
import "./styles.css";
import {
  academyLogin, verifyOtp, getProfile, logout,
  checkApplicationStatus,
  getVerificationQueue, approveVerification, rejectVerification,
  getReviewQueue, verifyListing,
  getMyDisputes, submitDisputeRecommendation,
  getAllListings, getMyOrders, getWalletBalance, getTransactions, getAgentEarnings,
  getDeliveryStatus, markPickupInProgress, confirmPickup, markDeliveryArrived, confirmDeliveryByAgent,
  getTradeSessions, getTradeMessages, sendTradeMessage,
  getAcademyProgress, markTopicComplete, getTopicContent, submitExam, getCertificates,
  getMarketPrices,
} from "./api.js";
import AgentApplicationWizard from "./components/AgentApplicationWizard";
import PracticalAssessmentPanel from "./components/PracticalAssessmentPanel";
import ShadowingPanel from "./components/ShadowingPanel";
import SupervisedPanel from "./components/SupervisedPanel";

const AUTH_KEY = "zimagritrust_agent_auth";
const USER_KEY = "zimagritrust_agent_user";
const CROPS = ["Maize","Wheat","Soybean","Tobacco","Cotton","Tomato","Potato","Groundnuts","Sorghum","Sunflower","Other"];
const PROVINCES = ["Harare","Bulawayo","Manicaland","Mashonaland Central","Mashonaland East","Mashonaland West","Masvingo","Matabeleland North","Matabeleland South","Midlands"];

// ── Auth ──────────────────────────────────────────────────────────────────────
function AuthScreen({ onLogin }) {
  const [agentCode, setAgentCode] = useState(""); const [pin, setPin] = useState("");
  const [otp, setOtp] = useState(""); const [step, setStep] = useState(1);
  const [pending, setPending] = useState(""); const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [mode, setMode] = useState("login");
  const [statusPhone, setStatusPhone] = useState("");
  const [application, setApplication] = useState(null);

  const fmt = p => p.startsWith("+") ? p.replace(/\s/g, "") : `+263${p.replace(/^0+/, "").replace(/\s/g, "")}`;

  const handleLogin = async e => {
    e.preventDefault(); setErr(""); setLoading(true);
    try {
      onLogin(await academyLogin(agentCode.trim().toUpperCase(), pin));
    } catch(e){ setErr(e.message); } finally { setLoading(false); }
  };

  const handleVerify = async e => {
    e.preventDefault(); setErr(""); setLoading(true);
    try { onLogin(await verifyOtp(pending, otp)); }
    catch(e){ setErr(e.message); } finally { setLoading(false); }
  };

  const handleStatusCheck = async e => {
    e.preventDefault(); setErr(""); setApplication(null); setLoading(true);
    try { setApplication(await checkApplicationStatus(fmt(statusPhone))); }
    catch(e){ setErr(e.status === 404 ? "No application found for that phone number." : e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-brand">
          <img src="/logo.png" alt="ZimAgriTrust" style={{ height: '48px', width: 'auto' }} />
          <h1>ZimAgritrust</h1><p>Agent Portal</p>
        </div>
        {err && <div className="alert alert-error">{err}</div>}
        <div className="auth-mode-grid">
          <button type="button" className={`auth-mode ${mode==="login"?"active":""}`} onClick={()=>{setMode("login");setErr("");}}>
            <i className="fas fa-lock"></i>
            <span>Approved Agent</span>
          </button>
          <button type="button" className={`auth-mode ${mode==="apply"?"active":""}`} onClick={()=>{setMode("apply");setErr("");}}>
            <i className="fas fa-user-plus"></i>
            <span>Apply</span>
          </button>
          <button type="button" className={`auth-mode ${mode==="status"?"active":""}`} onClick={()=>{setMode("status");setErr("");}}>
            <i className="fas fa-search"></i>
            <span>Status</span>
          </button>
        </div>
        {mode === "apply" ? (
          <div>
            <div className="pipeline-card">
              <div className="pipeline-icon"><i className="fas fa-road"></i></div>
              <div>
                <h3>Start your field agent journey</h3>
                <p>Submit your application first. After documentation approval, you will receive your trainee code and PIN by WhatsApp/SMS.</p>
              </div>
            </div>
            <div className="flow-list">
              <div><strong>1</strong><span>Apply and submit identity details</span></div>
              <div><strong>2</strong><span>Documentation is reviewed by operations</span></div>
              <div><strong>3</strong><span>Approved trainees receive Academy login details</span></div>
              <div><strong>4</strong><span>Complete training, practicals, shadowing and deployment</span></div>
            </div>
            <a className="btn btn-primary btn-full btn-lg" href="?apply=1">Start Agent Application</a>
            <button type="button" className="btn btn-ghost btn-full" style={{marginTop:8}} onClick={()=>setMode("status")}>Already applied? Check status</button>
          </div>
        ) : mode === "status" ? (
          <form onSubmit={handleStatusCheck}>
            <div className="section-intro">
              <h3>Track your onboarding stage</h3>
              <p>Use the phone number submitted on your application to see your current pipeline status.</p>
            </div>
            <div className="form-group"><label className="form-label">Application Phone</label>
              <div className="phone-row"><span className="phone-prefix">+263</span>
                <input className="form-input" type="tel" placeholder="77 123 4567" value={statusPhone} onChange={e=>setStatusPhone(e.target.value)} required />
              </div></div>
            <button className="btn btn-primary btn-full btn-lg" disabled={loading}>{loading?"Checking...":"Check Application Status"}</button>
            {application && <ApplicationStatusCard application={application} />}
          </form>
        ) : step === 1 ? (
          <form onSubmit={handleLogin}>
            <div className="section-intro">
              <h3>Secure Agent Academy Login</h3>
              <p>Use the Agent Code and Initial PIN sent to you after documentation approval. This opens Academy training first.</p>
            </div>
            <div className="form-group"><label className="form-label">Agent Code</label>
              <input className="form-input" placeholder="TRNC0467" value={agentCode} onChange={e=>setAgentCode(e.target.value)} required />
            </div>
            <div className="form-group"><label className="form-label">Initial PIN</label>
              <input className="form-input" type="password" inputMode="numeric" placeholder="6-digit PIN" value={pin} onChange={e=>setPin(e.target.value)} required /></div>
            <button className="btn btn-primary btn-full btn-lg" disabled={loading}>{loading?"Authenticating...":"Enter Agent Academy"}</button>
          </form>
        ) : (
          <form onSubmit={handleVerify}>
            <p style={{textAlign:"center",color:"var(--text-dim)",marginBottom:16}}>Enter 6-digit OTP sent to your phone</p>
            <input className="form-input" style={{textAlign:"center",letterSpacing:8,fontSize:20}} maxLength={6} value={otp} onChange={e=>setOtp(e.target.value)} required />
            <button className="btn btn-primary btn-full btn-lg" style={{marginTop:16}} disabled={loading||otp.length<6}>{loading?"Verifying...":"Verify & Login"}</button>
            <button type="button" className="btn btn-ghost btn-full" style={{marginTop:8}} onClick={()=>setStep(1)}>← Back</button>
          </form>
        )}
      </div>
    </div>
  );
}

function ApplicationStatusCard({ application }) {
  const status = String(application?.status || "pending").toLowerCase();
  const steps = [
    ["pending", "Application received"],
    ["documentation", "Document review"],
    ["training", "Academy training"],
    ["equipment", "Equipment/app setup"],
    ["practical", "Practical assessment"],
    ["shadowing", "Shadowing"],
    ["certified", "Certified agent"],
  ];
  const matchedIndex = steps.findIndex(([key]) => status.includes(key));
  const currentIndex = matchedIndex >= 0 ? matchedIndex : 0;
  return (
    <div className="status-card">
      <div className="status-card-header">
        <div>
          <div className="card-title">Application Status</div>
          <p>Your latest recruitment pipeline position</p>
        </div>
        <span className="badge badge-yellow">{application.status || "pending"}</span>
      </div>
      <div className="status-row">
        <span>Application ID</span><strong>{application.id}</strong>
      </div>
      <div className="status-timeline">
        {steps.map(([key,label], index)=>(
          <div key={key} className={`status-step ${index<=currentIndex?"done":""}`}>
            <i className="fas fa-check-circle"></i>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <p className="status-note">
        If approved, you will receive SMS instructions. If rejected, contact support or resubmit when requested.
      </p>
    </div>
  );
}

// ── Dashboard Overview ────────────────────────────────────────────────────────
function Dashboard({ user }) {
  const [stats, setStats] = useState({});
  useEffect(() => {
    getWalletBalance().then(w => setStats(s=>({...s, balance: w?.balance ?? w?.available_balance ?? 0}))).catch(()=>{});
    getVerificationQueue("pending").then(d => setStats(s=>({...s, kyc: Array.isArray(d)?d.length:0}))).catch(()=>{});
    getMyDisputes().then(d => setStats(s=>({...s, disputes: Array.isArray(d)?d.filter(x=>x.status==="open").length:0}))).catch(()=>{});
    getReviewQueue().then(d => setStats(s=>({...s, listings: Array.isArray(d)?d.length:0}))).catch(()=>{});
  }, []);

  return (
    <div>
      <h2 className="page-title">Agent Dashboard</h2>
      <p className="page-sub">Welcome back, {user?.full_name?.split(" ")[0] || "Agent"} · Trust Score: {user?.trust_score ?? "—"}/100</p>
      <div className="stats-grid">
        {[
          { icon:"fa-wallet", label:"Wallet Balance", value:`$${Number(stats.balance||0).toFixed(2)}`, sub:"Available earnings" },
          { icon:"fa-id-card", label:"KYC Pending", value:stats.kyc??"-", sub:"Awaiting review" },
          { icon:"fa-flag", label:"Open Disputes", value:stats.disputes??"-", sub:"Need mediation" },
          { icon:"fa-list", label:"Listings Review", value:stats.listings??"-", sub:"Awaiting approval" },
        ].map(s=>(
          <div key={s.label} className="stat-card">
            <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
            <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong><span>{s.sub}</span></div>
          </div>
        ))}
      </div>
    </div>
  );
}

// -- KYC Verification Queue ----------------------------------------------------
function KYCPanel() {
  const [queue, setQueue] = useState(null);
  const [tab, setTab] = useState("pending");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const load = () => getVerificationQueue(tab).then(setQueue).catch(()=>setQueue([]));
  useEffect(load, [tab]);
  const handleApprove = async (id) => {
    const note = prompt("Approval note:", "Documents verified and approved.");
    if (note === null) return;
    setLoading(true);
    try { await approveVerification(id, note); setMsg("Approved!"); load(); }
    catch(e){ setMsg(e.message); } finally { setLoading(false); }
  };
  const handleReject = async (id) => {
    const note = prompt("Rejection reason:");
    if (!note) return;
    setLoading(true);
    try { await rejectVerification(id, note); setMsg("Rejected."); load(); }
    catch(e){ setMsg(e.message); } finally { setLoading(false); }
  };
  return (
    <div>
      <h2 className="page-title">KYC Verification Queue</h2>
      <p className="page-sub">Review identity documents submitted by users</p>
      {msg && <div className="alert alert-info" onClick={()=>setMsg("")}>{msg}</div>}
      <div style={{display:"flex",gap:8,marginBottom:16}}>
        {["pending","approved","rejected"].map(t=>(
          <button key={t} className={`btn btn-sm ${tab===t?"btn-primary":"btn-ghost"}`} onClick={()=>setTab(t)}>{t[0].toUpperCase()+t.slice(1)}</button>
        ))}
      </div>
      {queue===null ? <p>Loading...</p> : queue.length===0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-inbox"></i></div><h3>No {tab} requests</h3></div>
      ) : (
        <div className="card"><div className="table-wrap"><table>
          <thead><tr><th>User</th><th>Phone</th><th>Role</th><th>ID Number</th><th>Documents</th><th>Date</th><th>Actions</th></tr></thead>
          <tbody>
            {queue.map(r=>(
              <tr key={r.request_id}>
                <td><strong>{r.user_name}</strong></td>
                <td style={{fontFamily:"monospace",fontSize:12}}>{r.user_phone}</td>
                <td><span className="badge badge-yellow">{r.user_role}</span></td>
                <td>{r.national_id_number||"�"}</td>
                <td style={{fontSize:12}}>
                  {r.has_front&&<span className="badge badge-green" style={{marginRight:4}}>Front</span>}
                  {r.has_back&&<span className="badge badge-green" style={{marginRight:4}}>Back</span>}
                  {r.has_selfie&&<span className="badge badge-green">Selfie</span>}
                </td>
                <td style={{fontSize:11}}>{new Date(r.submitted_at).toLocaleDateString()}</td>
                <td>
                  {tab==="pending" ? (
                    <div style={{display:"flex",gap:6}}>
                      <button className="btn btn-sm btn-primary" onClick={()=>handleApprove(r.request_id)} disabled={loading}>Approve</button>
                      <button className="btn btn-sm btn-danger" onClick={()=>handleReject(r.request_id)} disabled={loading}>Reject</button>
                    </div>
                  ) : <span className={`badge ${tab==="approved"?"badge-green":"badge-red"}`}>{tab}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table></div></div>
      )}
    </div>
  );
}

// -- Listing Review ------------------------------------------------------------
function ListingReviewPanel() {
  const [queue, setQueue] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const load = () => getReviewQueue().then(d=>setQueue(Array.isArray(d)?d:d?.listings||[])).catch(()=>setQueue([]));
  useEffect(load, []);
  const handle = async (id, approved) => {
    setLoading(true);
    try { await verifyListing(id, approved); setMsg(approved?"Listing approved!":"Listing rejected."); load(); }
    catch(e){ setMsg(e.message); } finally { setLoading(false); }
  };
  return (
    <div>
      <h2 className="page-title">Listing Review</h2>
      <p className="page-sub">Approve farmer crop listings before they go live</p>
      {msg && <div className="alert alert-info" onClick={()=>setMsg("")}>{msg}</div>}
      {queue===null ? <p>Loading...</p> : queue.length===0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-clipboard-list"></i></div><h3>No listings pending review</h3></div>
      ) : (
        <div className="listing-grid">
          {queue.map(l=>(
            <div key={l.id} className="listing-card">
              <div className="listing-card-top">
                <div><div className="listing-crop-name">{l.crop_type||l.crop}</div>
                <div className="listing-location"><i className="fas fa-map-marker-alt"></i> {l.province}</div></div>
              </div>
              <div>
                <div className="listing-price">${Number(l.price_per_kg||l.price||0).toFixed(2)}/kg</div>
                <div className="listing-qty">{l.quantity_kg||l.quantity} kg � Grade {l.grade||"A"}</div>
                <div style={{fontSize:12,color:"var(--text-dim)",marginTop:4}}>by {l.farmer_name||"Farmer"}</div>
              </div>
              <div className="listing-actions" style={{display:"flex",gap:8}}>
                <button className="btn btn-sm btn-primary" style={{flex:1}} onClick={()=>handle(l.id,true)} disabled={loading}>? Approve</button>
                <button className="btn btn-sm btn-danger" style={{flex:1}} onClick={()=>handle(l.id,false)} disabled={loading}>? Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// -- Disputes Mediation --------------------------------------------------------
function DisputesPanel() {
  const [disputes, setDisputes] = useState(null);
  const [selected, setSelected] = useState(null);
  const [rec, setRec] = useState({outcome:"refund",note:""});
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const load = () => getMyDisputes().then(d=>setDisputes(Array.isArray(d)?d:[])).catch(()=>setDisputes([]));
  useEffect(load, []);
  const handleSubmit = async e => {
    e.preventDefault(); setLoading(true);
    try { await submitDisputeRecommendation(selected.id, rec); setMsg("Recommendation submitted!"); setSelected(null); load(); }
    catch(e){ setMsg(e.message); } finally { setLoading(false); }
  };
  const sc = s=>({open:"badge-yellow",investigating:"badge-yellow",resolved:"badge-green",escalated:"badge-red"}[s]||"badge-gray");
  return (
    <div>
      <h2 className="page-title">Disputes & Mediation</h2>
      <p className="page-sub">Investigate and mediate buyer-farmer disputes</p>
      {msg && <div className="alert alert-info" onClick={()=>setMsg("")}>{msg}</div>}
      {disputes===null ? <p>Loading...</p> : disputes.length===0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-balance-scale"></i></div><h3>No disputes assigned</h3></div>
      ) : (
        <div className="card"><div className="table-wrap"><table>
          <thead><tr><th>ID</th><th>Reason</th><th>Status</th><th>Date</th><th>Action</th></tr></thead>
          <tbody>
            {disputes.map(d=>(
              <tr key={d.id}>
                <td style={{fontFamily:"monospace",fontSize:11}}>{d.id?.slice(0,8)}�</td>
                <td>{d.reason||d.description||"�"}</td>
                <td><span className={`badge ${sc(d.status)}`}>{d.status}</span></td>
                <td style={{fontSize:11}}>{new Date(d.created_at).toLocaleDateString()}</td>
                <td>{d.status!=="resolved"&&<button className="btn btn-sm btn-primary" onClick={()=>setSelected(d)}>Mediate</button>}</td>
              </tr>
            ))}
          </tbody>
        </table></div></div>
      )}
      {selected&&(
        <div className="modal-overlay" onClick={()=>setSelected(null)}>
          <div className="modal-box" onClick={e=>e.stopPropagation()}>
            <button className="modal-close" onClick={()=>setSelected(null)}>&times;</button>
            <div className="modal-title">Mediation Recommendation</div>
            <form onSubmit={handleSubmit}>
              <div className="form-group"><label className="form-label">Outcome</label>
                <select className="form-select" value={rec.outcome} onChange={e=>setRec(r=>({...r,outcome:e.target.value}))}>
                  <option value="refund">Full Refund to Buyer</option>
                  <option value="release">Release Payment to Farmer</option>
                  <option value="partial">Partial Settlement</option>
                  <option value="escalate">Escalate to Admin</option>
                </select></div>
              <div className="form-group"><label className="form-label">Investigation Notes</label>
                <textarea className="form-textarea" rows={4} value={rec.note} onChange={e=>setRec(r=>({...r,note:e.target.value}))} required placeholder="Describe your findings..." /></div>
              <button className="btn btn-primary btn-full" type="submit" disabled={loading}>Submit Recommendation</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// -- Wallet / Earnings ---------------------------------------------------------
function EarningsPanel() {
  const [wallet, setWallet] = useState(null);
  const [txns, setTxns] = useState(null);
  useEffect(()=>{
    getWalletBalance().then(setWallet).catch(()=>{});
    getTransactions().then(d=>setTxns(Array.isArray(d)?d:d?.transactions||[])).catch(()=>setTxns([]));
  },[]);
  const balance = wallet?.balance??wallet?.available_balance??0;
  const pending = wallet?.pending_balance??wallet?.pending??0;
  return (
    <div>
      <h2 className="page-title">Earnings & Wallet</h2>
      <p className="page-sub">Track your commissions and payouts</p>
      <div className="stats-grid">
        {[
          {icon:"fa-wallet",label:"Available Balance",value:`$${Number(balance).toFixed(2)}`},
          {icon:"fa-clock",label:"Pending",value:`$${Number(pending).toFixed(2)}`},
          {icon:"fa-list",label:"Transactions",value:txns?.length??"-"},
        ].map(s=>(
          <div key={s.label} className="stat-card">
            <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
            <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong></div>
          </div>
        ))}
      </div>
      {txns&&txns.length>0&&(
        <div className="card" style={{marginTop:20}}>
          <div className="card-title">Recent Transactions</div>
          <div className="table-wrap"><table>
            <thead><tr><th>ID</th><th>Type</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>
              {txns.slice(0,20).map(t=>(
                <tr key={t.id}>
                  <td style={{fontFamily:"monospace",fontSize:11}}>{t.id?.slice(0,8)}�</td>
                  <td>{t.type||t.transaction_type||"�"}</td>
                  <td style={{fontWeight:700,color:"var(--primary)"}}>${Number(t.amount||t.total_amount||0).toFixed(2)}</td>
                  <td><span className={`badge ${t.status==="completed"?"badge-green":t.status==="pending"?"badge-yellow":"badge-gray"}`}>{t.status}</span></td>
                  <td style={{fontSize:11}}>{new Date(t.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
        </div>
      )}
    </div>
  );
}

// -- Academy Panel -------------------------------------------------------------
function AcademyPanel() {
  const [progress, setProgress] = useState(null);
  const [certs, setCerts] = useState(null);
  const [msg, setMsg] = useState("");
  const [activeTopic, setActiveTopic] = useState(null);
  useEffect(()=>{
    getAcademyProgress().then(setProgress).catch(()=>setProgress({modules:[]}));
    getCertificates().then(d=>setCerts(Array.isArray(d)?d:[])).catch(()=>setCerts([]));
  },[]);
  const handleComplete = async (moduleId, topicId) => {
    try { await markTopicComplete(moduleId, topicId); setMsg("Topic marked complete!"); getAcademyProgress().then(setProgress); }
    catch(e){ setMsg(e.message); }
  };
  const handleOpenTopic = async (moduleNumber, topicId) => {
    try { setActiveTopic(await getTopicContent(moduleNumber, topicId)); }
    catch(e){ setMsg(e.message); }
  };
  return (
    <div>
      <h2 className="page-title">Agent Academy</h2>
      <p className="page-sub">Complete all 10 professional training modules in sequence to unlock assessment and certification.</p>
      {msg&&<div className="alert alert-info" onClick={()=>setMsg("")}>{msg}</div>}
      {progress?.overall_progress!==undefined&&(
        <div className="academy-hero">
          <div>
            <span className="eyebrow">Certification Progress</span>
            <h3>{progress.modules_completed || 0} of {(progress.modules||[]).length || 10} modules completed</h3>
            <p>Study the module topics, mark each lesson complete, then pass the module quiz before moving forward.</p>
          </div>
          <div className="academy-progress-ring">{Math.round(progress.overall_progress || 0)}%</div>
          <div className="academy-progress-bar">
            <div style={{width:`${progress.overall_progress||0}%`}}/>
          </div>
        </div>
      )}
      {certs&&certs.length>0&&(
        <div className="card" style={{marginBottom:20}}>
          <div className="card-title"><i className="fas fa-certificate"></i> Your Certificates</div>
          <div style={{display:"flex",flexWrap:"wrap",gap:10}}>
            {certs.map((c,i)=>(
              <div key={i} style={{background:"var(--surface2)",borderRadius:8,padding:"8px 16px",border:"1px solid var(--primary)",fontSize:13}}>
                <i className="fas fa-award" style={{marginRight:6}}></i>{c.module_name||c.name}
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="grid-2">
        {(progress?.modules||[]).map(m=>{
          const completedTopics = (m.topics||[]).filter(t=>t.is_completed).length;
          const totalTopics = (m.topics||[]).length;
          const topicProgress = totalTopics ? Math.round((completedTopics / totalTopics) * 100) : 0;
          return (
          <div key={m.id} className={`academy-module-card ${m.is_locked ? "locked" : ""}`}>
            <div className="academy-module-head">
              <div>
                <span className="eyebrow">Module {m.module_number}</span>
                <div className="card-title">{m.title}</div>
              </div>
              <span className={`badge ${m.is_locked ? "badge-gray" : m.status === "completed" ? "badge-green" : "badge-yellow"}`}>{m.is_locked ? "Locked" : m.status}</span>
            </div>
            <p className="academy-module-meta">{completedTopics}/{totalTopics} lessons complete · {topicProgress}%</p>
            <div className="academy-topic-progress"><div style={{width:`${topicProgress}%`}}/></div>
            {(m.topics||[]).map(t=>(
              <div key={t.id} className="academy-topic-row">
                <button type="button" className="academy-topic-open" onClick={()=>handleOpenTopic(m.module_number,t.id)} disabled={m.is_locked}>
                  <i className="fas fa-book-open"></i>
                  {t.title}
                </button>
                {!m.is_locked&&!t.is_completed&&<button className="btn btn-sm btn-outline" onClick={()=>handleComplete(m.module_number,t.id)}>Complete</button>}
              </div>
            ))}
          </div>
        )})}
      </div>
      {activeTopic&&(
        <div className="modal-overlay" onClick={()=>setActiveTopic(null)}>
          <div className="modal-box" onClick={e=>e.stopPropagation()} style={{maxWidth:720}}>
            <button className="modal-close" onClick={()=>setActiveTopic(null)}>&times;</button>
            <div className="modal-title">{activeTopic.title}</div>
            <div className="modal-sub">Module {activeTopic.module_number} · Topic {activeTopic.topic_id}</div>
            <p style={{whiteSpace:"pre-wrap",lineHeight:1.7,color:"var(--text)",marginTop:16}}>{activeTopic.content}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function TrainingPortalShell({ user, progress, onLogout }) {
  const modulesCompleted = progress?.modules_completed || 0;
  const totalModules = (progress?.modules || []).length || 10;
  const progressPercent = Math.round(progress?.overall_progress || 0);
  const displayName = user?.full_name || progress?.agent_name || "Trainee Agent";

  return (
    <div className="training-portal">
      <header className="training-header">
        <div className="training-brand">
          <img src="/logo.png" alt="ZimAgriTrust" style={{ height: '48px', width: 'auto' }} />
          <div>
            <span className="eyebrow">ZimAgritrust Academy</span>
            <h1>Agent Training Portal</h1>
          </div>
        </div>
        <button className="btn btn-ghost" onClick={onLogout}><i className="fas fa-sign-out-alt"></i> Logout</button>
      </header>

      <section className="training-hero">
        <div>
          <span className="eyebrow">Welcome, {displayName}</span>
          <h2>Complete certification before operational access</h2>
          <p>Your main Agent Portal dashboard will unlock after you pass the final Academy test.</p>
        </div>
        <div className="training-progress-card">
          <div className="academy-progress-ring">{progressPercent}%</div>
          <strong>{modulesCompleted} / {totalModules} modules</strong>
          <span>Certification progress</span>
        </div>
      </section>

      <main className="training-content">
        <AcademyPanel />
      </main>
    </div>
  );
}

// -- Delivery Controls ---------------------------------------------------------
function DeliveryPanel() {
  const [orders, setOrders] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  useEffect(()=>{ getMyOrders().then(d=>setOrders(Array.isArray(d)?d:d?.transactions||[])).catch(()=>setOrders([])); },[]);
  const openTrack = async id => {
    setLoading(true);
    try { setTracking(await getDeliveryStatus(id)); }
    catch(e) { alert("No delivery info yet. Order may not have logistics set up."); }
    finally { setLoading(false); }
  };
  const action = async (fn, label) => {
    if (!tracking) return; setLoading(true);
    try { await fn(tracking.order_id); setMsg(`${label} done!`); setTracking(await getDeliveryStatus(tracking.order_id)); }
    catch(e){ setMsg(e.message); } finally { setLoading(false); }
  };
  const steps = ["PENDING","METHOD_SET","PICKUP_IN_PROGRESS","IN_TRANSIT","ARRIVED","DELIVERED"];
  const stepIdx = tracking ? steps.indexOf(tracking.status) : -1;
  return (
    <div>
      <h2 className="page-title">Delivery Controls</h2>
      <p className="page-sub">Manage logistics for assigned orders</p>
      {msg&&<div className="alert alert-info" onClick={()=>setMsg("")}>{msg}</div>}
      {orders===null?<p>Loading...</p>:orders.length===0?(
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-truck"></i></div><h3>No orders</h3></div>
      ):(
        <div className="card"><div className="table-wrap"><table>
          <thead><tr><th>Order ID</th><th>Crop</th><th>Amount</th><th>Status</th><th>Delivery</th></tr></thead>
          <tbody>
            {orders.map(o=>(
              <tr key={o.id}>
                <td style={{fontFamily:"monospace",fontSize:11}}>{o.id?.slice(0,8)}�</td>
                <td>{o.crop_type||o.crop||"�"}</td>
                <td style={{fontWeight:700}}>${Number(o.total_amount||o.amount||0).toFixed(2)}</td>
                <td><span className="badge badge-yellow">{o.status}</span></td>
                <td><button className="btn btn-sm btn-ghost" onClick={()=>openTrack(o.id)} disabled={loading}><i className="fas fa-cog"></i> Manage</button></td>
              </tr>
            ))}
          </tbody>
        </table></div></div>
      )}
      {tracking&&(
        <div className="modal-overlay" onClick={()=>setTracking(null)}>
          <div className="modal-box" onClick={e=>e.stopPropagation()} style={{maxWidth:480}}>
            <button className="modal-close" onClick={()=>setTracking(null)}>&times;</button>
            <div className="modal-title">Delivery Management</div>
            <div className="modal-sub">Status: <strong>{tracking.status}</strong></div>
            <div style={{display:"flex",flexDirection:"column",gap:8,marginTop:16}}>
              {[
                {label:"Mark Pickup In Progress",fn:()=>action(markPickupInProgress,"Pickup started"),show:stepIdx<=1},
                {label:"Confirm Goods Collected",fn:()=>action(id=>confirmPickup(id,{gps_verified:true}),"Pickup confirmed"),show:stepIdx===2},
                {label:"Mark Arrived at Destination",fn:()=>action(markDeliveryArrived,"Arrival confirmed"),show:stepIdx===3},
                {label:"Confirm Delivery Complete",fn:()=>action(id=>confirmDeliveryByAgent(id,{gps_verified:true}),"Delivery confirmed"),show:stepIdx===4},
              ].filter(b=>b.show).map(b=>(
                <button key={b.label} className="btn btn-primary" onClick={b.fn} disabled={loading}>{b.label}</button>
              ))}
            </div>
            <div style={{fontSize:12,color:"var(--text-dim)",marginTop:16}}>Driver: {tracking.driver_name||"Not assigned"} � ETA: {tracking.estimated_arrival_at?new Date(tracking.estimated_arrival_at).toLocaleString():"TBD"}</div>
          </div>
        </div>
      )}
    </div>
  );
}


// -- Agent Tasks Panel ---------------------------------------------------------
function TasksPanel() {
  const [tasks, setTasks] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => getMyTasks().then(d=>setTasks(Array.isArray(d)?d:[])).catch(()=>setTasks([]));
  useEffect(load, []);

  const handleAccept = async id => {
    setLoading(true);
    try { await acceptTask(id); setMsg("Task accepted!"); load(); }
    catch(e){ setMsg(e.message); } finally { setLoading(false); }
  };
  const handleReject = async id => {
    const reason = prompt("Reason for rejection:");
    if (!reason) return;
    setLoading(true);
    try { await rejectTask(id, reason); setMsg("Task rejected."); load(); }
    catch(e){ setMsg(e.message); } finally { setLoading(false); }
  };
  const handleReport = async task => {
    const notes = prompt("Enter verification notes:");
    if (notes === null) return;
    setLoading(true);
    try {
      await submitVerificationReport(task.id, { notes, recommendation: "approve", crop_exists: true, farmer_identity_ok: true });
      setMsg("Report submitted!"); load();
    }
    catch(e){ setMsg(e.message); } finally { setLoading(false); }
  };

  const sc = s => ({pending:"badge-yellow",accepted:"badge-green",completed:"badge-green",rejected:"badge-red"}[s]||"badge-gray");

  return (
    <div>
      <h2 className="page-title">My Tasks</h2>
      <p className="page-sub">Field assignments � KYC visits, listing inspections, delivery witnessing</p>
      {msg && <div className="alert alert-info" onClick={()=>setMsg("")}>{msg}</div>}
      {tasks===null ? <p>Loading...</p> : tasks.length===0 ? (
        <div className="empty-state"><div className="empty-icon"><i className="fas fa-tasks"></i></div><h3>No tasks assigned</h3></div>
      ) : (
        <div className="card"><div className="table-wrap"><table>
          <thead><tr><th>Type</th><th>Priority</th><th>Bounty</th><th>Status</th><th>Deadline</th><th>Actions</th></tr></thead>
          <tbody>
            {tasks.map(t=>(
              <tr key={t.id}>
                <td><strong>{(t.assignment_type||"Task").replace(/_/g," ")}</strong></td>
                <td><span className={`badge ${t.priority==="urgent"?"badge-red":t.priority==="high"?"badge-yellow":"badge-gray"}`}>{t.priority||"normal"}</span></td>
                <td style={{color:"var(--primary)",fontWeight:700}}>${Number(t.bounty_amount||0).toFixed(2)}</td>
                <td><span className={`badge ${sc(t.status)}`}>{t.status}</span></td>
                <td style={{fontSize:11}}>{t.deadline?new Date(t.deadline).toLocaleDateString():"�"}</td>
                <td>
                  <div style={{display:"flex",gap:6}}>
                    {t.status==="pending"&&<button className="btn btn-sm btn-primary" onClick={()=>handleAccept(t.id)} disabled={loading}>Accept</button>}
                    {t.status==="pending"&&<button className="btn btn-sm btn-danger" onClick={()=>handleReject(t.id)} disabled={loading}>Reject</button>}
                    {t.status==="accepted"&&<button className="btn btn-sm btn-primary" onClick={()=>handleReport(t)} disabled={loading}>Submit Report</button>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table></div></div>
      )}
    </div>
  );
}

// -- Performance Panel ---------------------------------------------------------
function PerformancePanel({ user }) {
  const [perf, setPerf] = useState(null);
  useEffect(()=>{ getAgentPerformance().then(setPerf).catch(()=>{}); },[]);
  const rate = perf ? ((perf.completed_tasks||0)/(perf.total_tasks||1)*100).toFixed(0) : 0;
  return (
    <div>
      <h2 className="page-title">Performance</h2>
      <p className="page-sub">Your field agent KPIs and ratings</p>
      {perf===null ? <p>Loading...</p> : (
        <>
          <div className="stats-grid">
            {[
              {icon:"fa-star",label:"Rating",value:`${Number(perf.rating||0).toFixed(1)}/5.0`},
              {icon:"fa-tasks",label:"Total Tasks",value:perf.total_tasks||0},
              {icon:"fa-check",label:"Completed",value:perf.completed_tasks||0},
              {icon:"fa-percent",label:"Completion Rate",value:`${rate}%`},
            ].map(s=>(
              <div key={s.label} className="stat-card">
                <div className="stat-icon"><i className={`fas ${s.icon}`}></i></div>
                <div className="stat-info"><label>{s.label}</label><strong>{s.value}</strong></div>
              </div>
            ))}
          </div>
          <div className="card" style={{marginTop:20}}>
            <div className="card-title">Agent Details</div>
            <div style={{display:"grid",gap:12,fontSize:14}}>
              <div style={{display:"flex",justifyContent:"space-between"}}><span>Agent Code</span><strong style={{fontFamily:"monospace"}}>{perf.agent_code||"�"}</strong></div>
              <div style={{display:"flex",justifyContent:"space-between"}}><span>Status</span><span className={`badge ${perf.status==="active"?"badge-green":"badge-yellow"}`}>{perf.status}</span></div>
              <div style={{display:"flex",justifyContent:"space-between"}}><span>Current Load</span><strong>{perf.current_load||0} active tasks</strong></div>
              <div style={{display:"flex",justifyContent:"space-between"}}><span>Avg Response Time</span><strong>{perf.avg_response_time_hours?`${Number(perf.avg_response_time_hours).toFixed(1)}h`:"�"}</strong></div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
// -- Main App ------------------------------------------------------------------
const NAV = [
  {id:"dashboard",icon:"fa-home",label:"Dashboard"},
  {id:"tasks",icon:"fa-tasks",label:"My Tasks"},
  {id:"kyc",icon:"fa-id-card",label:"KYC Queue"},
  {id:"listings",icon:"fa-list",label:"Listing Review"},
  {id:"disputes",icon:"fa-flag",label:"Disputes"},
  {id:"delivery",icon:"fa-truck",label:"Delivery"},
  {id:"academy",icon:"fa-graduation-cap",label:"Academy"},
  {id:"practical",icon:"fa-clipboard-check",label:"Practical Assessment"},
  {id:"shadowing",icon:"fa-eye",label:"Shadowing"},
  {id:"supervised",icon:"fa-user-graduate",label:"Supervised"},
  {id:"earnings",icon:"fa-wallet",label:"Earnings"},
  {id:"performance",icon:"fa-chart-line",label:"Performance"},
];

export default function App() {
  const [auth, setAuth] = useState(()=>{ try { return JSON.parse(localStorage.getItem(AUTH_KEY)); } catch{ return null; } });
  const [user, setUser] = useState(()=>{ try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch{ return null; } });
  const [view, setView] = useState("academy");
  const [academyProgress, setAcademyProgress] = useState(null);

  const handleLogin = d => {
    setAuth(d); setUser(d?.user||d);
    setView("academy");
    localStorage.setItem(AUTH_KEY, JSON.stringify(d));
    localStorage.setItem(USER_KEY, JSON.stringify(d?.user||d));
    getProfile().then(p=>{ setUser(p); localStorage.setItem(USER_KEY, JSON.stringify(p)); }).catch(()=>{});
    getAcademyProgress().then(setAcademyProgress).catch(()=>{});
  };

  const handleLogout = () => {
    logout(); setAuth(null); setUser(null);
    localStorage.removeItem(AUTH_KEY); localStorage.removeItem(USER_KEY);
  };

  useEffect(() => {
    if (!auth) return;
    getAcademyProgress().then(setAcademyProgress).catch(e=>{
      setAcademyProgress(null);
      if (e.status === 401 || e.status === 403) {
        setAuth(null);
        setUser(null);
        localStorage.removeItem(AUTH_KEY);
        localStorage.removeItem(USER_KEY);
      }
    });
  }, [auth]);

  // Pre-auth: public application wizard at /apply or ?apply=1
  const url = typeof window !== "undefined" ? window.location : { pathname: "", search: "" };
  const wantsApply = url.pathname.startsWith("/apply") || url.search.includes("apply=1");
  if (wantsApply && !auth) {
    return (
      <AgentApplicationWizard
        onCancel={() => { window.location.href = "/"; }}
        onSuccess={() => {}}
      />
    );
  }

  if (!auth) return (
    <>
      <AuthScreen onLogin={handleLogin} />
      <div style={{ position: "fixed", bottom: 16, left: 0, right: 0, textAlign: "center", fontSize: 12, color: "#94a3b8" }}>
        Not an agent yet?{" "}
        <a href="?apply=1" style={{ color: "#16a34a", fontWeight: 700 }}>Apply now</a>
      </div>
    </>
  );

  const role = (user?.role||"").toLowerCase();
  if (role && role !== "agent") return (
    <div className="auth-screen"><div className="auth-card">
      <h1>Access Denied</h1><p>This portal is for certified ZimAgritrust field agents only.</p>
      <button className="btn btn-primary btn-full" onClick={handleLogout}>Log Out</button>
    </div></div>
  );

  const certificationLevel = String(academyProgress?.certification_level || "").toLowerCase();
  const academyCompleted = certificationLevel && certificationLevel !== "trainee";

  if (!academyCompleted) {
    return <TrainingPortalShell user={user} progress={academyProgress} onLogout={handleLogout} />;
  }

  const handleNavClick = id => {
    setView(id);
  };

  const renderView = () => {
    switch(view) {
      case "tasks": return <TasksPanel />;
      case "kyc": return <KYCPanel />;
      case "listings": return <ListingReviewPanel />;
      case "disputes": return <DisputesPanel />;
      case "delivery": return <DeliveryPanel />;
      case "academy": return <AcademyPanel />;
      case "practical": return <PracticalAssessmentPanel />;
      case "shadowing": return <ShadowingPanel user={user} />;
      case "supervised": return <SupervisedPanel />;
      case "earnings": return <EarningsPanel />;
      case "performance": return <PerformancePanel user={user} />;
      default: return <Dashboard user={user} />;
    }
  };

  const initials = (user?.full_name||"A").split(" ").map(n=>n[0]).join("").slice(0,2).toUpperCase();

  return (
    <div className="app-container">
      <nav className="sidebar">
        <div className="sidebar-brand">
          <img src="/logo.png" alt="ZimAgriTrust" style={{ height: '32px', width: 'auto' }} />
          <span>Agent Portal</span>
        </div>
        <div className="sidebar-menu">
          {NAV.map(n=>(
            <button key={n.id} className={`sidebar-item ${view===n.id?"active":""}`} onClick={()=>handleNavClick(n.id)}>
              <i className={`fas ${n.icon}`}></i> {n.label}
            </button>
          ))}
        </div>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{initials}</div>
            <div><div className="user-name">{user?.full_name||"Agent"}</div><div className="user-role">Field Agent � Score: {user?.trust_score??"-"}</div></div>
          </div>
          <button className="btn btn-ghost btn-full" onClick={handleLogout}><i className="fas fa-sign-out-alt"></i> Logout</button>
        </div>
      </nav>
      <main className="main-content">{renderView()}</main>
    </div>
  );
}

