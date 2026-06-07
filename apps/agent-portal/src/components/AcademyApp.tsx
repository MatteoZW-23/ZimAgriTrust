import React, { useEffect, useMemo, useState } from "react";
import {
  completeAcademyTopic,
  enrollInAcademyCourse,
  getAcademyCourseDetail,
  getAcademyCourses,
  getAcademyResource,
  getCertificate,
  login,
} from "../api.ts";

const ACADEMY_AUTH_KEY = "zimagritrust_academy_auth";
const NEEDS_ACADEMY_KEY = "zimagritrust_came_from_academy";

function fmtPhone(phone: string) {
  if (phone.startsWith("+")) return phone.replace(/\s/g, "");
  return `+263${phone.replace(/^0+/, "").replace(/\s/g, "")}`;
}

export default function AcademyApp({ onGraduate, onCancel }) {
  const [auth, setAuth] = useState(() => {
    try { return JSON.parse(localStorage.getItem(ACADEMY_AUTH_KEY)); } catch { return null; }
  });
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [detail, setDetail] = useState(null);
  const [resource, setResource] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [notice, setNotice] = useState("");

  const overallProgress = useMemo(() => {
    if (!courses.length) return 0;
    return Math.round(courses.reduce((sum, course) => sum + Number(course.progress_percentage || 0), 0) / courses.length);
  }, [courses]);

  useEffect(() => {
    if (auth?.access_token) loadCourses();
  }, [auth?.access_token]);

  const handleLogin = async (event) => {
    event.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const session = await login(fmtPhone(phoneNumber), password);
      localStorage.setItem(ACADEMY_AUTH_KEY, JSON.stringify(session));
      setAuth(session);
    } catch (error) {
      setErr(error.message || "Unable to enter the Academy");
    } finally {
      setLoading(false);
    }
  };

  const loadCourses = async () => {
    setErr("");
    setLoading(true);
    try {
      const nextCourses = await getAcademyCourses();
      setCourses(nextCourses || []);
      if (!selectedCourse && nextCourses?.length) await openCourse(nextCourses[0]);
    } catch (error) {
      setErr(error.message || "Unable to load academy modules");
    } finally {
      setLoading(false);
    }
  };

  const openCourse = async (course) => {
    setSelectedCourse(course);
    setResource(null);
    setErr("");
    try {
      setDetail(await getAcademyCourseDetail(course.id));
    } catch (error) {
      setDetail(null);
      setErr(error.message || "Unable to open this module");
    }
  };

  const enroll = async (course) => {
    setErr("");
    setNotice("");
    setLoading(true);
    try {
      await enrollInAcademyCourse(course.id);
      setNotice("Enrollment started.");
      await loadCourses();
      await openCourse(course);
    } catch (error) {
      setErr(error.message || "Unable to enroll in this module");
    } finally {
      setLoading(false);
    }
  };

  const completeTopic = async (topic) => {
    setErr("");
    setNotice("");
    setLoading(true);
    try {
      await completeAcademyTopic(topic.id);
      setNotice("Topic completed.");
      await loadCourses();
      if (selectedCourse) await openCourse(selectedCourse);
    } catch (error) {
      setErr(error.message || "Unable to complete this topic");
    } finally {
      setLoading(false);
    }
  };

  const openResource = async (item) => {
    setErr("");
    setResource(null);
    try {
      setResource(await getAcademyResource(item.id));
    } catch (error) {
      setErr(error.message || "Unable to open this lesson resource");
    }
  };

  const checkCertificate = async () => {
    setErr("");
    setNotice("");
    setLoading(true);
    try {
      await getCertificate();
      localStorage.setItem(NEEDS_ACADEMY_KEY, "graduated");
      localStorage.removeItem(ACADEMY_AUTH_KEY);
      onGraduate();
    } catch (error) {
      setErr(error.message || "Complete all Academy modules before certification.");
    } finally {
      setLoading(false);
    }
  };

  if (!auth?.access_token) {
    return (
      <div className="academy-login-shell">
        <div className="academy-login-card">
          <div className="academy-login-brand">
            <img className="academy-login-logo" src="/logo.png" alt="ZimAgriTrust" />
            <div>
              <div className="academy-login-eyebrow">Trainee access</div>
              <h1>Agent Academy</h1>
              <p className="academy-login-sub">Use the phone number and password issued after application approval.</p>
            </div>
          </div>
          {err && <div className="alert alert-error">{err}</div>}
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input className="form-input" placeholder="+263..." value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input className="form-input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            </div>
            <button className="btn btn-primary btn-full btn-lg" disabled={loading}>{loading ? "Entering..." : "Enter Academy"}</button>
            <button type="button" className="btn btn-ghost btn-full" style={{ marginTop: 8 }} onClick={onCancel}>Back to Agent Portal</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="academy-shell">
      <header className="academy-topbar">
        <div className="academy-topbar-brand">
          <img className="academy-topbar-logo" src="/logo.png" alt="ZimAgriTrust" />
          <div>
            <div className="academy-topbar-name">Agent Academy</div>
            <div className="academy-topbar-sub">Training, readiness and certification</div>
          </div>
        </div>
        <div className="academy-phase-indicator">
          <span>{overallProgress}%</span>
          <small>overall progress</small>
        </div>
        <div className="academy-topbar-right">
          <button className="btn btn-primary" onClick={checkCertificate} disabled={loading}>Check Certificate</button>
          <button className="btn btn-ghost" onClick={onCancel}>Portal Login</button>
        </div>
      </header>

      <main className="academy-main">
        <section className="academy-hero">
          <div>
            <div className="eyebrow">Structured trainee path</div>
            <h3>Complete modules in order before full agent access unlocks.</h3>
            <p>Lessons, topic completion and certification are connected to the live classroom backend.</p>
          </div>
          <div className="academy-progress-ring"><span>{overallProgress}%</span></div>
        </section>

        {err && <div className="alert alert-error">{err}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}

        <div className="dashboard-grid">
          <section className="panel">
            <div className="panel-header">
              <h2>Modules</h2>
              <button className="btn btn-ghost" onClick={loadCourses} disabled={loading}>Refresh</button>
            </div>
            <div className="cards-list">
              {courses.map((course) => (
                <button key={course.id} className={`academy-module-card ${course.is_locked ? "locked" : ""}`} onClick={() => openCourse(course)} disabled={course.is_locked}>
                  <div className="academy-module-head">
                    <div>
                      <div className="eyebrow">Module {course.module_number}</div>
                      <div className="card-title">{course.title}</div>
                    </div>
                    <span className="badge">{Math.round(course.progress_percentage || 0)}%</span>
                  </div>
                  <p>{course.description || course.lock_message || "Academy training module"}</p>
                  <div className="academy-progress-bar"><div style={{ width: `${Math.min(100, Math.max(0, course.progress_percentage || 0))}%` }} /></div>
                  {!course.is_locked && Number(course.progress_percentage || 0) === 0 && (
                    <span className="academy-topic-open" onClick={(event) => { event.stopPropagation(); enroll(course); }}>Enroll</span>
                  )}
                </button>
              ))}
              {!courses.length && !loading && <div className="empty-state">No Academy modules are configured yet.</div>}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>{detail?.title || "Module Detail"}</h2>
              {detail && <span className="badge badge-green">{Math.round(detail.progress_percentage || 0)}%</span>}
            </div>
            {detail ? (
              <div className="cards-list">
                {detail.topics?.map((topic) => (
                  <div key={topic.id} className={`academy-topic-row ${topic.is_locked ? "locked" : ""}`}>
                    <div>
                      <strong>{topic.title}</strong>
                      <span>{topic.is_completed ? "Completed" : topic.is_locked ? "Locked" : "Available"}</span>
                      <div className="academy-module-meta">
                        {topic.resources?.map((item) => (
                          <button key={item.id} className="academy-topic-open" disabled={item.is_locked} onClick={() => openResource(item)}>
                            <i className={`fas ${item.resource_type === "quiz" ? "fa-clipboard-question" : "fa-book-open"}`}></i>
                            {item.title}
                          </button>
                        ))}
                      </div>
                    </div>
                    <button className="btn btn-ghost" disabled={topic.is_locked || topic.is_completed || loading} onClick={() => completeTopic(topic)}>
                      {topic.is_completed ? "Done" : "Complete"}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">Select an unlocked module to see lessons.</div>
            )}
          </section>

          {resource && (
            <section className="panel">
              <div className="panel-header">
                <h2>{resource.title}</h2>
                <span className="badge">{resource.resource_type}</span>
              </div>
              {resource.content_text && <p className="lesson-copy">{resource.content_text}</p>}
              {resource.content_url && <a className="btn btn-primary" href={resource.content_url} target="_blank" rel="noreferrer">Open Resource</a>}
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
