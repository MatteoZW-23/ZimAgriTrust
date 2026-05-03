/**
 * ZimAgritrust Agent Portal – API Client
 * All endpoints used by field agents.
 */
const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

export async function request(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
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
  request("/auth/login", { method: "POST", body: JSON.stringify({ phone_number, password }) });

export const verifyOtp = (phone_number, otp) =>
  request("/auth/verify-login-2fa", { method: "POST", body: JSON.stringify({ phone_number, otp }) });

export const forgotPassword = (phone_number) =>
  request("/auth/forgot-password", { method: "POST", body: JSON.stringify({ phone_number }) });

export const resetPassword = (phone_number, otp, new_password) =>
  request("/auth/reset-password", { method: "POST", body: JSON.stringify({ phone_number, otp, new_password }) });

export const getProfile = () => request("/auth/me");

export const updateProfile = (payload) =>
  request("/auth/profile", { method: "PATCH", body: JSON.stringify(payload) });

export const logout = () =>
  request("/auth/logout", { method: "POST" }).catch(() => {});

// ── Agent Tasks ───────────────────────────────────────────────────────────────
export const getMyTasks = () => request("/agent/tasks");

export const acceptTask = (taskId) =>
  request(`/agent/tasks/${taskId}/accept`, { method: "POST" });

export const rejectTask = (taskId, reason) =>
  request(`/agent/tasks/${taskId}/reject`, { method: "POST", body: JSON.stringify({ reason }) });

export const submitVerificationReport = (taskId, payload) =>
  request(`/agent/tasks/${taskId}/report`, { method: "POST", body: JSON.stringify(payload) });

// ── Verification Queue ────────────────────────────────────────────────────────
export const getVerificationQueue = (status = "pending") =>
  request(`/verification/queue?status=${status}`);

export const approveVerification = (requestId, note = "Approved") =>
  request(`/verification/${requestId}/approve?note=${encodeURIComponent(note)}`, { method: "POST" });

export const rejectVerification = (requestId, note) => {
  const form = new FormData();
  form.append("note", note);
  return request(`/verification/${requestId}/reject`, { method: "POST", body: form });
};

// ── Disputes ──────────────────────────────────────────────────────────────────
export const getMyDisputes = () => request("/disputes");

export const submitDisputeRecommendation = (disputeId, payload) =>
  request(`/disputes/${disputeId}/recommend`, { method: "POST", body: JSON.stringify(payload) });

// ── Listings (review) ─────────────────────────────────────────────────────────
export const getReviewQueue = () => request("/admin/listings/review-queue");

export const verifyListing = (listingId, approved) =>
  request(`/admin/listings/${listingId}/verify?approved=${approved}`, { method: "POST" });

// ── Market ────────────────────────────────────────────────────────────────────
export const getMarketActivities = () => request("/admin/activities");

export const getAllListings = () => request("/listings");

export const getMyOrders = () => request("/orders");

export const getAllUsers = () => request("/admin/users");

// ── Messaging ─────────────────────────────────────────────────────────────────
export const getTradeSessions = () => request("/trades/sessions");

export const getTradeMessages = (sessionId) => request(`/trades/${sessionId}/messages`);

export const sendTradeMessage = (sessionId, payload) =>
  request(`/trades/${sessionId}/messages`, { method: "POST", body: JSON.stringify(payload) });

// ── Earnings ──────────────────────────────────────────────────────────────────
export const getWalletBalance = () => request("/payments/balance");

export const getTransactions = () => request("/transactions");

// ── Academy ───────────────────────────────────────────────────────────────────
export const getAcademyProgress = () => request("/academy/my-progress");

export const getTopicContent = (moduleId, topicId) =>
  request(`/academy/modules/${moduleId}/topics/${topicId}/content`);

export const markTopicComplete = (moduleId, topicId) =>
  request(`/academy/modules/${moduleId}/topics/${topicId}/complete`, { method: "POST" });

export const academyLogin = (agent_code, pin) =>
  request("/academy/login", { method: "POST", body: JSON.stringify({ agent_code, pin }) });
