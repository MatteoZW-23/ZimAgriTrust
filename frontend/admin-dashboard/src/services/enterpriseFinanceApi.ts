import type { PlatformFeeQuoteDto, WalletBalanceDto } from '@agritrust/shared';

const FINTECH_API_URL =
  import.meta.env.VITE_FINTECH_API_URL || 'http://localhost:8090/api/v1';

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
    return request<Array<{ grossMinor: string; feeMinor: string; taxMinor: string; netMinor: string; currency: string; count: number }>>(
      `/admin/revenue?from=${encodeURIComponent(from.toISOString())}&to=${encodeURIComponent(to.toISOString())}`,
      accessToken,
    );
  },
  settlements(accessToken?: string) {
    return request<Array<{ id: string; status: string; grossMinor: string; netMinor: string; currency: string }>>('/admin/settlements', accessToken);
  },
  transactions(accessToken?: string) {
    return request<Array<{ id: string; status: string; provider: string; amountMinor: string; currency: string }>>('/admin/transactions', accessToken);
  },
  walletBalance(accessToken?: string) {
    return request<WalletBalanceDto>('/wallets/balance', accessToken);
  },
  feeQuote(grossMinor: number | string, currency = 'USD', plan = 'BASIC') {
    return request<PlatformFeeQuoteDto>(
      `/payments/fees/quote?grossMinor=${encodeURIComponent(String(grossMinor))}&currency=${currency}&plan=${plan}`,
    );
  },
};
