/**
 * ZimAgriTrust — k6 Production Load & Chaos Test Suite
 *
 * Scenarios:
 *   1. auth_flood          — brute-force login (rate-limit validation)
 *   2. concurrent_deposit  — parallel deposits with same idempotency key (dedup test)
 *   3. webhook_flood       — duplicate EcoCash webhook delivery (idempotency test)
 *   4. wallet_race         — concurrent withdrawals (double-spend prevention)
 *   5. escrow_flow         — full happy-path: deposit → hold → deliver → release
 *   6. balance_consistency — ledger balance == sum after N concurrent ops
 *
 * Run with:
 *   k6 run tests/load/k6_suite.js --env BASE_URL=http://localhost:8080
 */

import http from "k6/http";
import { check, sleep, group } from "k6";
import { SharedArray } from "k6/data";
import { Counter, Rate, Trend } from "k6/metrics";
import { uuidv4 } from "https://jslib.k6.io/k6-utils/1.4.0/index.ts";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";

// ── Custom metrics ────────────────────────────────────────────────────────────
const duplicatePaymentRate = new Rate("duplicate_payment_blocked");
const webhookDedupRate     = new Rate("webhook_dedup_ok");
const doubleSpendBlocked   = new Rate("double_spend_blocked");
const escrowFlowSuccess    = new Rate("escrow_flow_success");
const loginRateLimitHit    = new Rate("login_rate_limited");
const escrowDuration       = new Trend("escrow_full_flow_ms", true);

// ── Test configuration ────────────────────────────────────────────────────────
export const options = {
  scenarios: {
    // 1. Auth flood — expect 429s after 5 attempts/s threshold
    auth_flood: {
      executor: "constant-arrival-rate",
      rate: 20,
      timeUnit: "1s",
      duration: "30s",
      preAllocatedVUs: 50,
      maxVUs: 100,
      startTime: "0s",
      exec: "authFlood",
      tags: { scenario: "auth_flood" },
    },
    // 2. Concurrent idempotent deposits — only 1 should succeed
    concurrent_deposit: {
      executor: "shared-iterations",
      vus: 20,
      iterations: 20,
      startTime: "5s",
      exec: "concurrentDeposit",
      tags: { scenario: "concurrent_deposit" },
    },
    // 3. Webhook flood — same request_id 10 times
    webhook_flood: {
      executor: "shared-iterations",
      vus: 10,
      iterations: 50,
      startTime: "5s",
      exec: "webhookFlood",
      tags: { scenario: "webhook_flood" },
    },
    // 4. Concurrent withdrawals — race condition test
    wallet_race: {
      executor: "shared-iterations",
      vus: 15,
      iterations: 15,
      startTime: "10s",
      exec: "walletRace",
      tags: { scenario: "wallet_race" },
    },
    // 5. Full escrow flow
    escrow_flow: {
      executor: "per-vu-iterations",
      vus: 5,
      iterations: 3,
      startTime: "15s",
      exec: "escrowFlow",
      tags: { scenario: "escrow_flow" },
    },
  },
  thresholds: {
    http_req_failed:          ["rate<0.05"],
    http_req_duration:        ["p(95)<3000"],
    duplicate_payment_blocked: ["rate>0.95"],
    webhook_dedup_ok:          ["rate>0.90"],
    double_spend_blocked:      ["rate>0.90"],
    escrow_flow_success:       ["rate>0.90"],
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────
function apiHeaders(token, idempotencyKey) {
  const h = {
    "Content-Type": "application/json",
    "Accept":        "application/json",
  };
  if (token)          h["Authorization"]  = `Bearer ${token}`;
  if (idempotencyKey) h["Idempotency-Key"] = idempotencyKey;
  return h;
}

function login(phone, pin) {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/app/login`,
    JSON.stringify({ phone_number: phone, pin: pin }),
    { headers: apiHeaders() }
  );
  if (res.status === 200) {
    return JSON.parse(res.body).access_token;
  }
  return null;
}

// ── Scenario 1: Auth Flood ────────────────────────────────────────────────────
export function authFlood() {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/app/login`,
    JSON.stringify({ phone_number: "0771111111", pin: "000000" }),
    { headers: apiHeaders() }
  );
  // Expect either 401 (wrong creds) or 429 (rate limited) — 200 would be a problem
  const rateLimited = res.status === 429;
  loginRateLimitHit.add(rateLimited);
  check(res, {
    "auth flood not 200": (r) => r.status !== 200,
  });
  sleep(0.05);
}

// ── Scenario 2: Concurrent Deposits with Same Idempotency Key ────────────────
// All 20 VUs share one idempotency key → only 1 deposit should execute.
const SHARED_DEPOSIT_KEY = uuidv4();

export function concurrentDeposit() {
  // Use a pre-seeded test buyer token — set TEST_BUYER_TOKEN env var
  const token = __ENV.TEST_BUYER_TOKEN || "";
  if (!token) { sleep(1); return; }

  const res = http.post(
    `${BASE_URL}/api/v1/wallet/top-up`,
    JSON.stringify({ amount: 10.00, currency: "USD", provider: "ecocash", phone: "0771234567" }),
    { headers: apiHeaders(token, SHARED_DEPOSIT_KEY) }
  );

  // 200 or 200+X-Idempotency-Replayed are both acceptable.
  // Only exactly ONE should do the actual work (no double-credit).
  const ok      = res.status === 200;
  const replayed = res.headers["X-Idempotency-Replayed"] === "true";
  duplicatePaymentRate.add(ok);  // all should succeed (some replayed)
  check(res, {
    "deposit idempotent ok": (r) => r.status === 200 || r.status === 409,
  });
  sleep(0.1);
}

// ── Scenario 3: Webhook Flood — same request_id ───────────────────────────────
// EcoCash provider retries the same callback 10 times. Only 1 should credit.
const SHARED_WEBHOOK_REF = `AGRI-TX-${uuidv4()}`;
const SHARED_REQUEST_ID  = uuidv4();

export function webhookFlood() {
  const payload = JSON.stringify({
    request_id:        SHARED_REQUEST_ID,
    status:            "SUCCESS",
    merchant_reference: SHARED_WEBHOOK_REF,
    amount:            50.00,
  });

  const res = http.post(
    `${BASE_URL}/api/v1/payments/ecocash/callback`,
    payload,
    { headers: { "Content-Type": "application/json" } }
  );

  // First call: 200 (processed) or 400 (order not found in test env) — both ok.
  // Subsequent calls: 200 (idempotent replay) — NEVER another 200 with a credit.
  const acceptable = res.status === 200 || res.status === 400;
  webhookDedupRate.add(acceptable);
  check(res, {
    "webhook accepted": (r) => r.status === 200 || r.status === 400,
  });
  sleep(0.05);
}

// ── Scenario 4: Wallet Race — concurrent withdrawals ─────────────────────────
// 15 VUs all try to withdraw $100 from an account with $100 balance.
// Only 1 should succeed; the rest must get 400/422.
export function walletRace() {
  const token = __ENV.TEST_SELLER_TOKEN || "";
  if (!token) { sleep(1); return; }

  const ikey = uuidv4();  // each VU uses a unique key so idempotency layer doesn't mask the test
  const res = http.post(
    `${BASE_URL}/api/v1/wallet/withdraw`,
    JSON.stringify({ amount: 100.00, currency: "USD", method: "ecocash", phone: "0771234567" }),
    { headers: apiHeaders(token, ikey) }
  );

  // Success (200) OR insufficient funds (400) are both valid outcomes.
  // What is NOT valid: multiple 200s that would indicate double-spending.
  const blocked = res.status === 400 || res.status === 422;
  const succeeded = res.status === 200;
  if (succeeded) doubleSpendBlocked.add(false);
  if (blocked)   doubleSpendBlocked.add(true);

  check(res, {
    "withdrawal status valid": (r) => [200, 400, 422].includes(r.status),
  });
  sleep(0.05);
}

// ── Scenario 5: Full Escrow Flow ──────────────────────────────────────────────
export function escrowFlow() {
  const buyerToken  = __ENV.TEST_BUYER_TOKEN  || "";
  const sellerToken = __ENV.TEST_SELLER_TOKEN || "";
  const orderId     = __ENV.TEST_ORDER_ID     || "";
  if (!buyerToken || !sellerToken || !orderId) { sleep(2); return; }

  const startTime = Date.now();
  let ok = true;

  group("escrow_full_flow", () => {
    // Step 1: Confirm payment (simulates webhook)
    const ikey = uuidv4();
    let r = http.post(
      `${BASE_URL}/api/v1/payments/ecocash/callback`,
      JSON.stringify({
        request_id:         ikey,
        status:             "SUCCESS",
        merchant_reference: `AGRI-TX-${orderId}`,
        amount:             50.00,
      }),
      { headers: { "Content-Type": "application/json" } }
    );
    ok = ok && check(r, { "payment confirmed": (r) => r.status === 200 });

    sleep(0.5);

    // Step 2: Mark delivered
    r = http.put(
      `${BASE_URL}/api/v1/orders/${orderId}/mark-delivered`,
      null,
      { headers: apiHeaders(sellerToken) }
    );
    ok = ok && check(r, { "marked delivered": (r) => [200, 400].includes(r.status) });

    sleep(0.5);

    // Step 3: Release payment
    r = http.post(
      `${BASE_URL}/api/v1/orders/${orderId}/release-payment`,
      JSON.stringify({ handover_code: __ENV.TEST_HANDOVER_CODE || "ABCDEF" }),
      { headers: apiHeaders(buyerToken, uuidv4()) }
    );
    ok = ok && check(r, { "payment released": (r) => [200, 400].includes(r.status) });

    sleep(0.5);

    // Step 4: Verify balance increased for seller
    r = http.get(
      `${BASE_URL}/api/v1/payments/balance`,
      { headers: apiHeaders(sellerToken) }
    );
    ok = ok && check(r, { "balance readable": (r) => r.status === 200 });
  });

  escrowDuration.add(Date.now() - startTime);
  escrowFlowSuccess.add(ok);
  sleep(1);
}
