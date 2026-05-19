/**
 * ZimAgritrust Agent Portal – API Client
 * All endpoints used by field agents.
 */
const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export async function request(path, options = {}) {
  let storedAuth = null;
  // Read token from whichever session is active (academy takes priority if present)
  try { storedAuth = JSON.parse(localStorage.getItem("zimagritrust_academy_auth")); } catch {}
  if (!storedAuth?.access_token) {
    try { storedAuth = JSON.parse(localStorage.getItem("zimagritrust_agent_auth")); } catch {}
  }
  const token = storedAuth?.access_token;
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const res = await fetch(`${API}${path}`, { ...options, headers, credentials: "include" });
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : null;
  if (!res.ok) {
    const msg = data?.detail
      ? typeof data.detail === "string" ? data.detail
        : Array.isArray(data.detail) ? data.detail.map(e => `${e.loc?.join(".")}: ${e.msg}`).join(", ")
        : JSON.stringify(data.detail)
      : "Request failed";
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (phone_number, password) =>
  request("/agent/login", { method: "POST", body: JSON.stringify({ phone_number, password }) });
export const academyLogin = (agent_code, pin) =>
  request("/academy/login", { method: "POST", body: JSON.stringify({ agent_code, pin }) });
export const verifyOtp = (phone_number, otp) =>
  request("/agent/verify-mfa", { method: "POST", body: JSON.stringify({ phone_number, otp }) });
export const getProfile = () => request("/auth/me");
export const updateProfile = (payload) =>
  request("/auth/profile", { method: "PATCH", body: JSON.stringify(payload) });
export const logout = () => request("/auth/logout", { method: "POST" }).catch(() => {});
export const checkApplicationStatus = (phone_number) =>
  request(`/recruitment/my-status/${encodeURIComponent(phone_number)}`);

// ── KYC / ID Verification Queue ───────────────────────────────────────────────
export const getVerificationQueue = (status = "pending") =>
  request(`/verification/queue?status=${status}`);
export const approveVerification = (requestId, note = "Documents verified and approved.") =>
  request(`/verification/${requestId}/approve?note=${encodeURIComponent(note)}`, { method: "POST" });
export const rejectVerification = (requestId, note) => {
  const form = new FormData();
  form.append("note", note);
  return request(`/verification/${requestId}/reject`, { method: "POST", body: form });
};

// ── Listing Review Queue ──────────────────────────────────────────────────────
export const getReviewQueue = () => request("/admin/listings/review-queue");
export const verifyListing = (listingId, approved) =>
  request(`/admin/listings/${listingId}/verify?approved=${approved}`, { method: "POST" });

// ── Disputes (Mediation) ──────────────────────────────────────────────────────
export const getMyDisputes = () => request("/disputes");
export const submitDisputeRecommendation = (disputeId, payload) =>
  request(`/disputes/${disputeId}/recommend`, { method: "POST", body: JSON.stringify(payload) });

// ── Logistics Controls ────────────────────────────────────────────────────────
export const getDeliveryStatus = (orderId) => request(`/logistics/orders/${orderId}/delivery`);
export const markPickupInProgress = (orderId) =>
  request(`/logistics/orders/${orderId}/delivery/pickup-in-progress`, { method: "POST" });
export const confirmPickup = (orderId, payload = {}) =>
  request(`/logistics/orders/${orderId}/delivery/confirm-pickup`, { method: "POST", body: JSON.stringify(payload) });
export const markDeliveryArrived = (orderId) =>
  request(`/logistics/orders/${orderId}/delivery/arrived`, { method: "POST" });
export const confirmDeliveryByAgent = (orderId, payload = {}) =>
  request(`/logistics/orders/${orderId}/delivery/confirm-delivery`, { method: "POST", body: JSON.stringify(payload) });
export const markDeliveryDelayed = (orderId, new_eta = null) =>
  request(`/logistics/orders/${orderId}/delivery/delay`, { method: "POST", body: JSON.stringify({ new_eta }) });

// ── Trade Negotiations (Read-only mediation access) ───────────────────────────
export const getTradeSessions = () => request("/trades/sessions");
export const getTradeMessages = (sessionId) => request(`/trades/${sessionId}/messages`);
export const sendTradeMessage = (sessionId, payload) =>
  request(`/trades/${sessionId}/messages`, { method: "POST", body: JSON.stringify(payload) });

// ── Agent Tasks (Assignments) ─────────────────────────────────────────────────
export const getMyTasks = () => request("/agent/tasks");
export const acceptTask = (taskId) => request(`/agent/tasks/${taskId}/accept`, { method: "POST" });
export const rejectTask = (taskId, reason) => request(`/agent/tasks/${taskId}/reject`, { method: "POST", body: JSON.stringify({ reason }) });
export const submitVerificationReport = (taskId, payload) => request(`/agent/tasks/${taskId}/report`, { method: "POST", body: JSON.stringify(payload) });
export const getAgentPerformance = () => request("/agent/performance");

export const getAllListings = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/listings${qs ? `?${qs}` : ""}`);
};
export const getMyOrders = () => request("/transactions");
export const getMarketPrices = () =>
  request("/market/prices/current").catch(() => request("/market/summary"));

// ── Earnings / Wallet ─────────────────────────────────────────────────────────
export const getWalletBalance = () => request("/payments/balance");
export const getTransactions = () => request("/transactions");
export const getAgentEarnings = () => request("/agent/earnings").catch(() => request("/payments/balance"));
export const getAgentEarningsBreakdown = () => request("/agent/earnings");

// ── Practical Assessment (post-final-exam) ────────────────────────────────────
export const submitGradingTest = (payload) =>
  request("/agents/practical/grading-test", { method: "POST", body: JSON.stringify(payload) });
export const submitAppNavTest = (payload) =>
  request("/agents/practical/app-test", { method: "POST", body: JSON.stringify(payload) });
export const submitPhotoTest = (payload) =>
  request("/agents/practical/photo-test", { method: "POST", body: JSON.stringify(payload) });
export const submitDisputeRoleplay = (payload) =>
  request("/agents/practical/dispute-roleplay", { method: "POST", body: JSON.stringify(payload) });
export const getPracticalResults = () => request("/agents/practical/results");

// ── Shadowing (10 tasks with senior agent) ────────────────────────────────────
export const getShadowingTasks = () => request("/agents/shadowing/tasks");
export const createShadowingLog = (payload) =>
  request("/agents/shadowing", { method: "POST", body: JSON.stringify(payload) });
export const completeShadowing = (logId, payload) =>
  request(`/agents/shadowing/${logId}/complete`, { method: "POST", body: JSON.stringify(payload) });

// ── Supervised Independent (20 tasks reviewed) ───────────────────────────────
export const getSupervisedTasks = () => request("/agents/supervised/tasks");
export const submitSupervisedTask = (taskId, payload) =>
  request(`/agents/supervised/${taskId}/submit`, { method: "POST", body: JSON.stringify(payload) });
export const reviewSupervisedTask = (reviewId, payload) =>
  request(`/agents/supervised/${reviewId}/review`, { method: "POST", body: JSON.stringify(payload) });

// ── Application resubmit (after rejection) ────────────────────────────────────
export const resubmitApplication = (payload) =>
  request("/agents/application/resubmit", { method: "POST", body: JSON.stringify(payload) });

// ── Recruitment Pipeline (unified onboarding) ─────────────────────────────────
export const submitAgentApplication = (payload) =>
  request("/recruitment/apply", { method: "POST", body: JSON.stringify(payload) });
export const getApplicationStatusByPhone = (phone_number) =>
  request(`/recruitment/my-status/${encodeURIComponent(phone_number)}`);

// ── Academy / Classroom ───────────────────────────────────────────────────────
export const getAcademyCourses = () => request("/agent/classroom/courses");
export const getAcademyCourseDetail = (courseId) => request(`/agent/classroom/courses/${courseId}`);
export const enrollInAcademyCourse = (courseId) =>
  request(`/agent/classroom/courses/${courseId}/enroll`, { method: "POST" });
export const completeAcademyTopic = (topicId) =>
  request(`/agent/classroom/topics/${topicId}/complete`, { method: "POST" });
export const startAcademyQuiz = (resourceId) =>
  request(`/agent/classroom/quizzes/${resourceId}/start`, { method: "POST" });
export const submitAcademyQuiz = (resourceId, answers) =>
  request(`/agent/classroom/quizzes/${resourceId}/submit`, { method: "POST", body: JSON.stringify({ answers }) });
export const getAcademyProgress = () => request("/agent/classroom/progress");

// ── Academy Certification ──────────────────────────────────────────────────────
export const getAcademyMyProgress = () => request("/academy/my-progress");
export const submitFinalExam = (answers) =>
  request("/academy/exam/final/submit", { method: "POST", body: JSON.stringify({ answers }) });

export async function getCertificate() {
  let storedAuth = null;
  try { storedAuth = JSON.parse(localStorage.getItem("zimagritrust_academy_auth")); } catch {}
  if (!storedAuth?.access_token) {
    try { storedAuth = JSON.parse(localStorage.getItem("zimagritrust_agent_auth")); } catch {}
  }
  const token = storedAuth?.access_token;
  const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";
  const res = await fetch(`${API}/agent/classroom/certificate`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: "include",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data?.detail || "Certificate not available yet");
  }
  const html = await res.text();
  // Open the HTML certificate in a new tab
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  return { certificate_url: url };
}
