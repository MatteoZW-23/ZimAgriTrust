const API = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

async function get(path) {
  const res = await fetch(`${API}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function getPublicListings(params = {}) {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null))
  ).toString();
  // Try public endpoint first, fall back to general listings
  try {
    return await get(`/public/listings${q ? `?${q}` : ""}`);
  } catch {
    return get(`/listings${q ? `?${q}` : ""}`);
  }
}

export async function getPublicListing(id) {
  try {
    return await get(`/public/listings/${id}`);
  } catch {
    return get(`/listings/${id}`);
  }
}

export async function getMarketPrices() {
  try {
    return await get("/public/prices/current");
  } catch {
    return get("/market/summary");
  }
}

export async function getTrendingCrops() {
  try {
    return await get("/public/prices/trending");
  } catch {
    return get("/market/pulse");
  }
}

export async function getPlatformStats() {
  try {
    return await get("/public/stats");
  } catch {
    return get("/admin/overview");
  }
}

export async function getPublicNews() {
  return get("/public/news");
}

export async function getPublicWeather() {
  return get("/public/weather");
}

export async function getSeasonalCalendar() {
  return get("/public/calendar");
}

export async function searchPublicListings(params = {}) {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null))
  ).toString();
  try {
    return await get(`/listings/search${q ? `?${q}` : ""}`);
  } catch {
    return get(`/listings${q ? `?${q}` : ""}`);
  }
}

export async function getPublicFeePreview(amount, currency = 'USD', transportFee = 0) {
  const q = new URLSearchParams({ amount: String(amount), currency, transport_fee: String(transportFee) }).toString();
  return get(`/public/fee-preview?${q}`);
}
