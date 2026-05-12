import React, { useState, useCallback, useMemo } from 'react';
import { loginPin, register, getProfile, request } from "../api";


export default function PublicLoginScreen({ onLogin, onBrowseGuest }) {
  const [tab, setTab] = useState("login");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [pin, setPin] = useState("");
  const [regPin, setRegPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  
  // Forgot Password State
  const [forgotStep, setForgotStep] = useState(1); 
  const [otp, setOtp] = useState("");
  const [newPin, setNewPin] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  // Login flow states (public users use PIN login, no 2FA)
  const [loginStep, setLoginStep] = useState(1);
  const [pendingPhone, setPendingPhone] = useState("");
  const [otpValue, setOtpValue] = useState("");

  // Academy Academy Stats
  const [academyAppId, setAcademyAppId] = useState("");
  const [isExamStarted, setIsExamStarted] = useState(false);
  const [academyView, setAcademyView] = useState("curriculum"); // curriculum or exam
  const [trainingModules, setTrainingModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [activeLesson, setActiveLesson] = useState(null);
  const [examQuestions, setExamQuestions] = useState([]);
  const [activePageIndex, setActivePageIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [examResults, setExamResults] = useState(null);

  const [academyPassword, setAcademyPassword] = useState("");
  const [academyToken, setAcademyToken] = useState(null);
  const [certificationLevel, setCertificationLevel] = useState("trainee");

  // Show/hide PIN toggles
  const [showPin, setShowPin] = useState(false);
  const [showRegPin, setShowRegPin] = useState(false);
  const [showConfirmPin, setShowConfirmPin] = useState(false);
  const [showAcademyPin, setShowAcademyPin] = useState(false);
  const [showNewPin, setShowNewPin] = useState(false);

  const enterAcademy = async () => {
    if (!academyAppId || !academyPassword) {
      setError("PLEASE ENTER BOTH AGENT CODE AND SECURITY PASSWORD.");
      return;
    }
    try {
      setLoading(true);
      setError("");
      
      // 1. Secure Authentication Exchange
      const auth = await request(`/academy/login`, {
          method: "POST",
          body: JSON.stringify({ agent_code: academyAppId, pin: academyPassword })
      });
      
      setAcademyToken(auth.access_token);
      
      // 2. Fetch Progress using the new session token
      const progress = await request(`/academy/my-progress`, { 
        headers: { 
            "Authorization": `Bearer ${auth.access_token}` 
        } 
      });
      
      setTrainingModules(progress.modules || []);
      setOverallProgress(progress.overall_progress || 0);
      setCertificationLevel(progress.certification_level);
      
      // AUTO-SELECT FIRST MODULE 
      if (progress.modules && progress.modules.length > 0) {
          setSelectedModule(progress.modules[0]);
      }
      
      setIsExamStarted(true);
      setAcademyView("curriculum");
    } catch (err) {
      setError("ACCESS DENIED: " + (err.message || "Invalid Agent Code or Password."));
    } finally {
      setLoading(false);
    }
  };


  const [overallProgress, setOverallProgress] = useState(0);

  const openLesson = async (topic) => {
    try {
      setLoading(true);
      // Fetch dynamic lesson content from the secure curriculum vault
      const res = await request(`/academy/modules/${selectedModule.module_number}/topics/${topic.id}/content`, {
          headers: { "Authorization": `Bearer ${academyToken}` }
      });
      const rawContent = res.content || "Content synchronization in progress...";
      const processedContent = typeof rawContent === 'string' 
        ? rawContent.split(/\n\n+/).map(p => p.trim()).filter(p => p.length > 0)
        : rawContent;

      setActiveLesson({ 
          ...topic, 
          abstract: res.abstract || "Historical field intelligence for this module is restricted to authorized trainees.",
          content: processedContent
      });
    } catch (err) {
      setError("CONTENT_SYNC_FAILURE: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const closeLesson = useCallback(async () => {
    if (activeLesson) {
        // Prevent multiple simultaneous calls
        if (loading) return;
        setLoading(true);
        try {
            await markTopicRead(selectedModule.module_number, activeLesson.id);
            setActiveLesson(null);
        } catch (err) {
            setError("Failed to mark lesson as complete: " + err.message);
        } finally {
            setLoading(false);
        }
    }
  }, [activeLesson, selectedModule, loading]);

  const markTopicRead = async (module_num, topic_id) => {
    try {
      setLoading(true);
      await request(`/academy/modules/${module_num}/topics/${topic_id}/complete`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${academyToken}` }
      });
      
      const progress = await request(`/academy/my-progress`, { 
        headers: { "Authorization": `Bearer ${academyToken}` } 
      });
      setTrainingModules(progress.modules || []);
      setOverallProgress(progress.overall_progress || 0);
      setCertificationLevel(progress.certification_level);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };


  const openQuiz = async (module) => {
    try {
      setLoading(true);
      const res = await request(`/academy/modules/${module.module_number}/content`, { 
        method: "GET",
        headers: { "Authorization": `Bearer ${academyToken}` }
      });
      if (res && res.quiz_questions) {
        setExamQuestions(res.quiz_questions.questions || []);
        setIsModuleQuiz(true);
        setCurrentQuizModule(module.module_number);
        setAcademyView("exam");
      }
    } catch (err) {
      setError("QUIZ_LOCK: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const [isModuleQuiz, setIsModuleQuiz] = useState(false);
  const [currentQuizModule, setCurrentQuizModule] = useState(null);

  const startExam = async () => {

    if (overallProgress < 100) {
      setError("LOCK: You must complete all 10 modules before attempting the Final Exam.");
      return;
    }
    try {
      setLoading(true);
      const res = await request(`/academy/modules/10/content`, { 
        method: "GET",
        headers: { "Authorization": `Bearer ${academyToken}` }
      });
      // In new logic, we fetch exam questions specifically if needed, otherwise use res
      setExamQuestions(res.quiz_questions?.questions || []);
      setAcademyView("exam");
    } catch (err) {
      setError("EXAM_LOCK: " + err.message);
    } finally {
      setLoading(false);
    }
  };


  const submitExam = async () => {
    try {
      setLoading(true);
      const url = isModuleQuiz 
        ? `/academy/modules/${currentQuizModule}/quiz/submit`
        : `/academy/exam/final/submit`;

      // Calculate score for display/server fallback
      let correct = 0;
      if (examQuestions.length > 0) {
          examQuestions.forEach(q => {
              if (userAnswers[q.id] === q.correct_index) correct++;
          });
      }

      const res = await request(url, {
        method: "POST",
        headers: { "Authorization": `Bearer ${academyToken}` },
        body: JSON.stringify({ 
            answers: userAnswers,
            correct_answers: correct 
        })
      });
      setExamResults(res);
      // If module quiz passed, refresh background curriculum
      if (res.passed && isModuleQuiz) {
          const progress = await request(`/academy/my-progress`, { 
            headers: { "Authorization": `Bearer ${academyToken}` } 
          });
          setTrainingModules(progress.modules || []);
          setOverallProgress(progress.overall_progress || 0);
          setCertificationLevel(progress.certification_level);
      }
    } catch (err) {
      setError("SUBMISSION FAILURE: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Forgot PIN ──────────────────────────────────────────────────────────────
  const [forgotPhone, setForgotPhone] = useState("");
  async function handleForgotRequest(e) {
    e.preventDefault();
    setLoading(true); setError(""); setSuccessMsg("");
    try {
      let cleaned = forgotPhone.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      await request("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ phone_number: "+263" + cleaned })
      });
      setForgotStep(2);
      setSuccessMsg("Verification code sent via WhatsApp & SMS.");
    } catch (err) { setError(err.message || "Failed to send code."); }
    finally { setLoading(false); }
  }

  async function handleForgotReset(e) {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      let cleaned = forgotPhone.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      await request("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ phone_number: "+263" + cleaned, otp, new_password: newPin })
      });
      setSuccessMsg("PIN updated! You can now log in with your new PIN.");
      setTab("login"); setForgotStep(1); setOtp(""); setNewPin("");
    } catch (err) { setError(err.message || "Reset failed. Check your code."); }
    finally { setLoading(false); }
  }

  // ── Resend Credentials (Academy) ────────────────────────────────────────────
  const [resendPhone, setResendPhone] = useState("");
  async function handleResendCredentials(e) {
    e.preventDefault();
    setLoading(true); setError(""); setSuccessMsg("");
    try {
      let cleaned = resendPhone.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      await request("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ phone_number: "+263" + cleaned })
      });
      setSuccessMsg("A password reset code has been sent to your WhatsApp. Use it to set a new password, then log in to the Academy.");
    } catch (err) { setError(err.message || "Could not send reset code."); }
    finally { setLoading(false); }
  }

  async function handleLoginSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let cleaned = phoneNumber.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      const fullPhone = "+263" + cleaned;
      const data = await loginPin(fullPhone, pin);
      const user = await getProfile(data.access_token);
      if (user.role?.toUpperCase() === "ADMIN" || user.role?.toUpperCase() === "AGENT") {
        throw new Error("ACCESS_RESTRICTED: Staff members must use the Secure HQ Portal.");
      }
      onLogin({ ...data, user });
    } catch (err) {
      setError(err.message || "Invalid credentials. Please verify your phone number and PIN.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRegisterSubmit(e) {
    e.preventDefault();
    setError("");
    if (regPin !== confirmPin) {
      setError("PINs do not match");
      return;
    }
    setLoading(true);
    try {
      let cleaned = regPhoneNumber.replace(/\s/g, "");
      if (cleaned.startsWith("0")) cleaned = cleaned.substring(1);
      const fullPhone = "+263" + cleaned;
      const roleInDb = userRole.toLowerCase();
      
      await register(fullName, fullPhone, roleInDb, regPin);
      const data = await loginPin(fullPhone, regPin);
      const user = await getProfile(data.access_token);
      onLogin({ ...data, user });
    } catch (err) {
      setError(err.message || "Registration failed. Please try again later.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="v4-login-page">
      <div className="v4-login-background"></div>
      
      <div className={`v4-login-container animate-fade-in ${isExamStarted ? 'academy-wide' : ''}`}>
        <div className={`${isExamStarted ? 'v4-academy-dashboard' : 'v4-login-card'}`}>
          {!isExamStarted && (
            <div className="v4-login-header">
              <div className="v4-brand">
                <img src="/logo.png" alt="ZimAgriTrust" style={{ height: '40px', width: 'auto' }} />
                <span style={{ color: '#000E2B', fontWeight: 1000, letterSpacing: '2px' }}>ZIMAGRITRUST CORE</span>
              </div>
              <h1 className="v4-institutional-title">{tab === 'login' ? 'System Authentication' : 'Account Provisioning'}</h1>
              <p className="v4-subtitle">
                {tab === 'login' ? 'Secure gateway for authorized ZimAgritrust network nodes.' : 'Establishing new infrastructure for regional transparency.'}
              </p>
            </div>
          )}

          <div className="v4-tabs">
            <button className={`v4-tab ${tab === 'login' ? 'active' : ''}`} onClick={() => setTab('login')}>Log In</button>
            <button className={`v4-tab ${tab === 'register' ? 'active' : ''}`} onClick={() => setTab('register')}>Register</button>
          </div>

          {error && (
            <div className="v4-error-alert slide-down">
              <i className="fas fa-exclamation-circle"></i>
              <span>{error}</span>
            </div>
          )}

          {tab === 'login' && (
            <form onSubmit={loginStep === 1 ? handleLoginSubmit : handleVerifyOTP} className="v4-form">
              {loginStep === 1 ? (
                <>
                  <div className="v4-field">
                    <label>Mobile Number</label>
                    <div className="v4-input-group">
                      <span className="v4-prefix">+263</span>
                      <input 
                        type="tel" 
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        placeholder="771 000 001"
                        required
                      />
                    </div>
                  </div>

                  <div className="v4-input-group animate-rise" style={{ 
                      animationDelay: '0.2s', 
                      flexDirection: 'column', 
                      alignItems: 'center', 
                      padding: '12px',
                      minHeight: '80px',
                      height: 'auto',
                      gap: '4px'
                  }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '4px' }}>
                          <label style={{ fontSize: '10px', fontWeight: 950, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Security PIN</label>
                          <span onClick={() => setTab('forgot')} style={{ fontSize: '10px', color: '#000E2B', fontWeight: 800, cursor: 'pointer', opacity: 0.8 }}>Recover PIN?</span>
                      </div>
                      <input 
                          type={showPin ? "text" : "password"}
                          inputMode="numeric"
                          pattern="[0-9]*"
                          placeholder="••••" 
                          value={pin}
                          onChange={(e) => setPin(e.target.value.replace(/[^0-9]/g, ''))}
                          maxLength={6}
                          style={{ width: '100%', border: 'none', outline: 'none', fontSize: '24px', fontWeight: 950, background: 'transparent', textAlign: 'center', letterSpacing: '0.2em' }}
                          required 
                      />
                      <button type="button" className="v4-pw-toggle" onClick={() => setShowPin(v => !v)} tabIndex={-1}>
                        <i className={`fas ${showPin ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                      </button>
                  </div>
                </>
              ) : (
                <div className="v4-field animate-rise">
                  <label style={{ textAlign: 'center', display: 'block' }}>Two-Step Verification Code</label>
                  <p style={{ fontSize: '12px', color: '#64748b', textAlign: 'center', marginBottom: '20px' }}>Enter the 6-digit cluster code sent to {pendingPhone}</p>
                  <div className="v4-input-group" style={{ height: '72px' }}>
                    <input 
                      type="text" 
                      inputMode="numeric"
                      value={otpValue}
                      onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, ''))}
                      placeholder="000 000"
                      maxLength={6}
                      required
                      style={{ textAlign: 'center', fontSize: '28px', fontWeight: 900, letterSpacing: '0.3em' }}
                    />
                  </div>
                  <button type="button" className="v4-ghost-btn" style={{ marginTop: '16px', border: 'none' }} onClick={() => setLoginStep(1)}>
                    <i className="fas fa-arrow-left"></i> Use different account
                  </button>
                </div>
              )}

              <button type="submit" className="v4-submit-btn" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : (loginStep === 1 ? "Begin Authentication" : "Verify & Access Hub")}
              </button>

              <div className="v4-divider"><span>OR</span></div>

              <button type="button" className="v4-ghost-btn" onClick={onBrowseGuest}>
                <i className="fas fa-eye"></i> Browse Public Market
              </button>
            </form>
          )}

          {tab === 'register' && (
            <form onSubmit={handleRegisterSubmit} className="v4-form">
              <div className="v4-field">
                <label>Full Legal Name</label>
                <div className="v4-input-group">
                   <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="e.g. Alex Johnson" required />
                </div>
              </div>
              <div className="v4-field">
                <label>Mobile Number</label>
                <div className="v4-input-group">
                  <span className="v4-prefix">+263</span>
                  <input type="tel" value={regPhoneNumber} onChange={(e) => setRegPhoneNumber(e.target.value)} placeholder="771 000 001" required />
                </div>
              </div>
              <div className="v4-field">
                <label>Account Role</label>
                <div className="v4-input-group">
                   <select value={userRole} onChange={(e) => setUserRole(e.target.value)} style={{ width: '100%', border: 'none', background: 'none', padding: '12px', outline: 'none' }}>
                     <option value="farmer">Farmer (Producer)</option>
                     <option value="buyer">Institutional Buyer</option>
                   </select>
                </div>
              </div>
              <div className="v4-field">
                <label>Create Security PIN</label>
                <div className="v4-input-group">
                   <input 
                      type={showRegPin ? "text" : "password"}
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={regPin} 
                      onChange={(e) => setRegPin(e.target.value.replace(/[^0-9]/g, ''))} 
                      placeholder="••••" 
                      maxLength={6}
                      required 
                   />
                   <button type="button" className="v4-pw-toggle" onClick={() => setShowRegPin(v => !v)} tabIndex={-1}>
                     <i className={`fas ${showRegPin ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                   </button>
                </div>
              </div>
              <div className="v4-field">
                <label>Repeat Security PIN</label>
                <div className="v4-input-group">
                   <input 
                      type={showConfirmPin ? "text" : "password"}
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={confirmPin} 
                      onChange={(e) => setConfirmPin(e.target.value.replace(/[^0-9]/g, ''))} 
                      placeholder="••••" 
                      maxLength={6}
                      required 
                   />
                   <button type="button" className="v4-pw-toggle" onClick={() => setShowConfirmPin(v => !v)} tabIndex={-1}>
                     <i className={`fas ${showConfirmPin ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                   </button>
                </div>
              </div>
              <button type="submit" className="v4-submit-btn" disabled={loading}>
                {loading ? <i className="fas fa-spinner fa-spin"></i> : 'Create My Account'}
              </button>
            </form>
          )}

          {tab === 'agent-apply' && (
            <div className="v4-form animate-fade-in">
              <div style={{ marginBottom: '24px', padding: '16px', background: '#ecfdf5', borderRadius: '16px', border: '1px solid #10b98122' }}>
                <h4 style={{ margin: 0, color: '#065f46', fontSize: '14px', fontWeight: 950 }}>Agent Recruitment Active</h4>
                <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: '#065f46', opacity: 0.8 }}>Join the 6-Phase Pipeline to become a certified ZimAgritrust regional agent.</p>
              </div>

              <form onSubmit={async (e) => {
                e.preventDefault();
                setLoading(true);
                try {
                  const formData = new FormData(e.target);
                  const payload = {
                    full_name: formData.get('fullName'),
                    phone_number: "+263" + formData.get('phone').replace(/\s/g, ""),
                    national_id: formData.get('idNum'),
                    province: formData.get('province'),
                    district: formData.get('district'),
                    has_smartphone: true,
                    has_transport: true,
                    agri_experience_years: parseInt(formData.get('exp')),
                    specializations: ["General Verification"]
                  };
                  const { submitApplication } = await import("../api");
                  const res = await submitApplication(payload);
                  setSuccessMsg(`APPLICATION SUBMITTED! Your ID is: ${res.id}. Please SAVE this ID; you will need it to enter the Agent Academy once your documentation is approved.`);
                  setTab('login');
                } catch (err) {
                  setError(err.message);
                } finally {
                    setLoading(false);
                }
              }}>
                <div className="v4-field">
                  <label>Full Name</label>
                  <input name="fullName" type="text" className="v4-basic-input" required />
                </div>
                <div className="v4-field">
                  <label>Mobile Number</label>
                  <div className="v4-input-group">
                    <span className="v4-prefix">+263</span>
                    <input name="phone" type="tel" required />
                  </div>
                </div>
                <div className="v4-field">
                  <label>National ID / Passport</label>
                  <input name="idNum" type="text" className="v4-basic-input" required />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div className="v4-field">
                        <label>Province</label>
                        <input name="province" type="text" className="v4-basic-input" placeholder="e.g. Harare" required />
                    </div>
                    <div className="v4-field">
                        <label>District</label>
                        <input name="district" type="text" className="v4-basic-input" placeholder="e.g. Central" required />
                    </div>
                </div>
                <div className="v4-field">
                  <label>Agri Experience (Years)</label>
                  <input name="exp" type="number" className="v4-basic-input" defaultValue="0" required />
                </div>

                <button type="submit" className="v4-submit-btn" disabled={loading} style={{ background: '#059669' }}>
                   Submit Application
                </button>
                <button type="button" className="v4-ghost-btn" style={{ marginTop: '12px' }} onClick={() => setTab('login')}>Back to Log In</button>
              </form>
            </div>
          )}

          {tab === 'forgot' && (
            <div className="v4-form animate-fade-in">
              <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <div style={{ fontSize: '40px', marginBottom: '12px' }}>🔑</div>
                <h3 style={{ fontWeight: 900, color: '#000E2B', margin: 0 }}>Reset Your PIN</h3>
                <p style={{ fontSize: '13px', color: '#64748b', marginTop: '8px' }}>
                  {forgotStep === 1 ? "Enter your phone number and we'll send a reset code via WhatsApp." : "Enter the code you received and choose a new PIN."}
                </p>
              </div>

              {forgotStep === 1 ? (
                <form onSubmit={handleForgotRequest}>
                  <div className="v4-field">
                    <label>Mobile Number</label>
                    <div className="v4-input-group">
                      <span className="v4-prefix">+263</span>
                      <input type="tel" value={forgotPhone} onChange={e => setForgotPhone(e.target.value)} placeholder="771 000 001" required />
                    </div>
                  </div>
                  <button type="submit" className="v4-submit-btn" disabled={loading}>
                    {loading ? <i className="fas fa-spinner fa-spin"></i> : 'Send Reset Code'}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleForgotReset}>
                  <div className="v4-field">
                    <label>Verification Code</label>
                    <div className="v4-input-group">
                      <input type="text" inputMode="numeric" value={otp} onChange={e => setOtp(e.target.value.replace(/\D/g, ''))} placeholder="000000" maxLength={6} required style={{ textAlign: 'center', fontSize: '22px', letterSpacing: '0.3em' }} />
                    </div>
                  </div>
                  <div className="v4-field">
                    <label>New PIN</label>
                    <div className="v4-input-group">
                      <input type={showNewPin ? "text" : "password"} inputMode="numeric" pattern="[0-9]*" value={newPin} onChange={e => setNewPin(e.target.value.replace(/[^0-9]/g, ''))} placeholder="••••" maxLength={6} required style={{ textAlign: 'center', fontSize: '22px', letterSpacing: '0.3em' }} />
                      <button type="button" className="v4-pw-toggle" onClick={() => setShowNewPin(v => !v)} tabIndex={-1}>
                        <i className={`fas ${showNewPin ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                      </button>
                    </div>
                  </div>
                  <button type="submit" className="v4-submit-btn" disabled={loading}>
                    {loading ? <i className="fas fa-spinner fa-spin"></i> : 'Set New PIN'}
                  </button>
                </form>
              )}
              <button type="button" className="v4-ghost-btn" style={{ marginTop: '12px' }} onClick={() => { setTab('login'); setForgotStep(1); }}>
                <i className="fas fa-arrow-left"></i> Back to Login
              </button>
            </div>
          )}

          {tab === 'resend-credentials' && (
            <div className="v4-form animate-fade-in">
              <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <div style={{ fontSize: '40px', marginBottom: '12px' }}>📲</div>
                <h3 style={{ fontWeight: 900, color: '#000E2B', margin: 0 }}>Resend My Credentials</h3>
                <p style={{ fontSize: '13px', color: '#64748b', marginTop: '8px' }}>
                  Enter your registered phone number. We'll send a PIN reset code to your WhatsApp so you can access the Academy.
                </p>
              </div>
              <form onSubmit={handleResendCredentials}>
                <div className="v4-field">
                  <label>Registered Phone Number</label>
                  <div className="v4-input-group">
                    <span className="v4-prefix">+263</span>
                    <input type="tel" value={resendPhone} onChange={e => setResendPhone(e.target.value)} placeholder="771 000 001" required />
                  </div>
                </div>
                <button type="submit" className="v4-submit-btn" style={{ background: '#f59e0b', color: '#000' }} disabled={loading}>
                  {loading ? <i className="fas fa-spinner fa-spin"></i> : '📲 Send to WhatsApp'}
                </button>
              </form>
              <button type="button" className="v4-ghost-btn" style={{ marginTop: '12px' }} onClick={() => setTab('academy-portal')}>
                <i className="fas fa-arrow-left"></i> Back to Academy Login
              </button>
            </div>
          )}

          {tab === 'academy-portal' && (
            <div className="v4-form animate-fade-in academy-container">
               {!isExamStarted ? (
                  <div className="v4-academy-entry-form slide-down">
                      <div className="v4-entry-header" style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                          <div style={{ background: '#f59e0b', width: '48px', height: '48px', borderRadius: '12px', display: 'grid', placeItems: 'center', color: '#fff' }}>
                              <i className="fas fa-graduation-cap" style={{ fontSize: '20px' }}></i>
                          </div>
                          <div>
                              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 900 }}>Agent Academy</h3>
                              <p style={{ margin: 0, fontSize: '12px', opacity: 0.6 }}>Secure Trainee Portal</p>
                          </div>
                      </div>

                      <div className="v4-field" style={{ marginBottom: '16px' }}>
                          <label style={{ fontSize: '10px', fontWeight: 900, color: '#f59e0b', marginBottom: '8px', display: 'block' }}>AGENT CODE</label>
                          <input 
                             type="text" 
                             className="v4-basic-input" 
                             placeholder="e.g. TRNE0AD4" 
                             value={academyAppId} 
                             onChange={(e) => setAcademyAppId(e.target.value)} 
                          />
                      </div>

                      <div className="v4-field" style={{ marginBottom: '24px' }}>
                          <label style={{ fontSize: '10px', fontWeight: 900, color: '#f59e0b', marginBottom: '8px', display: 'block' }}>SECURITY PASSWORD</label>
                          <div style={{ position: 'relative', display: 'flex', alignItems: 'center', background: '#f8fafc', border: '1.5px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
                            <input 
                               type={showAcademyPin ? "text" : "password"}
                               style={{ flex: 1, border: 'none', outline: 'none', padding: '14px 16px', fontSize: '18px', fontWeight: 800, background: 'transparent', letterSpacing: '0.2em' }}
                               placeholder="••••••••" 
                               value={academyPassword} 
                               onChange={(e) => setAcademyPassword(e.target.value)} 
                            />
                            <button type="button" className="v4-pw-toggle" onClick={() => setShowAcademyPin(v => !v)} tabIndex={-1}>
                              <i className={`fas ${showAcademyPin ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                            </button>
                          </div>
                      </div>

                      <button className="v4-submit-btn" style={{ background: '#000E2B' }} onClick={enterAcademy} disabled={loading}>
                          {loading ? <i className="fas fa-spinner fa-spin"></i> : "ENTER ACADEMY"}
                      </button>
                      
                      <button className="v4-ghost-btn" style={{ marginTop: '12px' }} onClick={() => setTab('login')}>Back to Home</button>
                      
                      <div style={{ marginTop: '16px', textAlign: 'center' }}>
                        <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700 }}>Forgot your credentials? </span>
                        <button type="button" onClick={() => setTab('resend-credentials')} style={{ background: 'none', border: 'none', color: '#f59e0b', fontWeight: 900, cursor: 'pointer', fontSize: '11px', textDecoration: 'underline' }}>
                          Resend via WhatsApp
                        </button>
                      </div>
                  </div>
                ) : (
                  <div className="academy-session-layer animate-fade-in" style={{ width: '100%', flex: 1 }}>
                     {examResults ? (
                         <div className="academy-portal-content slide-down" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', padding: '20px' }}>
                            <div className="exam-results-v4" style={{ maxWidth: '700px', width: '100%', background: '#fff', padding: '48px', borderRadius: '32px', boxShadow: '0 20px 40px rgba(0,0,0,0.05)' }}>
                                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                                    <div style={{ fontSize: '48px', color: examResults.passed ? '#20963D' : '#ef4444' }}>
                                        <i className={`fas ${examResults.passed ? 'fa-circle-check' : 'fa-circle-xmark'}`}></i>
                                    </div>
                                    <h2 style={{ margin: '16px 0 4px', fontWeight: 1000, color: '#000E2B' }}>{examResults.score}% SCORE</h2>
                                    <p style={{ fontWeight: 800, color: examResults.passed ? '#20963D' : '#ef4444' }}>{examResults.passed ? 'CERTIFICATION ACQUIRED' : 'RE-STUDY REQUIRED'}</p>
                                </div>
                                <div className="feedback-scroll" style={{ maxHeight: '300px', overflowY: 'auto', paddingRight: '12px', marginBottom: '32px' }}>
                                    {examResults.results?.map((res, i) => (
                                        <div key={i} style={{ padding: '16px', borderRadius: '12px', background: '#f8fafc', border: `1.5px solid ${res.is_correct ? '#dcfce7' : '#fee2e2'}`, marginBottom: '12px' }}>
                                            <div style={{ fontSize: '11px', fontWeight: 900, marginBottom: '4px', textTransform: 'uppercase', opacity: 0.6 }}>Question {i+1}</div>
                                            <p style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#475569' }}>{res.is_correct ? 'Excellent. Correct.' : `Incorrect. Correct Answer: ${res.explanation}`}</p>
                                        </div>
                                    ))}
                                </div>
                                <button className="v4-submit-btn" style={{ background: '#000E2B' }} onClick={() => { 
                                    if (isModuleQuiz) {
                                        setAcademyView("curriculum");
                                        setExamResults(null); 
                                        setExamQuestions([]);
                                        setUserAnswers({});
                                        setIsModuleQuiz(false);
                                    } else {
                                        setTab('login'); 
                                        setExamResults(null); 
                                        setAcademyAppId(""); 
                                        setIsExamStarted(false);
                                        setExamQuestions([]);
                                        setUserAnswers({});
                                    }
                                }}>Finish Session</button>
                            </div>
                         </div>
                     ) : examQuestions.length > 0 ? (
                         <div className="academy-portal-content slide-down" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', padding: '20px' }}>
                            <div className="questions-stack" style={{ maxWidth: '850px', width: '100%', background: '#fff', padding: '48px', borderRadius: '32px', boxShadow: '0 20px 40px rgba(0,0,0,0.05)' }}>
                               <div style={{ fontSize: '12px', fontWeight: 950, color: '#f59e0b', marginBottom: '12px', letterSpacing: '2px' }}>ASSESSMENT PROGRESS: {activePageIndex + 1} / {examQuestions.length}</div>
                               <div className="v4-progress-bar" style={{ height: '6px', background: '#f1f5f9', borderRadius: '3px', marginBottom: '32px', overflow: 'hidden' }}>
                                  <div style={{ width: `${((activePageIndex + 1) / examQuestions.length) * 100}%`, background: '#f59e0b', height: '100%', transition: 'width 0.3s' }}></div>
                               </div>
                               <h3 style={{ fontSize: '24px', fontWeight: 1000, color: '#000E2B', lineHeight: 1.4, marginBottom: '32px' }}>{examQuestions[activePageIndex]?.text}</h3>
                               <div className="options-grid" style={{ display: 'grid', gap: '12px' }}>
                                   {examQuestions[activePageIndex]?.options?.map((opt, idx) => (
                                       <button 
                                          key={idx} 
                                          className={`v4-opt-btn ${userAnswers[examQuestions[activePageIndex].id] === idx ? 'selected' : ''}`}
                                          style={{ width: '100%', padding: '24px', borderRadius: '20px', border: '2px solid #e2e8f0', background: '#fff', textAlign: 'left', fontWeight: 800, cursor: 'pointer', transition: 'all 0.2s' }}
                                          onClick={() => setUserAnswers({...userAnswers, [examQuestions[activePageIndex].id]: idx})}
                                       >
                                          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                             <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: userAnswers[examQuestions[activePageIndex].id] === idx ? '#f59e0b' : '#f8fafc', border: '1px solid #e2e8f0', display: 'grid', placeItems: 'center', fontSize: '14px', color: userAnswers[examQuestions[activePageIndex].id] === idx ? '#fff' : '#94a3b8' }}>
                                                {String.fromCharCode(65 + idx)}
                                             </div>
                                             {opt}
                                          </div>
                                       </button>
                                   ))}
                               </div>
                               <div style={{ display: 'flex', gap: '16px', marginTop: '40px' }}>
                                   {activePageIndex > 0 && <button className="q-btn ghost" style={{ flex: 1, padding: '18px' }} onClick={() => setActivePageIndex(v => v-1)}><i className="fas fa-arrow-left"></i> Previous</button>}
                                    {activePageIndex < examQuestions.length - 1 ? (
                                        <button className="q-btn primary-btn" style={{ flex: 2, background: '#000E2B', padding: '18px' }} onClick={() => setActivePageIndex(v => v+1)} disabled={userAnswers[examQuestions[activePageIndex].id] === undefined}>Next Question <i className="fas fa-arrow-right" style={{ marginLeft: '8px' }}></i></button>
                                    ) : (
                                        <button className="q-btn" style={{ flex: 2, background: '#f59e0b', color: '#fff', padding: '18px', borderRadius: '16px', fontWeight: 1000 }} onClick={submitExam} disabled={userAnswers[examQuestions[activePageIndex].id] === undefined}>
                                            {isModuleQuiz ? "SUBMIT MODULE QUIZ" : "SUBMIT FINAL CERTIFICATION"}
                                        </button>
                                    )}
                               </div>
                            </div>
                         </div>
                     ) : (
                        <div className="academy-portal-content slide-down">
                            <div className="academy-header-flex">
                                <div className="academy-brand">
                                    <h1 className="academy-title">ZIMAGRITRUST ACADEMY</h1>
                                    <p className="academy-subtitle">Curriculum & Field Training Portal</p>
                                </div>
                                <div className="academy-actions">
                                    <button className="q-btn ghost small" onClick={() => { setIsExamStarted(false); setTab('login'); }}>
                                        <i className="fas fa-sign-out-alt"></i> Exit Dashboard
                                    </button>
                                </div>
                            </div>

                            <div className="academy-layout">
                                <aside className="academy-sidebar">
                                    <div className="v4-glass-card-premium" style={{ padding: '24px', borderLeft: '4px solid #f59e0b', marginBottom: '20px' }}>
                                        <label style={{ fontSize: '10px', fontWeight: 950, opacity: 0.6, display: 'block' }}>OVERALL PROGRESS</label>
                                        <strong style={{ fontSize: '32px', display: 'block', margin: '4px 0' }}>{Math.round(overallProgress)}%</strong>
                                        <div className="v4-progress-bar" style={{ height: '8px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                                            <div style={{ width: `${overallProgress}%`, background: '#f59e0b', height: '100%', transition: 'width 1s' }}></div>
                                        </div>
                                    </div>

                                    <div className="v4-glass-card-premium" style={{ padding: '24px', marginBottom: '20px', background: 'linear-gradient(135deg, #fff 0%, #fffcf0 100%)' }}>
                                        <label style={{ fontSize: '10px', fontWeight: 950, color: '#f59e0b', textTransform: 'uppercase', letterSpacing: '1px', display: 'block', marginBottom: '8px' }}>Active Path</label>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <div className={certificationLevel === 'certified' ? 'pulse-dot' : 'pulse-dot warning'}></div>
                                            <strong style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px', color: '#000E2B' }}>{certificationLevel} AGENT</strong>
                                        </div>
                                        <p style={{ margin: '8px 0 0', fontSize: '11px', color: '#64748b', lineHeight: 1.4 }}>{certificationLevel === 'certified' ? 'You are a fully authorized agent in the ZimAgritrust network.' : 'Complete your 10 modules to unlock full farm verification powers.'}</p>
                                    </div>

                                    <div className="module-nav" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                        <h5 style={{ fontSize: '11px', fontWeight: 950, color: '#64748b', marginBottom: '12px', paddingLeft: '8px' }}>CURRICULUM MODULES</h5>
                                        {trainingModules.map((mod, idx) => (
                                            <div key={mod.id} 
                                                className={`module-nav-item`}
                                                style={{ 
                                                    padding: '14px 16px', 
                                                    borderRadius: '16px', 
                                                    background: selectedModule?.id === mod.id ? '#000E2B' : 'transparent',
                                                    color: selectedModule?.id === mod.id ? '#fff' : '#475569',
                                                    cursor: mod.is_locked ? 'not-allowed' : 'pointer',
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center',
                                                    transition: 'all 0.3s',
                                                    border: selectedModule?.id === mod.id ? 'none' : '1px solid transparent'
                                                }}
                                                onClick={() => !mod.is_locked && setSelectedModule(mod)}>
                                                <span style={{ fontSize: '13px', fontWeight: 800 }}>0{idx+1}. {mod.title}</span>
                                                {mod.is_locked ? (
                                                    <i className="fas fa-lock" style={{ fontSize: '10px', opacity: 0.5 }}></i>
                                                ) : mod.status === 'COMPLETED' ? (
                                                    <i className="fas fa-check-circle" style={{ color: '#20963D' }}></i>
                                                ) : (
                                                    <i className="fas fa-chevron-right" style={{ fontSize: '10px', opacity: 0.3 }}></i>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </aside>

                                <main className="academy-main" style={{ flexGrow: 1 }}>
                                    {selectedModule ? (
                                        <div className="module-study-center animate-fade-in" style={{ width: '100%' }}>
                                            <div className="study-header" style={{ marginBottom: '32px' }}>
                                                <div className="friendly-kicker">
                                                     <i className="fas fa-lightbulb"></i>
                                                     <span>Pro-Tip: Review the handbook carefully; the quiz has a 75% pass threshold!</span>
                                                </div>
                                                <span className="module-kicker" style={{ display: 'block', color: '#f59e0b', marginBottom: '8px' }}>MODULE 0{selectedModule.module_number}</span>
                                                <h2 className="module-main-title" style={{ margin: 0 }}>{selectedModule.title}</h2>
                                                <p className="module-description" style={{ marginTop: '16px' }}>{selectedModule.description}</p>
                                            </div>

                                            <div className="curriculum-topics-section">
                                                <h4 className="topics-heading">CORE STUDY TOPICS ({selectedModule.topics?.length})</h4>
                                                <div className="topics-grid">
                                                    {selectedModule.topics?.map(topic => (
                                                        <div key={topic.id} className={`topic-item ${topic.is_completed ? 'completed' : ''}`}>
                                                            <div className="topic-check">
                                                                {topic.is_completed && <i className="fas fa-check"></i>}
                                                            </div>
                                                            <div className="topic-info" style={{ flex: 1 }}>
                                                                <h5 style={{ margin: 0, fontSize: '14px', fontWeight: 800 }}>{topic.title}</h5>
                                                            </div>
                                                            <button className="q-btn ghost small" style={{ background: '#fff' }} onClick={() => openLesson(topic)}>
                                                                {topic.is_completed ? "Review Lesson" : "Study Lesson"}
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="module-completion-zone" style={{ marginTop: '50px', padding: '40px', background: '#f8fafc', borderRadius: '32px', border: '2px dashed #cbd5e1', textAlign: 'center' }}>
                                                {selectedModule.status === 'COMPLETED' ? (
                                                    <div>
                                                        <div style={{ width: '64px', height: '64px', background: '#ecfdf5', borderRadius: '50%', display: 'grid', placeItems: 'center', margin: '0 auto 16px', color: '#059669' }}>
                                                            <i className="fas fa-award" style={{ fontSize: '28px' }}></i>
                                                        </div>
                                                        <h3 style={{ fontSize: '20px', color: '#000E2B', marginBottom: '8px' }}>Course Module Passed!</h3>
                                                        <p style={{ fontSize: '14px', color: '#64748b' }}>Proficiency Score: <strong>{selectedModule.score}%</strong></p>
                                                    </div>
                                                ) : (
                                                    <div>
                                                        <button className="q-btn primary-btn" 
                                                                style={{ padding: '18px 60px', fontSize: '16px', background: '#000E2B', borderRadius: '16px', boxShadow: '0 20px 40px rgba(0,14,43,0.2)' }}
                                                                disabled={!selectedModule.topics?.every(t => t.is_completed)}
                                                                onClick={() => openQuiz(selectedModule)}>
                                                            {selectedModule.topics?.every(t => t.is_completed) ? "Take Certification Quiz" : "Finish All Topics to Unlock Quiz"}
                                                        </button>
                                                        <p style={{ marginTop: '16px', fontSize: '12px', color: '#94a3b8', fontWeight: 700 }}>YOU MUST READ ALL LESSONS BEFORE STARTING THE QUIZ</p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="academy-welcome animate-fade-in">
                                            <div className="welcome-content-v4">
                                                <div className="welcome-icon-stack">
                                                    <div className="icon-bg-institutional">
                                                        <i className="fas fa-certificate"></i>
                                                    </div>
                                                </div>
                                                <h2 className="v4-institutional-title">Agent Command Center</h2>
                                                <h3 className="v4-standard-subtitle">Infrastructure Training & Certification Pipeline</h3>
                                                <p className="description-standard">Identify and select an operational module from the curriculum matrix to proceed with professional accreditation.</p>
                                                
                                                <div className="institutional-audit-box">
                                                    <i className="fas fa-shield-check"></i>
                                                    <p>All training sessions are recorded on the Sovereign Ledger for audit and governance compliance.</p>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </main>

                                {activeLesson && (
                                    <div className="academic-reader-overlay animate-fade-in">
                                        <div className="academic-reader-card slide-down">
                                            <div className="reader-header">
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                    <div>
                                                        <span className="doc-type">OFFICIAL FIELD PROTOCOL</span>
                                                        <h2 className="doc-title">{activeLesson.title}</h2>
                                                    </div>
                                                    <button className="close-reader" onClick={closeLesson}>
                                                        <i className="fas fa-times"></i>
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="reader-body">
                                                <div className="academic-abstract">
                                                    <strong>ABSTRACT: </strong>
                                                    {activeLesson.abstract.split('**').map((part, idx) => 
                                                        idx % 2 === 1 ? <strong key={idx} style={{ color: '#20963D' }}>{part}</strong> : part
                                                    )}
                                                </div>
                                                <div className="academic-content">
                                                    {useMemo(() => 
                                                        activeLesson.content.map((p, i) => {
                                                             // Basic Markdown interpreter for the React View
                                                             if (p.startsWith('#')) return <h3 key={i} style={{ color: '#000E2B', fontSize: '20px', marginTop: '24px', marginBottom: '12px' }}>{p.replace(/#/g, '').trim()}</h3>;
                                                             if (p.startsWith('*')) return <li key={i} style={{ marginLeft: '20px', marginBottom: '8px', color: '#475569' }}>{p.replace(/^\*/, '').trim()}</li>;
                                                             
                                                             return (
                                                                 <div key={i} className="content-segment">
                                                                     <p style={{ lineHeight: '1.6', marginBottom: '16px', color: '#475569' }}>
                                                                         {p.split('**').map((part, idx) => 
                                                                             idx % 2 === 1 ? <strong key={idx} style={{ color: '#20963D' }}>{part}</strong> : part
                                                                         )}
                                                                     </p>
                                                                 </div>
                                                             );
                                                        }),
                                                        [activeLesson.content]
                                                    )}
                                                </div>
                                                <div className="reader-footer-note">
                                                    <i className="fas fa-microchip"></i>
                                                    <span>Verified against Infrastructure v4.3 Standards</span>
                                                </div>
                                            </div>
                                            <div className="reader-actions">
                                                <button className="v4-submit-btn" style={{ background: '#000E2B' }} onClick={closeLesson} disabled={loading}>
                                                    {loading ? <i className="fas fa-spinner fa-spin"></i> : "FINISH STUDY SESSION"}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                     )}
                  </div>
                )}
            </div>
          )}


          {successMsg && (
             <div className="v4-success-alert animate-pop" style={{ marginTop: '20px', padding: '16px', background: '#f0fdf4', border: '1.5px solid #20963D33', borderRadius: '16px', color: '#166534', fontSize: '13px', fontWeight: 700, display: 'flex', gap: '12px', alignItems: 'center' }}>
                <i className="fas fa-check-circle" style={{ fontSize: '18px' }}></i>
                <span>{successMsg}</span>
             </div>
          )}

          <div className="v4-card-footer">
            {tab === 'login' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
                    <p style={{ margin: 0 }}>
                        <span style={{ color: '#64748b', fontSize: '11px', fontWeight: 800, textTransform: 'uppercase' }}>Join the Network: </span>
                        <button onClick={() => setTab('agent-apply')} style={{ background: 'none', border: 'none', color: '#20963D', fontWeight: 900, cursor: 'pointer', textDecoration: 'underline', fontSize: '11px' }}>Apply as Agent</button>
                    </p>
                    <p style={{ margin: 0 }}>
                        <span style={{ color: '#64748b', fontSize: '11px', fontWeight: 800, textTransform: 'uppercase' }}>Continue Training: </span>
                        <button onClick={() => setTab('academy-portal')} style={{ background: 'none', border: 'none', color: '#f59e0b', fontWeight: 900, cursor: 'pointer', textDecoration: 'underline', fontSize: '11px' }}>Agent Academy</button>
                    </p>
                </div>
            )}
            <p>© 2026 ZimAgritrust Marketplace • Platform v4.3</p>
          </div>
        </div>
      </div>

      <style>{`
        .options-grid { display: flex; flex-direction: column; gap: 12px; }
        .v4-opt-btn { width: 100%; padding: 16px; border-radius: 12px; border: 1.5px solid #e2e8f0; background: #fff; text-align: left; font-size: 14px; font-weight: 700; color: #475569; cursor: pointer; transition: all 0.2s; }
        .v4-opt-btn:hover { border-color: #f59e0b; background: #fffcf0; }
        .v4-opt-btn.selected { background: #000E2B; color: #fff; border-color: #000E2B; transform: scale(1.02); }

        .friendly-gradient-text {
          background: linear-gradient(135deg, #000E2B 0%, #20963D 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          font-weight: 1000;
          letter-spacing: -2px;
        }

        .bounce-soft { animation: bounceSoft 3s ease-in-out infinite; }
        @keyframes bounceSoft {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }

        .v4-institutional-title {
          font-size: 32px; 
          font-weight: 950; 
          color: #000E2B; 
          margin-bottom: 8px; 
          letter-spacing: -0.04em; 
          text-transform: uppercase;
        }

        .v4-standard-subtitle { font-size: 16px; font-weight: 700; color: #475569; margin-bottom: 24px; }
        .description-standard { font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 40px; }

        .icon-bg-institutional { width: 80px; height: 80px; border-radius: 16px; background: #000E2B; display: grid; placeItems: center; font-size: 32px; color: #fff; margin: 0 auto 32px; }
        .institutional-audit-box { background: #f1f5f9; padding: 20px; border-radius: 12px; display: flex; gap: 16px; align-items: center; color: #475569; font-size: 13px; text-align: left; border-left: 4px solid #000E2B; }
        .institutional-audit-box i { color: #000E2B; font-size: 20px; }

        .v4-login-page {
          position: fixed;
          inset: 0;
          display: flex;
          align-items: flex-start;
          justify-content: center;
          font-family: 'Outfit', 'Inter', sans-serif;
          background: #020617;
          overflow-y: auto;
          overflow-x: hidden;
          padding: 40px 0;
        }
        .v4-login-background {
          position: absolute;
          inset: 0;
          background-image: url('/ZimAgritrust_professional_hero_1775945205140.png');
          background-size: cover;
          background-position: center;
          filter: brightness(0.4) saturate(1.2) blur(2px);
          transform: scale(1.05);
        }
        .v4-login-container {
          position: relative;
          z-index: 10;
          width: 100%;
          max-width: 460px;
          padding: 24px;
        }
        .v4-login-card {
          background: rgba(255, 255, 255, 0.98);
          backdrop-filter: blur(20px);
          border-radius: 32px;
          padding: 32px;
          box-shadow: 0 40px 80px -20px rgba(0,0,0,0.5);
          border: 1px solid rgba(255,255,255,0.3);
          max-height: 90vh;
          overflow-y: auto;
        }
        .v4-login-header { text-align: center; margin-bottom: 24px; }
        .v4-brand { font-size: 20px; font-weight: 900; color: #000E2B; margin-bottom: 24px; display: flex; align-items: center; justify-content: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.1em; }
        .v4-brand i { color: #20963D; font-size: 24px; }
        .v4-login-header h1 { font-size: 32px; font-weight: 950; color: #000E2B; margin-bottom: 8px; letter-spacing: -0.04em; }
        .v4-subtitle { font-size: 14px; color: #64748b; font-weight: 600; line-height: 1.5; }

        .v4-tabs { display: flex; background: #f1f5f9; padding: 6px; border-radius: 18px; margin-bottom: 32px; }
        .v4-tab { flex: 1; border: none; background: transparent; padding: 10px; border-radius: 14px; font-size: 14px; font-weight: 800; color: #64748b; cursor: pointer; transition: 0.2s; }
        .v4-tab.active { background: #fff; color: #000E2B; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

        .v4-field { margin-bottom: 20px; }
        .v4-field label { display: block; font-size: 11px; font-weight: 900; color: #475569; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.08em; }
        .v4-input-group { position: relative; display: flex; align-items: center; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; transition: 0.3s; }
        .v4-input-group:focus-within { border-color: #20963D; box-shadow: 0 0 0 4px rgba(32, 150, 61, 0.08); }
        .v4-prefix { padding: 0 16px; font-weight: 800; color: #94a3b8; font-size: 14px; border-right: 1.5px solid #f1f5f9; background: #f8fafc; height: 48px; display: grid; place-items: center; }
        .v4-input-group input { flex: 1; border: none; padding: 12px 16px; outline: none; font-size: 15px; font-weight: 700; color: #000E2B; height: 48px; }
        
        .v4-pw-toggle { background: none; border: none; padding: 8px 16px; color: #94a3b8; cursor: pointer; font-size: 14px; }

        .v4-submit-btn { width: 100%; height: 52px; background: #000E2B; color: #fff; border: none; border-radius: 14px; font-size: 14px; font-weight: 900; cursor: pointer; transition: 0.3s; margin-top: 8px; box-shadow: 0 4px 12px rgba(6, 78, 59, 0.2); }
        .v4-submit-btn:hover { background: #065f46; transform: translateY(-1px); box-shadow: 0 8px 16px rgba(6, 78, 59, 0.3); }
        .v4-submit-btn:disabled { opacity: 0.7; transform: none; box-shadow: none; }

        .v4-divider { text-align: center; margin: 20px 0; position: relative; display: flex; align-items: center; justify-content: center; }
        .v4-divider::before { content: ''; position: absolute; left: 0; right: 0; top: 50%; height: 1px; background: #e2e8f0; z-index: 1; }
        .v4-divider span { position: relative; z-index: 2; background: #fff; padding: 0 12px; font-size: 9px; font-weight: 900; color: #94a3b8; }

        .v4-ghost-btn { width: 100%; height: 52px; background: transparent; border: 1.5px solid #f1f5f9; border-radius: 14px; color: #475569; font-size: 13px; font-weight: 900; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .v4-ghost-btn:hover { background: #f8fafc; border-color: #e2e8f0; color: #000E2B; }

        .v4-basic-input { width: 100%; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 12px 16px; outline: none; font-size: 15px; font-weight: 700; color: #000E2B; transition: 0.3s; }
        .v4-basic-input:focus { border-color: #20963D; box-shadow: 0 0 0 4px rgba(32, 150, 61, 0.08); }

        .v4-error-alert { background: #fff1f2; border: 1px solid #fecaca; color: #be123c; padding: 12px 16px; border-radius: 14px; font-size: 13px; font-weight: 700; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
        .v4-card-footer { margin-top: 40px; text-align: center; }
        .v4-card-footer p { font-size: 11px; font-weight: 700; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.05em; }

        .animate-fade-in { animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .slide-down { animation: slideDown 0.3s ease-out; }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}
