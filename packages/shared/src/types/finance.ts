export type CurrencyCode = 'USD' | 'ZiG' | 'ZAR' | 'BWP' | 'EUR' | 'GBP';

export type PaymentProviderCode =
  | 'ECOCASH'
  | 'ONEMONEY'
  | 'INNBUCKS'
  | 'ZIPIT'
  | 'BANK_TRANSFER'
  | 'VISA_MASTERCARD';

export type PaymentStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'CANCELLED'
  | 'REFUNDED'
  | 'REVERSED';

export type WalletType =
  | 'USER'
  | 'SUPPLIER'
  | 'ESCROW'
  | 'PLATFORM'
  | 'SUBSCRIPTION_REVENUE';

export type SubscriptionPlanCode = 'BASIC' | 'PRO' | 'ENTERPRISE';

export interface MoneyDto {
  amountMinor: number | string;
  currency: CurrencyCode;
}

export interface PaymentInitiationRequest {
  amount?: MoneyDto;
  amountMinor?: number | string;
  currency?: CurrencyCode;
  provider: PaymentProviderCode;
  payerUserId?: string;
  orderId?: string;
  invoiceId?: string;
  idempotencyKey: string;
  callbackUrl?: string;
  destinationWalletType?: WalletType;
}

export interface PaymentInitiationResponse {
  id?: string;
  paymentId?: string;
  providerReference: string;
  status: PaymentStatus;
  amountMinor?: number | string;
  currency?: CurrencyCode;
  redirectUrl?: string;
  instructions?: string;
}

export interface WalletBalanceDto {
  walletId: string;
  type: WalletType;
  available: MoneyDto;
  pending: MoneyDto;
  ledgerVersion: number;
}

export interface PlatformFeeQuoteDto {
  gross: MoneyDto;
  fee: MoneyDto;
  tax: MoneyDto;
  supplierNet: MoneyDto;
  platformRevenue: MoneyDto;
  plan: SubscriptionPlanCode;
}
