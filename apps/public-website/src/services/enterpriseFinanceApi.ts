import type {
  PaymentInitiationRequest,
  PaymentInitiationResponse,
  PlatformFeeQuoteDto,
  WalletBalanceDto,
} from '@agritrust/shared';

const FINTECH_API_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

async function request<T>(path: string, init?: RequestInit & { accessToken?: string; idempotencyKey?: string }): Promise<T> {
  const { accessToken, idempotencyKey, ...fetchInit } = init || {};
  const response = await fetch(`${FINTECH_API_URL}${path}`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
      ...(init?.headers || {}),
    },
    ...fetchInit,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.message || payload?.detail || `Request failed: ${response.status}`);
  }
  return payload as T;
}

export const enterpriseFinanceApi = {
  initiatePayment(payload: PaymentInitiationRequest, accessToken?: string) {
    const amountMinor = payload.amountMinor ?? payload.amount?.amountMinor;
    const currency = payload.currency ?? payload.amount?.currency;
    return request<PaymentInitiationResponse>('/payments/initiate', {
      method: 'POST',
      idempotencyKey: payload.idempotencyKey,
      accessToken,
      body: JSON.stringify({
        provider: payload.provider,
        amountMinor,
        currency,
        orderId: payload.orderId,
        invoiceId: payload.invoiceId,
        callbackUrl: payload.callbackUrl,
        destinationWalletType: payload.destinationWalletType ?? 'USER',
      }),
    });
  },

  getWalletBalance(accessToken?: string) {
    return request<WalletBalanceDto>('/wallet/balance', { accessToken });
  },

  quotePlatformFee(grossMinor: number | string, currency = 'USD', plan = 'BASIC') {
    return request<PlatformFeeQuoteDto>(
      `/payments/fees/quote?grossMinor=${encodeURIComponent(String(grossMinor))}&currency=${currency}&plan=${plan}`,
    );
  },
};
