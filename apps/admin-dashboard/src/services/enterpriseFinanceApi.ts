import type { PlatformFeeQuoteDto, WalletBalanceDto } from '@agritrust/shared';

const FINTECH_API_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

async function request<T>(path: string, accessToken?: string): Promise<T> {
  const response = await fetch(`${FINTECH_API_URL}${path}`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.message || payload?.detail || `Request failed: ${response.status}`);
  }
  return payload as T;
}

export const enterpriseFinanceApi = {
  revenue(from: Date, to: Date, accessToken?: string) {
    return request<{ total_debits: number; total_credits: number; difference: number; currency: string; is_balanced: boolean }>(
      `/admin/fintech/reconciliation?from=${encodeURIComponent(from.toISOString())}&to=${encodeURIComponent(to.toISOString())}`,
      accessToken,
    );
  },
  settlements(accessToken?: string) {
    return request<{ pending_withdrawals: Array<{ entry_id: string; transaction_id: string; amount: number; currency: string }>; total: number }>(
      '/admin/fintech/transactions/pending-withdrawals',
      accessToken,
    );
  },
  transactions(accessToken?: string) {
    return request<{ transactions: Array<{ entry_id: string; transaction_id: string; type: string; amount: number; currency: string }>; total: number }>(
      '/admin/fintech/transactions/all',
      accessToken,
    );
  },
  walletBalance(accessToken?: string) {
    return request<WalletBalanceDto>('/wallet/balance', accessToken);
  },
  feeQuote(grossMinor: number | string, currency = 'USD', plan = 'BASIC') {
    return request<PlatformFeeQuoteDto>(
      `/payments/fees/quote?grossMinor=${encodeURIComponent(String(grossMinor))}&currency=${currency}&plan=${plan}`,
    );
  },
};
