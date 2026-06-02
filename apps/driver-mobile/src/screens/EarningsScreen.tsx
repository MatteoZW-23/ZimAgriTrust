import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, ActivityIndicator, RefreshControl, Alert,
  Modal, TextInput,
} from 'react-native';
import {
  TrendingUp as IconTrendingUp, ArrowDownCircle as IconArrowDownCircle, 
  Wallet as IconWallet, ChevronRight as IconChevronRight, 
  CheckCircle as IconCheckCircle, Truck as IconTruck, 
  CreditCard as IconCreditCard, DollarSign as IconDollarSign, 
  Clock as IconClock, X as IconX, Star as IconStar,
  MapPin as IconMapPin, Calendar as IconCalendar,
} from 'lucide-react-native';
import { theme } from '../styles';
import { getEarnings, withdrawEarnings } from '../api';

const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function WeeklyChart({ data = [] }) {
  const max = Math.max(...data, 1);
  const today = new Date().getDay(); // 0=Sun, 1=Mon...
  const todayIdx = today === 0 ? 6 : today - 1;
  return (
    <View style={styles.chartContainer}>
      {data.map((val, i) => (
        <View key={i} style={styles.chartCol}>
          {val > 0 && <Text style={styles.chartVal}>${val}</Text>}
          <View style={styles.chartBarBg}>
            <View style={[
              styles.chartBar,
              { height: `${(val / max) * 100}%` },
              i === todayIdx ? styles.chartBarToday : styles.chartBarDefault,
            ]} />
          </View>
          <Text style={[styles.chartDay, i === todayIdx && styles.chartDayToday]}>
            {WEEK_DAYS[i]}
          </Text>
        </View>
      ))}
    </View>
  );
}

export default function EarningsScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [earnings, setEarnings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [withdrawing, setWithdrawing] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('EcoCash');
  const [phoneNumber, setPhoneNumber] = useState('+26377');

  const fetchEarnings = useCallback(async () => {
    try {
      const data = await getEarnings(token);
      setEarnings(data);
    } catch {
      setEarnings({
        total: 1250, available: 900, pending: 350,
        this_week: 450, this_month: 1100, today: 120,
        completed_deliveries: 28, currency: 'USD',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { fetchEarnings(); }, [fetchEarnings]);
  const onRefresh = useCallback(() => { setRefreshing(true); fetchEarnings(); }, [fetchEarnings]);

  const handleWithdraw = () => {
    const amount = earnings?.available || 0;
    if (!amount) {
      Alert.alert('No Funds', 'You have no available balance to withdraw.');
      return;
    }
    setWithdrawAmount(String(amount));
    setShowWithdrawModal(true);
  };

  const handleConfirmWithdraw = async () => {
    const amount = parseFloat(withdrawAmount);
    if (!amount || amount <= 0) {
      Alert.alert('Invalid Amount', 'Please enter a valid withdrawal amount.');
      return;
    }
    if (amount > (earnings?.available || 0)) {
      Alert.alert('Insufficient Funds', 'You cannot withdraw more than your available balance.');
      return;
    }
    if (phoneNumber.length < 10) {
      Alert.alert('Invalid Phone', 'Please enter a valid phone number.');
      return;
    }

    setWithdrawing(true);
    try {
      const res = await withdrawEarnings(token, amount, selectedPaymentMethod, phoneNumber);
      Alert.alert('Success', `Funds withdrawn successfully. Reference: ${res.reference}`);
      setShowWithdrawModal(false);
      setWithdrawAmount('');
      fetchEarnings();
    } catch (err) {
      Alert.alert('Failed', err.message || 'Withdrawal failed. Try again.');
    } finally {
      setWithdrawing(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingState}>
          <ActivityIndicator size="large" color={theme.colors.sky} />
          <Text style={styles.loadingText}>Loading earnings...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const d = earnings || {};

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.sky} />}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Earnings</Text>
        </View>

        {/* Balance card */}
        <View style={styles.balanceCard}>
          <View style={styles.balanceTop}>
            <View>
              <Text style={styles.balanceLabel}>Available Balance</Text>
              <Text style={styles.balanceAmount}>${(d.available || 0).toLocaleString()}</Text>
            </View>
            <TouchableOpacity
              style={[styles.withdrawBtn, (!d.available || withdrawing) && styles.withdrawBtnDisabled]}
              onPress={handleWithdraw}
              disabled={!d.available || withdrawing}
            >
              {withdrawing ? <ActivityIndicator size="small" color="#FFF" /> : (
                <>
                  <IconArrowDownCircle size={16} color="#FFF" />
                  <Text style={styles.withdrawBtnText}>Withdraw</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
          <View style={styles.balanceStats}>
            <View style={styles.balanceStat}>
              <Text style={styles.bStatVal}>${d.today || 0}</Text>
              <Text style={styles.bStatLabel}>Today</Text>
            </View>
            <View style={styles.bStatDivider} />
            <View style={styles.balanceStat}>
              <Text style={styles.bStatVal}>${d.this_week || 0}</Text>
              <Text style={styles.bStatLabel}>This Week</Text>
            </View>
            <View style={styles.bStatDivider} />
            <View style={styles.balanceStat}>
              <Text style={styles.bStatVal}>${d.pending || 0}</Text>
              <Text style={styles.bStatLabel}>Pending</Text>
            </View>
          </View>
        </View>

        {/* Weekly chart */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>This Week</Text>
            <Text style={styles.sectionSub}>${d.this_week || 0} earned</Text>
          </View>
          <View style={styles.chartCard}>
            <WeeklyChart />
          </View>
        </View>

        {/* Performance Stats */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Performance Stats</Text>
          <View style={styles.perfGrid}>
            <View style={styles.perfCard}>
              <View style={styles.perfIcon}>
                <IconStar size={18} color="#F59E0B" />
              </View>
              <Text style={styles.perfValue}>4.8</Text>
              <Text style={styles.perfLabel}>Rating</Text>
            </View>
            <View style={styles.perfCard}>
              <View style={styles.perfIcon}>
                <IconTruck size={18} color={theme.colors.sky} />
              </View>
              <Text style={styles.perfValue}>{d.completed_deliveries || 0}</Text>
              <Text style={styles.perfLabel}>Deliveries</Text>
            </View>
            <View style={styles.perfCard}>
              <View style={styles.perfIcon}>
                <IconMapPin size={18} color="#4CAF50" />
              </View>
              <Text style={styles.perfValue}>1,240</Text>
              <Text style={styles.perfLabel}>km Traveled</Text>
            </View>
            <View style={styles.perfCard}>
              <View style={styles.perfIcon}>
                <IconCalendar size={18} color="#9C27B0" />
              </View>
              <Text style={styles.perfValue}>98%</Text>
              <Text style={styles.perfLabel}>On-Time</Text>
            </View>
          </View>
        </View>

        {/* Quick stats */}
        <View style={styles.statsRow}>
          <View style={[styles.statCard, { backgroundColor: '#F0FDF4' }]}>
            <IconCheckCircle size={20} color="#4CAF50" />
            <Text style={styles.statNum}>{d.completed_deliveries || 0}</Text>
            <Text style={styles.statLabel}>Completed</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: '#E1F5FE' }]}>
            <IconTrendingUp size={20} color={theme.colors.sky} />
            <Text style={styles.statNum}>${d.this_month || 0}</Text>
            <Text style={styles.statLabel}>This Month</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: '#FFFBEB' }]}>
            <IconWallet size={20} color="#F59E0B" />
            <Text style={styles.statNum}>${d.total || 0}</Text>
            <Text style={styles.statLabel}>All-Time</Text>
          </View>
        </View>

        {/* Recent transactions */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Activity</Text>
            <TouchableOpacity hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }} onPress={() => navigation.navigate('Transactions', { token })}>
              <Text style={styles.seeAll}>See All</Text>
            </TouchableOpacity>
          </View>
          {DEMO_TRANSACTIONS.map(tx => {
            const isWithdrawal = tx.type === 'withdrawal';
            const isPending = tx.status === 'pending';
            return (
              <View key={tx.id} style={styles.txRow}>
                <View style={[styles.txIcon, { backgroundColor: isWithdrawal ? '#FFFBEB' : '#E1F5FE' }]}>
                  {isWithdrawal
                    ? <IconArrowDownCircle size={18} color="#F59E0B" />
                    : <IconTruck size={18} color={theme.colors.sky} />
                  }
                </View>
                <View style={styles.txInfo}>
                  <Text style={styles.txRoute} numberOfLines={1}>{tx.route}</Text>
                  <Text style={styles.txDate}>{tx.date}</Text>
                </View>
                <View style={styles.txRight}>
                  <Text style={[styles.txAmount, isWithdrawal && styles.txAmountOut]}>
                    {isWithdrawal ? '-' : '+'}${Math.abs(tx.amount)}
                  </Text>
                  <View style={[styles.txStatusBadge, isPending && styles.txStatusPending]}>
                    {isPending
                      ? <IconClock size={9} color="#F59E0B" />
                      : <IconCheckCircle size={9} color="#4CAF50" />
                    }
                    <Text style={[styles.txStatusText, isPending && { color: '#F59E0B' }]}>
                      {isPending ? 'Pending' : 'Paid'}
                    </Text>
                  </View>
                </View>
              </View>
            );
          })}
        </View>

        {/* Payment method */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Payment Method</Text>
          <TouchableOpacity style={styles.paymentRow} activeOpacity={0.75}>
            <View style={styles.paymentIcon}>
              <IconCreditCard size={20} color={theme.colors.sky} />
            </View>
            <View style={styles.paymentInfo}>
              <Text style={styles.paymentName}>EcoCash</Text>
              <Text style={styles.paymentNum}>+263 77 •••• ••67</Text>
            </View>
            <View style={styles.primaryBadge}>
              <Text style={styles.primaryText}>Primary</Text>
            </View>
            <IconChevronRight size={18} color="#CCC" />
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Withdrawal Modal */}
      <Modal visible={showWithdrawModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Withdraw Funds</Text>
            <TouchableOpacity onPress={() => setShowWithdrawModal(false)} style={styles.modalCloseBtn}>
              <IconX size={20} color="#666" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.balanceInfo}>
              <Text style={styles.balanceInfoLabel}>Available Balance</Text>
              <Text style={styles.balanceInfoAmount}>${(earnings?.available || 0).toLocaleString()}</Text>
            </View>

            <Text style={styles.modalSectionTitle}>Amount</Text>
            <View style={styles.amountInputContainer}>
              <Text style={styles.currencySymbol}>$</Text>
              <TextInput
                style={styles.amountInput}
                value={withdrawAmount}
                onChangeText={setWithdrawAmount}
                placeholder="0.00"
                keyboardType="decimal-pad"
                placeholderTextColor="#CCC"
              />
            </View>

            <Text style={styles.modalSectionTitle}>Payment Method</Text>
            <View style={styles.paymentMethods}>
              {['EcoCash', 'OneMoney', 'Bank Transfer'].map(method => (
                <TouchableOpacity
                  key={method}
                  style={[
                    styles.paymentMethodCard,
                    selectedPaymentMethod === method && styles.paymentMethodSelected,
                  ]}
                  onPress={() => setSelectedPaymentMethod(method)}
                >
                  <View style={styles.paymentMethodRadio}>
                    {selectedPaymentMethod === method && (
                      <View style={styles.paymentMethodRadioInner} />
                    )}
                  </View>
                  <Text style={[
                    styles.paymentMethodText,
                    selectedPaymentMethod === method && styles.paymentMethodTextSelected,
                  ]}>
                    {method}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.modalSectionTitle}>Phone Number</Text>
            <TextInput
              style={styles.phoneInput}
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              placeholder="+263 77 123 4567"
              keyboardType="phone-pad"
              placeholderTextColor="#CCC"
            />

            <View style={styles.feeInfo}>
              <Text style={styles.feeLabel}>Processing Fee</Text>
              <Text style={styles.feeValue}>$0.00</Text>
            </View>
            <View style={styles.feeInfo}>
              <Text style={styles.feeLabel}>You'll Receive</Text>
              <Text style={[styles.feeValue, styles.feeValueHighlight]}>
                ${withdrawAmount || '0.00'}
              </Text>
            </View>
          </ScrollView>

          <View style={styles.modalFooter}>
            <TouchableOpacity
              style={[styles.confirmBtn, withdrawing && styles.confirmBtnDisabled]}
              onPress={handleConfirmWithdraw}
              disabled={withdrawing}
            >
              {withdrawing ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <>
                  <IconArrowDownCircle size={18} color="#FFF" />
                  <Text style={styles.confirmBtnText}>Confirm Withdrawal</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  scrollContent: { paddingBottom: 120 },
  loadingState: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#999', marginTop: 12, fontWeight: '600', fontSize: 14 },

  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 },
  title: { fontSize: 28, fontWeight: '900', color: theme.colors.dark },

  balanceCard: {
    marginHorizontal: 20, backgroundColor: theme.colors.sky,
    borderRadius: 24, padding: 24, ...theme.shadows.lg,
  },
  balanceTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  balanceLabel: { color: 'rgba(255,255,255,0.75)', fontSize: 13, fontWeight: '600' },
  balanceAmount: { color: '#FFF', fontSize: 36, fontWeight: '900', marginTop: 4 },
  withdrawBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 14,
  },
  withdrawBtnDisabled: { opacity: 0.5 },
  withdrawBtnText: { color: '#FFF', fontSize: 13, fontWeight: '700' },
  balanceStats: {
    flexDirection: 'row', backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 16, padding: 14,
  },
  balanceStat: { flex: 1, alignItems: 'center' },
  bStatVal: { color: '#FFF', fontSize: 16, fontWeight: '900' },
  bStatLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 11, fontWeight: '600', marginTop: 2 },
  bStatDivider: { width: 1, backgroundColor: 'rgba(255,255,255,0.2)' },

  section: { marginHorizontal: 20, marginTop: 24 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: '#BBB', textTransform: 'uppercase', letterSpacing: 1 },
  sectionSub: { fontSize: 13, fontWeight: '700', color: theme.colors.sky },
  seeAll: { fontSize: 13, fontWeight: '700', color: theme.colors.sky },

  chartCard: {
    backgroundColor: '#FFF', borderRadius: 20, padding: 20,
    ...theme.shadows.xs, borderWidth: 1, borderColor: '#F0F0F0',
  },
  chartContainer: { flexDirection: 'row', justifyContent: 'space-between', height: 130, alignItems: 'flex-end' },
  chartCol: { flex: 1, alignItems: 'center' },
  chartVal: { fontSize: 8, fontWeight: '700', color: '#999', marginBottom: 4 },
  chartBarBg: { width: 22, height: 80, backgroundColor: '#F5F5F5', borderRadius: 11, justifyContent: 'flex-end', overflow: 'hidden' },
  chartBar: { width: '100%', borderRadius: 11, minHeight: 4 },
  chartBarDefault: { backgroundColor: '#E0E8F0' },
  chartBarToday: { backgroundColor: theme.colors.sky },
  chartDay: { fontSize: 10, fontWeight: '600', color: '#BBB', marginTop: 5 },
  chartDayToday: { color: theme.colors.sky, fontWeight: '800' },

  statsRow: { flexDirection: 'row', marginHorizontal: 20, marginTop: 20, gap: 10 },
  statCard: { flex: 1, borderRadius: 16, padding: 14, alignItems: 'center', gap: 6 },
  statNum: { fontSize: 15, fontWeight: '900', color: theme.colors.dark },
  statLabel: { fontSize: 10, fontWeight: '700', color: '#999' },

  txRow: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    padding: 14, borderRadius: 16, marginBottom: 8, borderWidth: 1, borderColor: '#F5F5F5',
  },
  txIcon: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  txInfo: { flex: 1, marginLeft: 12 },
  txRoute: { fontSize: 14, fontWeight: '700', color: theme.colors.dark },
  txDate: { fontSize: 11, color: '#BBB', fontWeight: '500', marginTop: 2 },
  txRight: { alignItems: 'flex-end', gap: 4 },
  txAmount: { fontSize: 15, fontWeight: '900', color: '#4CAF50' },
  txAmountOut: { color: '#F59E0B' },
  txStatusBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 3,
    backgroundColor: '#F0FDF4', paddingHorizontal: 7, paddingVertical: 3, borderRadius: 8,
  },
  txStatusPending: { backgroundColor: '#FFFBEB' },
  txStatusText: { fontSize: 10, fontWeight: '700', color: '#4CAF50' },

  paymentRow: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    padding: 16, borderRadius: 18, borderWidth: 1, borderColor: '#F0F0F0', gap: 12,
  },
  paymentIcon: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: '#E1F5FE', justifyContent: 'center', alignItems: 'center',
  },
  paymentInfo: { flex: 1 },
  paymentName: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  paymentNum: { fontSize: 12, color: '#999', marginTop: 2 },
  primaryBadge: { backgroundColor: '#F0FDF4', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  primaryText: { fontSize: 11, fontWeight: '700', color: '#4CAF50' },

  perfGrid: { flexDirection: 'row', gap: 10 },
  perfCard: {
    flex: 1, backgroundColor: '#FFF', borderRadius: 16, padding: 14,
    alignItems: 'center', borderWidth: 1, borderColor: '#F0F0F0', ...theme.shadows.xs,
  },
  perfIcon: {
    width: 36, height: 36, borderRadius: 18, backgroundColor: '#F5F5F5',
    justifyContent: 'center', alignItems: 'center', marginBottom: 8,
  },
  perfValue: { fontSize: 18, fontWeight: '900', color: theme.colors.dark },
  perfLabel: { fontSize: 11, fontWeight: '600', color: '#999', marginTop: 2 },

  modalContainer: { flex: 1, backgroundColor: '#F8F9FA' },
  modalHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingVertical: 16, backgroundColor: '#FFF',
    borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  modalTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.dark },
  modalCloseBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: '#F5F5F5', justifyContent: 'center', alignItems: 'center',
  },
  modalContent: { flex: 1, padding: 20 },
  modalSectionTitle: {
    fontSize: 15, fontWeight: '700', color: theme.colors.dark, marginBottom: 10, marginTop: 8,
  },
  balanceInfo: {
    backgroundColor: theme.colors.sky, borderRadius: 16, padding: 20,
    alignItems: 'center', marginBottom: 24, ...theme.shadows.md,
  },
  balanceInfoLabel: { fontSize: 13, color: 'rgba(255,255,255,0.8)', fontWeight: '600' },
  balanceInfoAmount: { fontSize: 32, fontWeight: '900', color: '#FFF', marginTop: 4 },
  amountInputContainer: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    borderRadius: 14, borderWidth: 2, borderColor: '#F0F0F0', paddingHorizontal: 16, paddingVertical: 4,
  },
  currencySymbol: { fontSize: 24, fontWeight: '700', color: theme.colors.dark, marginRight: 8 },
  amountInput: { flex: 1, fontSize: 24, fontWeight: '700', color: theme.colors.dark, paddingVertical: 8 },
  paymentMethods: { flexDirection: 'row', gap: 10, marginBottom: 20 },
  paymentMethodCard: {
    flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: '#FFF', borderRadius: 12, borderWidth: 2, borderColor: '#F0F0F0',
    paddingHorizontal: 12, paddingVertical: 10,
  },
  paymentMethodSelected: { borderColor: theme.colors.sky, backgroundColor: '#F0F9FF' },
  paymentMethodRadio: {
    width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: '#D0D0D0',
    justifyContent: 'center', alignItems: 'center',
  },
  paymentMethodRadioInner: { width: 10, height: 10, borderRadius: 5, backgroundColor: theme.colors.sky },
  paymentMethodText: { fontSize: 13, fontWeight: '600', color: '#666' },
  paymentMethodTextSelected: { color: theme.colors.sky, fontWeight: '700' },
  phoneInput: {
    backgroundColor: '#FFF', borderRadius: 14, borderWidth: 2, borderColor: '#F0F0F0',
    paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, fontWeight: '600', color: theme.colors.dark,
    marginBottom: 20,
  },
  feeInfo: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  feeLabel: { fontSize: 14, fontWeight: '600', color: '#666' },
  feeValue: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  feeValueHighlight: { fontSize: 18, fontWeight: '900', color: '#4CAF50' },
  modalFooter: {
    padding: 20, backgroundColor: '#FFF', borderTopWidth: 1, borderTopColor: '#F0F0F0',
  },
  confirmBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    backgroundColor: theme.colors.sky, paddingVertical: 16, borderRadius: 16, ...theme.shadows.md,
  },
  confirmBtnDisabled: { backgroundColor: '#D0D0D0' },
  confirmBtnText: { color: '#FFF', fontSize: 16, fontWeight: '800' },
});
