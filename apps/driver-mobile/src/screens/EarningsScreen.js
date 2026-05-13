import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import {
  TrendingUp as IconTrendingUp, ArrowDownCircle as IconArrowDownCircle, 
  Wallet as IconWallet, ChevronRight as IconChevronRight, 
  CheckCircle as IconCheckCircle, Truck as IconTruck, 
  CreditCard as IconCreditCard, DollarSign as IconDollarSign, 
  Clock as IconClock,
} from 'lucide-react-native';
import { theme } from '../styles';
import { getEarnings, withdrawEarnings } from '../api';

const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DEMO_WEEK = [45, 0, 90, 65, 120, 80, 50];

function WeeklyChart({ data = DEMO_WEEK }) {
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

const DEMO_TRANSACTIONS = [
  { id: '1', route: 'Harare → Bulawayo', amount: 150, status: 'paid',    date: 'Today, 2:30 PM',  type: 'delivery' },
  { id: '2', route: 'Mutare → Harare',   amount: 90,  status: 'paid',    date: 'Yesterday',       type: 'delivery' },
  { id: '3', route: 'EcoCash Withdrawal',amount: -200, status: 'done',   date: 'May 1',           type: 'withdrawal' },
  { id: '4', route: 'Gweru → Masvingo',  amount: 65,  status: 'pending', date: 'Apr 30',          type: 'delivery' },
  { id: '5', route: 'Chinhoyi → Kariba', amount: 75,  status: 'paid',    date: 'Apr 29',          type: 'delivery' },
];

export default function EarningsScreen({ route }) {
  const { token } = route.params || {};
  const [earnings, setEarnings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [withdrawing, setWithdrawing] = useState(false);

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
    const amount = d.available || 0;
    if (!amount) {
      Alert.alert('No Funds', 'You have no available balance to withdraw.');
      return;
    }
    Alert.alert(
      'Withdraw Funds',
      `Transfer $${amount} to your EcoCash account?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          onPress: async () => {
            setWithdrawing(true);
            try {
              const res = await withdrawEarnings(token, amount, 'EcoCash', '+263770000000');
              Alert.alert('Success', `Funds withdrawn successfully. Reference: ${res.reference}`);
              fetchEarnings();
            } catch (err) {
              Alert.alert('Failed', err.message || 'Withdrawal failed. Try again.');
            } finally {
              setWithdrawing(false);
            }
          },
        },
      ],
    );
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
            <TouchableOpacity hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
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
});
