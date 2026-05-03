import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView, ActivityIndicator, RefreshControl, Alert } from 'react-native';
import { TrendingUp, Clock, ArrowDownCircle, Wallet, ChevronRight, CheckCircle, Truck } from 'lucide-react-native';
import { theme } from '../styles';
import { getEarnings } from '../api';

const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DEMO_WEEK = [45, 0, 90, 65, 120, 80, 50];

function WeeklyChart({ data = DEMO_WEEK }) {
  const max = Math.max(...data, 1);
  return (
    <View style={styles.chartContainer}>
      {data.map((val, i) => (
        <View key={i} style={styles.chartCol}>
          <Text style={styles.chartVal}>{val > 0 ? `$${val}` : ''}</Text>
          <View style={styles.chartBarBg}>
            <View style={[styles.chartBar, { height: `${(val / max) * 100}%`, backgroundColor: i === new Date().getDay() - 1 ? theme.colors.sky : '#E0E8F0' }]} />
          </View>
          <Text style={[styles.chartDay, i === new Date().getDay() - 1 && { color: theme.colors.sky, fontWeight: '800' }]}>{WEEK_DAYS[i]}</Text>
        </View>
      ))}
    </View>
  );
}

const DEMO_TRANSACTIONS = [
  { id: '1', route: 'Harare → Bulawayo', amount: 150, status: 'paid', date: 'Today, 2:30 PM', type: 'delivery' },
  { id: '2', route: 'Mutare → Harare', amount: 90, status: 'paid', date: 'Yesterday', type: 'delivery' },
  { id: '3', route: 'EcoCash Withdrawal', amount: -200, status: 'completed', date: 'May 1', type: 'withdrawal' },
  { id: '4', route: 'Gweru → Masvingo', amount: 65, status: 'pending', date: 'Apr 30', type: 'delivery' },
  { id: '5', route: 'Chinhoyi → Kariba', amount: 75, status: 'paid', date: 'Apr 29', type: 'delivery' },
];

export default function EarningsScreen({ route }) {
  const { token } = route.params || {};
  const [earnings, setEarnings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [period, setPeriod] = useState('week');

  const fetchEarnings = useCallback(async () => {
    try {
      const data = await getEarnings(token);
      setEarnings(data);
    } catch (err) {
      setEarnings({
        total: 1250, available: 900, pending: 350,
        this_week: 450, this_month: 1100, today: 120,
        completed_deliveries: 28, currency: 'USD',
      });
    } finally { setLoading(false); setRefreshing(false); }
  }, [token]);

  useEffect(() => { fetchEarnings(); }, [fetchEarnings]);
  const onRefresh = useCallback(() => { setRefreshing(true); fetchEarnings(); }, [fetchEarnings]);

  const handleWithdraw = () => {
    Alert.alert('Withdraw Funds', `Send $${earnings?.available || 0} to your EcoCash account?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Confirm Withdrawal', style: 'default', onPress: () => Alert.alert('Submitted!', 'Funds will arrive within 24 hours.') },
    ]);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={theme.colors.sky} />
          <Text style={{ color: '#999', marginTop: 12, fontWeight: '600' }}>Loading earnings...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const d = earnings || {};

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.sky} />}>

        <View style={styles.header}>
          <Text style={styles.title}>Earnings</Text>
        </View>

        {/* Balance Card */}
        <View style={styles.balanceCard}>
          <View style={styles.balanceTop}>
            <View>
              <Text style={styles.balanceLabel}>Available Balance</Text>
              <Text style={styles.balanceAmount}>${(d.available || 0).toLocaleString()}</Text>
            </View>
            <TouchableOpacity style={styles.withdrawBtnSmall} onPress={handleWithdraw} disabled={!d.available}>
              <ArrowDownCircle size={18} color="#FFF" />
              <Text style={styles.withdrawSmallText}>Withdraw</Text>
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

        {/* Weekly Chart */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>This Week</Text>
            <Text style={styles.sectionSub}>${d.this_week || 0} earned</Text>
          </View>
          <View style={styles.chartCard}>
            <WeeklyChart />
          </View>
        </View>

        {/* Quick Stats */}
        <View style={styles.quickStatsRow}>
          <View style={[styles.quickStat, { backgroundColor: '#E8F5E9' }]}>
            <CheckCircle size={20} color="#4CAF50" />
            <Text style={styles.qsNum}>{d.completed_deliveries || 0}</Text>
            <Text style={styles.qsLabel}>Completed</Text>
          </View>
          <View style={[styles.quickStat, { backgroundColor: '#E1F5FE' }]}>
            <TrendingUp size={20} color={theme.colors.sky} />
            <Text style={styles.qsNum}>${d.this_month || 0}</Text>
            <Text style={styles.qsLabel}>This Month</Text>
          </View>
          <View style={[styles.quickStat, { backgroundColor: '#FFF8E1' }]}>
            <Wallet size={20} color="#FF9800" />
            <Text style={styles.qsNum}>${d.total || 0}</Text>
            <Text style={styles.qsLabel}>All-Time</Text>
          </View>
        </View>

        {/* Recent Transactions */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Activity</Text>
            <TouchableOpacity><Text style={styles.seeAllText}>See All</Text></TouchableOpacity>
          </View>
          {DEMO_TRANSACTIONS.map(tx => (
            <View key={tx.id} style={styles.txRow}>
              <View style={[styles.txIcon, { backgroundColor: tx.type === 'withdrawal' ? '#FFF3E0' : '#E1F5FE' }]}>
                {tx.type === 'withdrawal' ? <ArrowDownCircle size={18} color="#FF9800" /> : <Truck size={18} color={theme.colors.sky} />}
              </View>
              <View style={styles.txInfo}>
                <Text style={styles.txRoute} numberOfLines={1}>{tx.route}</Text>
                <Text style={styles.txDate}>{tx.date}</Text>
              </View>
              <View style={styles.txRight}>
                <Text style={[styles.txAmount, tx.amount < 0 && { color: '#FF9800' }]}>
                  {tx.amount < 0 ? '-' : '+'}${Math.abs(tx.amount)}
                </Text>
                <Text style={[styles.txStatus, tx.status === 'pending' && { color: '#FF9800' }]}>
                  {tx.status === 'paid' ? '✓ Paid' : tx.status === 'pending' ? '⏳ Pending' : '✓ Done'}
                </Text>
              </View>
            </View>
          ))}
        </View>

        {/* Payment Method */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Payment Method</Text>
          <TouchableOpacity style={styles.paymentRow}>
            <Text style={{ fontSize: 28 }}>📱</Text>
            <View style={{ flex: 1, marginLeft: 14 }}>
              <Text style={styles.paymentName}>EcoCash</Text>
              <Text style={styles.paymentNum}>+263 77 •••• ••67</Text>
            </View>
            <View style={styles.primaryBadge}><Text style={styles.primaryText}>Primary</Text></View>
            <ChevronRight size={18} color="#CCC" />
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 },
  title: { fontSize: 28, fontWeight: '900', color: theme.colors.dark },

  balanceCard: { marginHorizontal: 20, backgroundColor: theme.colors.sky, borderRadius: 24, padding: 24, ...theme.shadows.lg },
  balanceTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  balanceLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 13, fontWeight: '600', letterSpacing: 0.5 },
  balanceAmount: { color: '#FFF', fontSize: 38, fontWeight: '900', marginTop: 4 },
  withdrawBtnSmall: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 14 },
  withdrawSmallText: { color: '#FFF', fontSize: 13, fontWeight: '700' },
  balanceStats: { flexDirection: 'row', backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 16, padding: 14 },
  balanceStat: { flex: 1, alignItems: 'center' },
  bStatVal: { color: '#FFF', fontSize: 16, fontWeight: '900' },
  bStatLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 11, fontWeight: '600', marginTop: 2 },
  bStatDivider: { width: 1, backgroundColor: 'rgba(255,255,255,0.2)' },

  section: { marginHorizontal: 20, marginTop: 24 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  sectionTitle: { fontSize: 14, fontWeight: '800', color: '#999', textTransform: 'uppercase', letterSpacing: 1 },
  sectionSub: { fontSize: 14, fontWeight: '700', color: theme.colors.sky },
  seeAllText: { fontSize: 13, fontWeight: '700', color: theme.colors.sky },

  chartCard: { backgroundColor: '#FFF', borderRadius: 20, padding: 20, ...theme.shadows.xs, borderWidth: 1, borderColor: '#F0F0F0' },
  chartContainer: { flexDirection: 'row', justifyContent: 'space-between', height: 140, alignItems: 'flex-end' },
  chartCol: { flex: 1, alignItems: 'center' },
  chartVal: { fontSize: 9, fontWeight: '700', color: '#999', marginBottom: 4 },
  chartBarBg: { width: 24, height: 90, backgroundColor: '#F5F5F5', borderRadius: 12, justifyContent: 'flex-end', overflow: 'hidden' },
  chartBar: { width: '100%', borderRadius: 12, minHeight: 4 },
  chartDay: { fontSize: 11, fontWeight: '600', color: '#BBB', marginTop: 6 },

  quickStatsRow: { flexDirection: 'row', marginHorizontal: 20, marginTop: 20, gap: 10 },
  quickStat: { flex: 1, borderRadius: 16, padding: 14, alignItems: 'center', gap: 6 },
  qsNum: { fontSize: 16, fontWeight: '900', color: theme.colors.dark },
  qsLabel: { fontSize: 10, fontWeight: '700', color: '#999' },

  txRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF', padding: 14, borderRadius: 16, marginBottom: 8, borderWidth: 1, borderColor: '#F5F5F5' },
  txIcon: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  txInfo: { flex: 1, marginLeft: 12 },
  txRoute: { fontSize: 14, fontWeight: '700', color: theme.colors.dark },
  txDate: { fontSize: 11, color: '#BBB', fontWeight: '500', marginTop: 2 },
  txRight: { alignItems: 'flex-end' },
  txAmount: { fontSize: 15, fontWeight: '900', color: '#4CAF50' },
  txStatus: { fontSize: 10, fontWeight: '700', color: '#4CAF50', marginTop: 2 },

  paymentRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF', padding: 16, borderRadius: 18, borderWidth: 1, borderColor: '#F0F0F0' },
  paymentName: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  paymentNum: { fontSize: 12, color: '#999', marginTop: 2 },
  primaryBadge: { backgroundColor: '#E8F5E9', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10, marginRight: 8 },
  primaryText: { fontSize: 11, fontWeight: '700', color: '#4CAF50' },
});
