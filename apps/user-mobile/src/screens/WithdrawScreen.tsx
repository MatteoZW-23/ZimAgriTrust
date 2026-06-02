import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  SafeAreaView, TextInput, Alert, ActivityIndicator
} from 'react-native';
import { 
  ArrowLeft as IconArrowLeft, 
  Smartphone as IconSmartphone, 
  CreditCard as IconCreditCard, 
  Landmark as IconLandmark 
} from 'lucide-react-native';
import { theme } from '../styles';
import { getWalletBalance, withdrawFunds, getWithdrawalQuote, getPayoutMethods } from '../api';

export default function WithdrawScreen({ navigation, route }) {
  const { token } = route.params || {};
  const [balance, setBalance] = useState(null);
  const [loadingBalance, setLoadingBalance] = useState(true);
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('ecocash');
  const [accountNumber, setAccountNumber] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [quote, setQuote] = useState<any>(null);
  const [payoutMethods, setPayoutMethods] = useState<any[]>([]);

  useEffect(() => {
    getWalletBalance(token)
      .then(setBalance)
      .catch(() => setBalance({ balance_usd: 0 }))
      .finally(() => setLoadingBalance(false));
    getPayoutMethods(token)
      .then((rows) => {
        const methods = Array.isArray(rows) ? rows : [];
        const verified = methods.filter((m) => String(m.status).toUpperCase() === 'VERIFIED');
        setPayoutMethods(verified);
        if (verified.length > 0) {
          const preferred = verified.find((m) => m.is_default) || verified[0];
          setMethod(preferred.id);
          setAccountNumber(preferred.account_number || '');
        }
      })
      .catch(() => setPayoutMethods([]));
  }, [token]);

  const availableBalance = balance?.balance_usd || 0;
  const parsedAmount = parseFloat(amount) || 0;
  const isValid = parsedAmount > 0 && parsedAmount <= availableBalance && accountNumber.trim().length >= 7;

  useEffect(() => {
    let cancelled = false;
    if (!parsedAmount || parsedAmount <= 0) {
      setQuote(null);
      return;
    }
    getWithdrawalQuote(token, parsedAmount, 'USD')
      .then((q) => {
        if (!cancelled) setQuote(q);
      })
      .catch(() => {
        if (!cancelled) setQuote(null);
      });
    return () => {
      cancelled = true;
    };
  }, [token, parsedAmount]);

  const handleWithdraw = async () => {
    if (!isValid) return;
    Alert.alert(
      'Confirm Withdrawal',
      `Withdraw $${parsedAmount.toFixed(2)} via ${payoutMethods.find((m) => m.id === method)?.account_name || 'selected method'}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          onPress: async () => {
            setSubmitting(true);
            try {
              await withdrawFunds(token, {
                amount: parsedAmount,
                currency: 'USD',
                payment_method: payoutMethods.find((m) => m.id === method)?.provider || 'ecocash',
                account_number: accountNumber.trim(),
                payout_method_id: method,
              });
              Alert.alert('Withdrawal Requested', 'Your payout has been initiated. Funds will arrive shortly.', [
                { text: 'OK', onPress: () => navigation.navigate('Wallet', { token }) }
              ]);
            } catch (err) {
              Alert.alert('Error', err.message || 'Withdrawal failed. Please try again.');
            } finally {
              setSubmitting(false);
            }
          }
        }
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <IconArrowLeft size={22} color={theme.colors.black} />
          </TouchableOpacity>
          <Text style={styles.title}>Withdraw Funds</Text>
          <View style={{ width: 44 }} />
        </View>

        {/* Balance Card */}
        <View style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>AVAILABLE BALANCE</Text>
          {loadingBalance ? (
            <ActivityIndicator color="#fff" style={{ marginVertical: 8 }} />
          ) : (
            <Text style={styles.balanceAmount}>${availableBalance.toLocaleString(undefined, { minimumFractionDigits: 2 })}</Text>
          )}
          <Text style={styles.balanceSub}>Funds held in escrow are not available for withdrawal</Text>
        </View>

        {/* Amount Input */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>WITHDRAWAL AMOUNT (USD)</Text>
          <View style={styles.amountInputRow}>
            <Text style={styles.currencyPrefix}>$</Text>
            <TextInput
              style={styles.amountInput}
              placeholder="0.00"
              placeholderTextColor="#94a3b8"
              keyboardType="decimal-pad"
              value={amount}
              onChangeText={setAmount}
            />
          </View>
          <View style={styles.quickAmounts}>
            {[10, 25, 50, 100].map(v => (
              <TouchableOpacity
                key={v}
                style={[styles.quickBtn, parsedAmount === v && styles.quickBtnActive]}
                onPress={() => setAmount(String(v))}
              >
                <Text style={[styles.quickBtnText, parsedAmount === v && styles.quickBtnTextActive]}>${v}</Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity
              style={[styles.quickBtn, parsedAmount === availableBalance && styles.quickBtnActive]}
              onPress={() => setAmount(String(availableBalance))}
            >
              <Text style={[styles.quickBtnText, parsedAmount === availableBalance && styles.quickBtnTextActive]}>MAX</Text>
            </TouchableOpacity>
          </View>
          {parsedAmount > availableBalance && (
            <Text style={styles.errorText}>Amount exceeds available balance</Text>
          )}
        </View>

        {/* Payment Method */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>PAYOUT METHOD</Text>
          {payoutMethods.map(m => (
            <TouchableOpacity
              key={m.id}
              style={[styles.methodCard, method === m.id && styles.methodCardActive]}
              onPress={() => { setMethod(m.id); setAccountNumber(m.account_number || ''); }}
            >
              <View style={styles.methodIconBox}>
                {m.provider === 'bank' ? <IconLandmark size={24} color={method === m.id ? theme.colors.green : '#94a3b8'} /> : m.provider === 'onemoney' ? <IconCreditCard size={24} color={method === m.id ? theme.colors.green : '#94a3b8'} /> : <IconSmartphone size={24} color={method === m.id ? theme.colors.green : '#94a3b8'} />}
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.methodLabel, method === m.id && styles.methodLabelActive]}>{m.account_name}</Text>
                <Text style={styles.methodDesc}>{String(m.provider).toUpperCase()} • {m.account_number || m.branch_code || '-'}</Text>
              </View>
              <View style={[styles.radio, method === m.id && styles.radioActive]}>
                {method === m.id && <View style={styles.radioDot} />}
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Account Number */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>PAYOUT ACCOUNT</Text>
          <TextInput
            style={styles.input}
            placeholder="Account number"
            placeholderTextColor="#94a3b8"
            keyboardType="default"
            value={accountNumber}
            onChangeText={setAccountNumber}
          />
        </View>

        {/* Fee Info */}
        {parsedAmount > 0 && (
          <View style={styles.feeCard}>
            <View style={styles.feeRow}>
              <Text style={styles.feeLabel}>Withdrawal amount</Text>
              <Text style={styles.feeValue}>${parsedAmount.toFixed(2)}</Text>
            </View>
            <View style={styles.feeRow}>
              <Text style={styles.feeLabel}>Withdrawal fee</Text>
              <Text style={styles.feeValue}>-${Number(quote?.fee ?? (parsedAmount * 0.01)).toFixed(2)}</Text>
            </View>
            <View style={[styles.feeRow, { borderTopWidth: 1, borderTopColor: '#e2e8f0', paddingTop: 10, marginTop: 4 }]}>
              <Text style={[styles.feeLabel, { fontWeight: '900', color: theme.colors.black }]}>You receive</Text>
              <Text style={[styles.feeValue, { color: theme.colors.green, fontWeight: '900' }]}>
                ${Number(quote?.net ?? (parsedAmount * 0.99)).toFixed(2)}
              </Text>
            </View>
          </View>
        )}

        {/* Submit */}
        <View style={styles.submitSection}>
          <TouchableOpacity
            style={[styles.submitBtn, (!isValid || submitting) && styles.submitBtnDisabled]}
            onPress={handleWithdraw}
            disabled={!isValid || submitting}
          >
            {submitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.submitBtnText}>Request Withdrawal</Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingTop: 60, paddingBottom: 20 },
  backBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#f8fafc', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#e2e8f0' },
  title: { fontSize: 20, fontWeight: '900', color: theme.colors.black },
  balanceCard: { marginHorizontal: 20, marginBottom: 8, backgroundColor: theme.colors.black, borderRadius: 24, padding: 28, alignItems: 'center' },
  balanceLabel: { fontSize: 11, fontWeight: '900', color: '#64748b', letterSpacing: 1.2, marginBottom: 8 },
  balanceAmount: { fontSize: 40, fontWeight: '900', color: '#fff', marginBottom: 8 },
  balanceSub: { fontSize: 12, color: '#475569', textAlign: 'center', lineHeight: 18 },
  section: { marginHorizontal: 20, marginTop: 24 },
  sectionLabel: { fontSize: 11, fontWeight: '900', color: '#94a3b8', letterSpacing: 1.2, marginBottom: 12, textTransform: 'uppercase' },
  amountInputRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f8fafc', borderWidth: 1.5, borderColor: '#e2e8f0', borderRadius: 16, paddingHorizontal: 16, height: 64 },
  currencyPrefix: { fontSize: 24, fontWeight: '900', color: theme.colors.green, marginRight: 8 },
  amountInput: { flex: 1, fontSize: 28, fontWeight: '900', color: theme.colors.black },
  quickAmounts: { flexDirection: 'row', gap: 8, marginTop: 12 },
  quickBtn: { flex: 1, paddingVertical: 10, borderRadius: 12, backgroundColor: '#f1f5f9', borderWidth: 1, borderColor: '#e2e8f0', alignItems: 'center' },
  quickBtnActive: { backgroundColor: theme.colors.green, borderColor: theme.colors.green },
  quickBtnText: { fontSize: 13, fontWeight: '800', color: '#475569' },
  quickBtnTextActive: { color: '#fff' },
  errorText: { color: '#ef4444', fontWeight: '700', fontSize: 13, marginTop: 8 },
  methodCard: { flexDirection: 'row', alignItems: 'center', gap: 14, padding: 16, borderRadius: 16, borderWidth: 1.5, borderColor: '#e2e8f0', marginBottom: 10, backgroundColor: '#f8fafc' },
  methodCardActive: { borderColor: theme.colors.green, backgroundColor: '#f0fdf4' },
  methodIconBox: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#f1f5f9', alignItems: 'center', justifyContent: 'center' },
  methodLabel: { fontSize: 15, fontWeight: '800', color: theme.colors.black },
  methodLabelActive: { color: theme.colors.green },
  methodDesc: { fontSize: 12, color: '#64748b', marginTop: 2 },
  radio: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: '#cbd5e1', justifyContent: 'center', alignItems: 'center' },
  radioActive: { borderColor: theme.colors.green },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: theme.colors.green },
  input: { backgroundColor: '#f8fafc', borderWidth: 1.5, borderColor: '#e2e8f0', borderRadius: 16, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, fontWeight: '600', color: theme.colors.black },
  feeCard: { marginHorizontal: 20, marginTop: 20, backgroundColor: '#f8fafc', borderRadius: 16, padding: 16, borderWidth: 1, borderColor: '#e2e8f0' },
  feeRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  feeLabel: { fontSize: 14, color: '#475569', fontWeight: '600' },
  feeValue: { fontSize: 14, color: theme.colors.black, fontWeight: '700' },
  submitSection: { marginHorizontal: 20, marginTop: 28 },
  submitBtn: { backgroundColor: theme.colors.green, paddingVertical: 18, borderRadius: 20, alignItems: 'center' },
  submitBtnDisabled: { opacity: 0.5 },
  submitBtnText: { color: '#fff', fontSize: 17, fontWeight: '900' },
});
