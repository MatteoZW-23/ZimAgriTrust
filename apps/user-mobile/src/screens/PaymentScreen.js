import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  SafeAreaView, ActivityIndicator, Alert, Animated
} from 'react-native';
import { getFeePreview, initiatePayment, getPaymentStatus } from '../api';
import { theme } from '../styles';

const METHODS = [
  {
    id: 'ecocash',
    label: 'EcoCash',
    icon: '📱',
    desc: 'Pay using your EcoCash wallet',
    recommended: true,
    ussd: '*151#',
    limit: '$500 max',
  },
  {
    id: 'onemoney',
    label: 'OneMoney',
    icon: '💳',
    desc: 'Pay using OneMoney',
    ussd: '*111#',
    limit: '$500 max',
  },
  {
    id: 'bank',
    label: 'Bank Transfer',
    icon: '🏦',
    desc: 'CBZ / NMB / Steward Bank (1-2 days)',
    limit: '$10,000 max',
  },
  {
    id: 'cash_agent',
    label: 'Cash via Agent',
    icon: '🤝',
    desc: 'Pay cash to nearest ZimAgritrust agent',
    limit: 'Any amount',
  },
];

// ─── Step 1: Method selection + fee preview ───────────────────────────────────
function SelectMethodStep({ order, token, onPay }) {
  const [method, setMethod] = useState('ecocash');
  const [fees, setFees] = useState(null);
  const [loadingFees, setLoadingFees] = useState(true);
  const [paying, setPaying] = useState(false);

  useEffect(() => {
    if (!order?.total_amount) return;
    getFeePreview(token, order.total_amount, order.currency || 'USD')
      .then(setFees)
      .catch(() => setFees(null))
      .finally(() => setLoadingFees(false));
  }, [order, token]);

  const handlePay = async () => {
    setPaying(true);
    try {
      const result = await initiatePayment(token, {
        order_id: order.id,
        payment_method: method,
        phone_number: order.buyer_phone,
      });
      onPay(result, method);
    } catch (err) {
      Alert.alert('Payment Error', err.message || 'Failed to initiate payment. Please try again.');
    } finally {
      setPaying(false);
    }
  };

  const totalToPay = fees?.buyer_pays?.total || order?.total_amount || 0;
  const currency = fees?.currency || order?.currency || 'USD';

  return (
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
      {/* Order Summary */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>📋 Order Summary</Text>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Product</Text>
          <Text style={styles.summaryVal}>{order?.product || '--'}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Quantity</Text>
          <Text style={styles.summaryVal}>{order?.quantity ? `${Number(order.quantity).toLocaleString()} kg` : '—'}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Order Amount</Text>
          <Text style={styles.summaryVal}>{currency === 'USD' ? '$' : currency + ' '}{Number(order?.total_amount || 0).toFixed(2)}</Text>
        </View>

        <View style={styles.divider} />

        {loadingFees ? (
          <ActivityIndicator color={theme.colors.green} style={{ marginVertical: 12 }} />
        ) : fees ? (
          <>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Escrow fee ({fees.buyer_pays.escrow_fee_rate})</Text>
              <Text style={styles.summaryVal}>+${fees.buyer_pays.escrow_fee.toFixed(2)}</Text>
            </View>
            <View style={[styles.summaryRow, styles.totalRow]}>
              <Text style={styles.totalLabel}>Total to Pay</Text>
              <Text style={styles.totalVal}>${totalToPay.toFixed(2)}</Text>
            </View>
          </>
        ) : null}

        <View style={styles.escrowBadge}>
          <Text style={styles.escrowBadgeText}>🛡️ Funds held in escrow until delivery confirmed</Text>
        </View>
      </View>

      {/* Payment Method */}
      <Text style={styles.sectionLabel}>SELECT PAYMENT METHOD</Text>
      {METHODS.map((m) => (
        <TouchableOpacity
          key={m.id}
          style={[styles.methodCard, method === m.id && styles.methodCardActive]}
          onPress={() => setMethod(m.id)}
          activeOpacity={0.85}
        >
          <Text style={styles.methodIcon}>{m.icon}</Text>
          <View style={{ flex: 1 }}>
            <View style={styles.methodTitleRow}>
              <Text style={[styles.methodLabel, method === m.id && styles.methodLabelActive]}>
                {m.label}
              </Text>
              {m.recommended && (
                <View style={styles.recommendedBadge}>
                  <Text style={styles.recommendedText}>Recommended</Text>
                </View>
              )}
            </View>
            <Text style={styles.methodDesc}>{m.desc}</Text>
            <Text style={styles.methodLimit}>{m.limit}</Text>
          </View>
          <View style={[styles.radio, method === m.id && styles.radioActive]}>
            {method === m.id && <View style={styles.radioDot} />}
          </View>
        </TouchableOpacity>
      ))}

      {/* Fee breakdown for seller info */}
      {fees && (
        <View style={styles.sellerFeeCard}>
          <Text style={styles.sellerFeeTitle}>💰 Seller Payout Breakdown</Text>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Gross amount</Text>
            <Text style={styles.summaryVal}>${fees.seller_receives.gross.toFixed(2)}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Platform fee ({fees.seller_receives.platform_fee_rate})</Text>
            <Text style={[styles.summaryVal, { color: '#ef4444' }]}>-${fees.seller_receives.platform_fee.toFixed(2)}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Agent commission (1%)</Text>
            <Text style={[styles.summaryVal, { color: '#ef4444' }]}>-${fees.seller_receives.agent_commission.toFixed(2)}</Text>
          </View>
          <View style={[styles.summaryRow, { borderTopWidth: 1, borderTopColor: '#e2e8f0', paddingTop: 8, marginTop: 4 }]}>
            <Text style={[styles.summaryLabel, { fontWeight: '900', color: theme.colors.black }]}>Farmer receives</Text>
            <Text style={[styles.summaryVal, { color: theme.colors.green, fontWeight: '900' }]}>
              ${fees.seller_receives.net_payout.toFixed(2)}
            </Text>
          </View>
        </View>
      )}

      {/* Pay Button */}
      <TouchableOpacity
        style={[styles.payBtn, paying && styles.payBtnDisabled]}
        onPress={handlePay}
        disabled={paying}
        activeOpacity={0.9}
      >
        {paying ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.payBtnText}>
            PAY ${totalToPay.toFixed(2)} via {METHODS.find(m => m.id === method)?.label}
          </Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

// ─── Step 2: USSD / bank instructions + countdown ────────────────────────────
function InstructionsStep({ paymentResult, method, onConfirmed, onCancel }) {
  const [timeLeft, setTimeLeft] = useState((paymentResult?.instructions?.expires_minutes || 10) * 60);
  const [polling, setPolling] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) { clearInterval(timerRef.current); return 0; }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  const mins = String(Math.floor(timeLeft / 60)).padStart(2, '0');
  const secs = String(timeLeft % 60).padStart(2, '0');
  const expired = timeLeft === 0;

  const steps = paymentResult?.instructions?.steps || [];
  const methodInfo = METHODS.find(m => m.id === method) || {};

  const handleConfirmed = () => {
    // If auto-confirmed by backend, go straight to success
    if (paymentResult?.status === 'confirmed') {
      onConfirmed();
      return;
    }
    setPolling(true);
    // In production, poll /payments/status/{ref}
    setTimeout(() => {
      setPolling(false);
      onConfirmed();
    }, 1500);
  };

  return (
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
      <View style={styles.instructionHero}>
        <Text style={styles.instructionIcon}>{methodInfo.icon || '📱'}</Text>
        <Text style={styles.instructionTitle}>
          {paymentResult?.status === 'confirmed' ? '✅ Payment Confirmed!' : 'Complete Your Payment'}
        </Text>
        <Text style={styles.instructionSub}>
          {paymentResult?.status === 'confirmed'
            ? 'Your funds are now held in escrow.'
            : `Follow the steps below to pay via ${methodInfo.label}`}
        </Text>
      </View>

      {paymentResult?.status !== 'confirmed' && (
        <>
          {/* Countdown */}
          {!expired ? (
            <View style={styles.countdownCard}>
              <Text style={styles.countdownLabel}>⏱️ Expires in</Text>
              <Text style={styles.countdownTime}>{mins}:{secs}</Text>
            </View>
          ) : (
            <View style={[styles.countdownCard, { backgroundColor: '#fef2f2', borderColor: '#fecaca' }]}>
              <Text style={[styles.countdownLabel, { color: '#ef4444' }]}>⚠️ Payment window expired</Text>
              <TouchableOpacity onPress={onCancel}>
                <Text style={[styles.countdownTime, { color: '#ef4444', fontSize: 16 }]}>Start Over</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Steps */}
          <View style={styles.stepsCard}>
            <Text style={styles.stepsTitle}>
              {method === 'ecocash' || method === 'onemoney'
                ? `Dial ${methodInfo.ussd} on your phone`
                : 'Follow these steps:'}
            </Text>
            {steps.map((step, i) => (
              <View key={i} style={styles.stepRow}>
                <View style={styles.stepNum}>
                  <Text style={styles.stepNumText}>{i + 1}</Text>
                </View>
                <Text style={styles.stepText}>{step}</Text>
              </View>
            ))}
          </View>

          {/* Reference */}
          <View style={styles.refCard}>
            <Text style={styles.refLabel}>Payment Reference</Text>
            <Text style={styles.refValue}>{paymentResult?.payment_ref || '—'}</Text>
            <Text style={styles.refHint}>Keep this reference for your records</Text>
          </View>
        </>
      )}

      {/* Amount summary */}
      <View style={styles.amountCard}>
        <Text style={styles.amountLabel}>Amount</Text>
        <Text style={styles.amountValue}>
          {paymentResult?.currency === 'USD' ? '$' : (paymentResult?.currency || '$')}
          {Number(paymentResult?.amount || 0).toFixed(2)}
        </Text>
        <Text style={styles.amountOrder}>Order #{paymentResult?.order_number || '—'}</Text>
      </View>

      <TouchableOpacity
        style={[styles.payBtn, (polling || expired) && styles.payBtnDisabled]}
        onPress={handleConfirmed}
        disabled={polling || expired}
      >
        {polling ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.payBtnText}>
            {paymentResult?.status === 'confirmed' ? 'Continue →' : "I've Completed Payment"}
          </Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity style={styles.cancelBtn} onPress={onCancel}>
        <Text style={styles.cancelBtnText}>Cancel Payment</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// ─── Step 3: Success screen ───────────────────────────────────────────────────
function SuccessStep({ paymentResult, onTrackOrder, onBackToMarket }) {
  const scaleAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 60, friction: 8 }).start();
  }, []);

  return (
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120, alignItems: 'center' }}>
      <Animated.View style={[styles.successIcon, { transform: [{ scale: scaleAnim }] }]}>
        <Text style={{ fontSize: 64 }}>🎉</Text>
      </Animated.View>

      <Text style={styles.successTitle}>Payment Successful!</Text>
      <Text style={styles.successSub}>Your funds are now held securely in escrow.</Text>

      <View style={styles.successCard}>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Amount paid</Text>
          <Text style={[styles.summaryVal, { color: theme.colors.green }]}>
            ${Number(paymentResult?.amount || 0).toFixed(2)}
          </Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Transaction ID</Text>
          <Text style={styles.summaryVal}>#{paymentResult?.order_number || '—'}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Status</Text>
          <Text style={[styles.summaryVal, { color: theme.colors.green }]}>🛡️ In Escrow</Text>
        </View>
      </View>

      <View style={styles.nextStepsCard}>
        <Text style={styles.nextStepsTitle}>What happens next?</Text>
        {[
          'Farmer prepares your order for delivery',
          "You'll receive a notification when goods are dispatched",
          'Confirm receipt to release payment to farmer',
        ].map((step, i) => (
          <View key={i} style={styles.nextStepRow}>
            <View style={styles.nextStepNum}>
              <Text style={styles.nextStepNumText}>{i + 1}</Text>
            </View>
            <Text style={styles.nextStepText}>{step}</Text>
          </View>
        ))}
      </View>

      <TouchableOpacity style={styles.payBtn} onPress={onTrackOrder}>
        <Text style={styles.payBtnText}>Track Order</Text>
      </TouchableOpacity>

      <TouchableOpacity style={[styles.cancelBtn, { marginTop: 12 }]} onPress={onBackToMarket}>
        <Text style={styles.cancelBtnText}>Back to Marketplace</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// ─── Main PaymentScreen ───────────────────────────────────────────────────────
export default function PaymentScreen({ navigation, route }) {
  const { order, token } = route.params || {};
  const [step, setStep] = useState('select'); // select | instructions | success
  const [paymentResult, setPaymentResult] = useState(null);
  const [selectedMethod, setSelectedMethod] = useState('ecocash');

  if (!order) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorState}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorTitle}>No order found</Text>
          <TouchableOpacity style={styles.payBtn} onPress={() => navigation.goBack()}>
            <Text style={styles.payBtnText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const handlePay = (result, method) => {
    setPaymentResult(result);
    setSelectedMethod(method);
    setStep('instructions');
  };

  const handleConfirmed = () => setStep('success');
  const handleCancel = () => navigation.goBack();

  const handleTrackOrder = () => {
    navigation.navigate('OrderDetails', { orderId: order.id, role: 'buyer', token });
  };

  const handleBackToMarket = () => {
    navigation.navigate('Marketplace');
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => step === 'select' ? navigation.goBack() : setStep('select')}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {step === 'select' ? '💳 Complete Payment' : step === 'instructions' ? '📱 Payment Instructions' : '🎉 Payment Complete'}
        </Text>
        <View style={{ width: 60 }} />
      </View>

      {/* Progress dots */}
      <View style={styles.progressRow}>
        {['select', 'instructions', 'success'].map((s, i) => (
          <View key={s} style={[styles.progressDot, step === s && styles.progressDotActive,
            (step === 'instructions' && i === 0) || (step === 'success' && i <= 1) ? styles.progressDotDone : null
          ]} />
        ))}
      </View>

      <View style={styles.content}>
        {step === 'select' && (
          <SelectMethodStep order={order} token={token} onPay={handlePay} />
        )}
        {step === 'instructions' && (
          <InstructionsStep
            paymentResult={paymentResult}
            method={selectedMethod}
            onConfirmed={handleConfirmed}
            onCancel={handleCancel}
          />
        )}
        {step === 'success' && (
          <SuccessStep
            paymentResult={paymentResult}
            onTrackOrder={handleTrackOrder}
            onBackToMarket={handleBackToMarket}
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20, paddingTop: 16 },
  back: { fontSize: 16, fontWeight: '700', color: theme.colors.sky },
  headerTitle: { fontSize: 16, fontWeight: '900', color: theme.colors.black, flex: 1, textAlign: 'center' },
  progressRow: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginBottom: 8 },
  progressDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#e2e8f0' },
  progressDotActive: { backgroundColor: theme.colors.green, width: 24 },
  progressDotDone: { backgroundColor: '#86efac' },
  content: { flex: 1, paddingHorizontal: 20 },

  // Summary card
  summaryCard: { backgroundColor: '#f8fafc', borderRadius: 20, padding: 20, marginBottom: 20, borderWidth: 1, borderColor: '#e2e8f0' },
  summaryTitle: { fontSize: 14, fontWeight: '900', color: theme.colors.black, marginBottom: 14, letterSpacing: 0.5 },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  summaryLabel: { fontSize: 14, color: '#64748b', fontWeight: '600' },
  summaryVal: { fontSize: 14, color: theme.colors.black, fontWeight: '700' },
  divider: { height: 1, backgroundColor: '#e2e8f0', marginVertical: 12 },
  totalRow: { marginTop: 4 },
  totalLabel: { fontSize: 16, fontWeight: '900', color: theme.colors.black },
  totalVal: { fontSize: 20, fontWeight: '900', color: theme.colors.green },
  escrowBadge: { backgroundColor: '#fefce8', borderRadius: 12, padding: 10, marginTop: 12, borderWidth: 1, borderColor: '#fde68a' },
  escrowBadgeText: { fontSize: 12, color: '#92400e', fontWeight: '700', textAlign: 'center' },

  // Method cards
  sectionLabel: { fontSize: 11, fontWeight: '900', color: '#94a3b8', letterSpacing: 1.2, marginBottom: 12, textTransform: 'uppercase' },
  methodCard: { flexDirection: 'row', alignItems: 'center', gap: 14, padding: 16, borderRadius: 16, borderWidth: 1.5, borderColor: '#e2e8f0', marginBottom: 10, backgroundColor: '#f8fafc' },
  methodCardActive: { borderColor: theme.colors.green, backgroundColor: '#f0fdf4' },
  methodIcon: { fontSize: 28 },
  methodTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 2 },
  methodLabel: { fontSize: 15, fontWeight: '800', color: theme.colors.black },
  methodLabelActive: { color: theme.colors.green },
  methodDesc: { fontSize: 12, color: '#64748b', marginBottom: 2 },
  methodLimit: { fontSize: 11, color: '#94a3b8', fontWeight: '700' },
  recommendedBadge: { backgroundColor: '#dcfce7', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 20 },
  recommendedText: { fontSize: 10, fontWeight: '900', color: '#15803d' },
  radio: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: '#cbd5e1', justifyContent: 'center', alignItems: 'center' },
  radioActive: { borderColor: theme.colors.green },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: theme.colors.green },

  // Seller fee card
  sellerFeeCard: { backgroundColor: '#fff', borderRadius: 16, padding: 16, marginBottom: 20, borderWidth: 1, borderColor: '#e2e8f0' },
  sellerFeeTitle: { fontSize: 13, fontWeight: '900', color: theme.colors.black, marginBottom: 12 },

  // Pay button
  payBtn: { backgroundColor: theme.colors.green, paddingVertical: 18, borderRadius: 20, alignItems: 'center', marginTop: 8 },
  payBtnDisabled: { opacity: 0.5 },
  payBtnText: { color: '#fff', fontSize: 16, fontWeight: '900' },
  cancelBtn: { paddingVertical: 14, alignItems: 'center' },
  cancelBtnText: { color: '#94a3b8', fontWeight: '700', fontSize: 14 },

  // Instructions step
  instructionHero: { alignItems: 'center', paddingVertical: 24 },
  instructionIcon: { fontSize: 56, marginBottom: 12 },
  instructionTitle: { fontSize: 22, fontWeight: '900', color: theme.colors.black, textAlign: 'center', marginBottom: 8 },
  instructionSub: { fontSize: 14, color: '#64748b', textAlign: 'center', lineHeight: 22 },
  countdownCard: { backgroundColor: '#f0fdf4', borderRadius: 16, padding: 16, alignItems: 'center', marginBottom: 16, borderWidth: 1, borderColor: '#bbf7d0' },
  countdownLabel: { fontSize: 12, fontWeight: '800', color: '#15803d', marginBottom: 4 },
  countdownTime: { fontSize: 32, fontWeight: '900', color: theme.colors.green },
  stepsCard: { backgroundColor: '#f8fafc', borderRadius: 16, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: '#e2e8f0' },
  stepsTitle: { fontSize: 14, fontWeight: '900', color: theme.colors.black, marginBottom: 14 },
  stepRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, marginBottom: 12 },
  stepNum: { width: 24, height: 24, borderRadius: 12, backgroundColor: theme.colors.green, justifyContent: 'center', alignItems: 'center', flexShrink: 0 },
  stepNumText: { color: '#fff', fontSize: 12, fontWeight: '900' },
  stepText: { flex: 1, fontSize: 14, color: '#475569', fontWeight: '600', lineHeight: 20 },
  refCard: { backgroundColor: '#fffbeb', borderRadius: 16, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: '#fde68a', alignItems: 'center' },
  refLabel: { fontSize: 11, fontWeight: '900', color: '#92400e', letterSpacing: 1, marginBottom: 6 },
  refValue: { fontSize: 18, fontWeight: '900', color: '#92400e', letterSpacing: 2 },
  refHint: { fontSize: 11, color: '#b45309', marginTop: 4 },
  amountCard: { backgroundColor: '#f0fdf4', borderRadius: 16, padding: 16, marginBottom: 20, alignItems: 'center', borderWidth: 1, borderColor: '#bbf7d0' },
  amountLabel: { fontSize: 11, fontWeight: '900', color: '#15803d', letterSpacing: 1, marginBottom: 4 },
  amountValue: { fontSize: 32, fontWeight: '900', color: theme.colors.green },
  amountOrder: { fontSize: 12, color: '#64748b', marginTop: 4 },

  // Success step
  successIcon: { marginTop: 32, marginBottom: 16, alignSelf: 'center' },
  successTitle: { fontSize: 28, fontWeight: '900', color: theme.colors.black, textAlign: 'center', marginBottom: 8 },
  successSub: { fontSize: 15, color: '#64748b', textAlign: 'center', marginBottom: 24, lineHeight: 22 },
  successCard: { width: '100%', backgroundColor: '#f0fdf4', borderRadius: 20, padding: 20, marginBottom: 20, borderWidth: 1, borderColor: '#bbf7d0' },
  nextStepsCard: { width: '100%', backgroundColor: '#f8fafc', borderRadius: 20, padding: 20, marginBottom: 24, borderWidth: 1, borderColor: '#e2e8f0' },
  nextStepsTitle: { fontSize: 14, fontWeight: '900', color: theme.colors.black, marginBottom: 16 },
  nextStepRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, marginBottom: 12 },
  nextStepNum: { width: 28, height: 28, borderRadius: 14, backgroundColor: theme.colors.green, justifyContent: 'center', alignItems: 'center', flexShrink: 0 },
  nextStepNumText: { color: '#fff', fontSize: 13, fontWeight: '900' },
  nextStepText: { flex: 1, fontSize: 14, color: '#475569', fontWeight: '600', lineHeight: 20 },

  // Error state
  errorState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  errorIcon: { fontSize: 48, marginBottom: 16 },
  errorTitle: { fontSize: 20, fontWeight: '900', color: theme.colors.black, marginBottom: 24 },
});
