import React, { useState } from "react";
import "./styles.css";
import { getProfile, logout } from "./api.ts";
import AgentApplicationWizard from "./components/AgentApplicationWizard";
import AuthScreen from "./components/AuthScreen";
import Dashboard from "./components/Dashboard";
import KYCPanel from "./components/KYCPanel";
import ListingReviewPanel from "./components/ListingReviewPanel";
import DisputesPanel from "./components/DisputesPanel";
import DeliveryPanel from "./components/DeliveryPanel";
import TasksPanel from "./components/TasksPanel";
import EarningsPanel from "./components/EarningsPanel";
import PerformancePanel from "./components/PerformancePanel";
import PracticalAssessmentPanel from "./components/PracticalAssessmentPanel";
import ShadowingPanel from "./components/ShadowingPanel";
import SupervisedPanel from "./components/SupervisedPanel";

const AUTH_KEY = "zimagritrust_agent_auth";
const USER_KEY = "zimagritrust_agent_user";
const NEEDS_ACADEMY_KEY = "zimagritrust_came_from_academy";

// -- Navigation Bar ----------------------------------------------------------
const NAV = [
  { id: "dashboard", icon: "fa-home", label: "Dashboard" },
  { id: "tasks", icon: "fa-tasks", label: "My Tasks" },
  { id: "kyc", icon: "fa-id-card", label: "KYC Queue" },
  { id: "listings", icon: "fa-list", label: "Listing Review" },
  { id: "disputes", icon: "fa-flag", label: "Disputes" },
  { id: "delivery", icon: "fa-truck", label: "Delivery" },
  { id: "practical", icon: "fa-clipboard-check", label: "Practical Assessment" },
  { id: "shadowing", icon: "fa-eye", label: "Shadowing" },
  { id: "supervised", icon: "fa-user-graduate", label: "Supervised" },
  { id: "earnings", icon: "fa-wallet", label: "Earnings" },
  { id: "performance", icon: "fa-chart-line", label: "Performance" },
];

export default function App() {
  const [auth, setAuth] = useState(() => { try { return JSON.parse(localStorage.getItem(AUTH_KEY)); } catch { return null; } });
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } });
  const [view, setView] = useState("dashboard");
  // Show standalone Academy for unauthenticated trainees or trainees who land here
  const [showAcademy, setShowAcademy] = useState(false);

  const handleLogin = d => {
    const u = d?.user || d;
    setAuth(d); setUser(u);
    setView("dashboard");
    localStorage.setItem(AUTH_KEY, JSON.stringify(d));
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    getProfile().then(p => { setUser(p); localStorage.setItem(USER_KEY, JSON.stringify(p)); }).catch(() => { });
  };

  // Called when a trainee graduates from AcademyApp — they now log in to the full portal
  const handleLogout = () => {
    logout(); setAuth(null); setUser(null);
    localStorage.removeItem(AUTH_KEY); localStorage.removeItem(USER_KEY);
  };

  // Pre-auth: public application wizard at /apply or ?apply=1
  const url = typeof window !== "undefined" ? window.location : { pathname: "", search: "" };
  const wantsApply = url.pathname.startsWith("/apply") || url.search.includes("apply=1");
  if (wantsApply && !auth) {
    return (
      <AgentApplicationWizard
        onCancel={() => { window.location.href = "/"; }}
        onSuccess={() => { }}
      />
    );
  }

  // If Academy session is active (or user chose Academy), show standalone Academy
  if (!auth) return (
    <>
      <AuthScreen onLogin={handleLogin} />
      <div style={{ position: "fixed", bottom: 16, left: 0, right: 0, textAlign: "center", fontSize: 13, color: "#94a3b8" }}>
        <span
          onClick={() => { window.location.href = "https://academy.zimagritrust.com"; }}
          style={{ color: "#10b981", fontWeight: 700, cursor: "pointer", marginRight: 16 }}
        >
          <i className="fas fa-graduation-cap" style={{ marginRight: 4 }}></i> Enter Academy (Trainees)
        </span>
        ·{" "}
        <a href="?apply=1" style={{ color: "#94a3b8", marginLeft: 8 }}>Apply to become an agent</a>
      </div>
    </>
  );

  // Trainees (status === "trainee") must complete the Academy before accessing the portal
  const agentStatus = (user?.agent_status || user?.status || "").toLowerCase();
  if (auth && agentStatus === "trainee") {
    window.location.href = "https://academy.zimagritrust.com";
    return null;
  }

  // Graduated trainees: show a portal login prompt (their status is now "active")
  const cameFromAcademy = localStorage.getItem(NEEDS_ACADEMY_KEY) === "graduated";
  if (!auth && cameFromAcademy) {
    return (
      <div className="auth-screen">
        <div className="auth-card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 56, marginBottom: 16 }}>🎓</div>
          <h2 style={{ color: "var(--text)", marginBottom: 8 }}>Academy Complete!</h2>
          <p style={{ color: "var(--text-dim)", marginBottom: 24 }}>You are now a Certified ZimAgritrust Field Agent. Log in below to access the full Agent Portal.</p>
          <AuthScreen onLogin={(d) => { localStorage.removeItem(NEEDS_ACADEMY_KEY); handleLogin(d); }} />
        </div>
      </div>
    );
  }

  const role = (user?.role || "").toLowerCase();
  if (role && role !== "agent") return (
    <div className="auth-screen"><div className="auth-card">
      <h1>Access Denied</h1><p>This portal is for certified ZimAgritrust field agents only.</p>
      <button className="btn btn-primary btn-full" onClick={handleLogout}>Log Out</button>
    </div></div>
  );

  const renderView = () => {
    switch (view) {
      case "tasks": return <TasksPanel />;
      case "kyc": return <KYCPanel />;
      case "listings": return <ListingReviewPanel />;
      case "disputes": return <DisputesPanel />;
      case "delivery": return <DeliveryPanel />;
      case "practical": return <PracticalAssessmentPanel />;
      case "shadowing": return <ShadowingPanel user={user} />;
      case "supervised": return <SupervisedPanel />;
      case "earnings": return <EarningsPanel />;
      case "performance": return <PerformancePanel user={user} />;
      default: return <Dashboard user={user} />;
    }
  };

  const initials = (user?.full_name || "A").split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="app-container">
      <nav className="sidebar">
        <div className="sidebar-brand" style={{ padding: '20px 16px 16px', borderBottom: '1px solid var(--border)' }}>
          <img src="/logo.png" alt="ZimAgriTrust" style={{ height: '32px', width: 'auto' }} onError={e => { e.target.style.display = 'none'; }} />
          <div>
            <div className="name">Agent Portal</div>
            <div className="tagline">ZimAgriTrust</div>
          </div>
        </div>
        <div className="sidebar-menu">
          {NAV.map(n => (
            <button key={n.id} className={`sidebar-item${view === n.id ? " active" : ""}`} onClick={() => setView(n.id)}>
              <i className={`fas ${n.icon}`}></i> {n.label}
            </button>
          ))}
        </div>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{initials}</div>
            <div>
              <div className="user-name">{user?.full_name || "Agent"}</div>
              <div className="user-role">Field Agent · Score: {user?.trust_score ?? "—"}</div>
            </div>
          </div>
          <button className="btn btn-ghost btn-full" onClick={handleLogout}><i className="fas fa-sign-out-alt"></i> Logout</button>
        </div>
      </nav>
      <main className="main-content">{renderView()}</main>
    </div>
  );
}
