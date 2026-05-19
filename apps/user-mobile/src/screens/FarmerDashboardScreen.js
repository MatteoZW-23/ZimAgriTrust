import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View, Dimensions } from 'react-native';
import Animated, { FadeInDown, FadeInRight, FadeInUp } from 'react-native-reanimated';
import { LineChart, PieChart } from 'react-native-chart-kit';
import { ClipboardList, Leaf, PackageCheck, PlusCircle, TrendingUp, Wallet, ChevronRight, Clock, DollarSign, BarChart3 } from 'lucide-react-native';
import { getMyListings, getProfile, getTransactions, getWalletBalance } from '../api';
import { theme } from '../styles';

const { width } = Dimensions.get('window');

export default function FarmerDashboardScreen({ navigation, route }) {
  const { token, profile: initialProfile = {} } = route.params || {};
  const [profile, setProfile] = useState(initialProfile);
  const [listings, setListings] = useState([]);
  const [orders, setOrders] = useState([]);
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setError('');
      const [profileData, listingData, orderData, walletData] = await Promise.all([
        getProfile(token),
        getMyListings(token),
        getTransactions(token),
        getWalletBalance(token),
      ]);
      setProfile(profileData || {});
      setListings(Array.isArray(listingData) ? listingData : listingData?.data || []);
      setOrders(Array.isArray(orderData) ? orderData : orderData?.data || []);
      setWallet(walletData || null);
    } catch (err) {
      setError(err.message || 'Could not load your farmer dashboard.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const activeListings = listings.filter((item) => String(item.status || '').toUpperCase() === 'ACTIVE').length;
  const totalSales = orders.filter(o => o.status === 'COMPLETED').reduce((sum, o) => sum + (Number(o.total_amount || o.amount || 0)), 0);
  const pendingOrders = orders.filter(o => o.status === 'PENDING' || o.status === 'PROCESSING').length;
  const completedOrders = orders.filter(o => o.status === 'COMPLETED').length;
  const avgOrderValue = completedOrders > 0 ? totalSales / completedOrders : 0;

  // Sales trend data (last 7 days)
  const salesTrendData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        data: [120, 280, 190, 350, 420, 380, 290],
        color: (opacity = 1) => `rgba(16, 185, 129, ${opacity})`,
        strokeWidth: 2,
      },
    ],
  };

  // Revenue breakdown data
  const revenueBreakdownData = [
    {
      name: 'Crops',
      population: 45,
      color: '#10B981',
      legendFontColor: '#0F172A',
      legendFontSize: 12,
    },
    {
      name: 'Livestock',
      population: 30,
      color: '#F59E0B',
      legendFontColor: '#0F172A',
      legendFontSize: 12,
    },
    {
      name: 'Equipment',
      population: 15,
      color: '#0EA5E9',
      legendFontColor: '#0F172A',
      legendFontSize: 12,
    },
    {
      name: 'Other',
      population: 10,
      color: '#8B5CF6',
      legendFontColor: '#0F172A',
      legendFontSize: 12,
    },
  ];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor="#10B981" />}
    >
      <Animated.View entering={FadeInDown.duration(600).springify()} style={styles.hero}>
        <View style={styles.heroGlow} />
        <View style={styles.heroContent}>
          <Text style={styles.kicker}>FARMER PORTAL</Text>
          <Text style={styles.title}>Hello,{'\n'}{profile.full_name || profile.name || 'Farmer'}!</Text>
          <Text style={styles.subtitle}>Manage your agricultural listings, track sales, and grow your business.</Text>
        </View>
      </Animated.View>

      {loading ? (
        <View style={styles.stateCard}>
          <ActivityIndicator size="large" color="#10B981" />
        </View>
      ) : error ? (
        <View style={styles.stateCard}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.primaryBtn} onPress={load}>
            <Text style={styles.primaryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          <Animated.View entering={FadeInUp.duration(600).delay(100).springify()} style={styles.grid}>
            <Metric icon={TrendingUp} color="#10B981" label="Total Sales" value={`$${totalSales.toFixed(2)}`} />
            <Metric icon={Leaf} color="#F59E0B" label="Active Listings" value={activeListings} />
            <Metric icon={Clock} color="#0EA5E9" label="Pending Orders" value={pendingOrders} />
            <Metric icon={Wallet} color="#8B5CF6" label="Wallet Balance" value={`$${Number(wallet?.available_usd ?? wallet?.available ?? 0).toFixed(2)}`} />
          </Animated.View>

          <Animated.View entering={FadeInUp.duration(600).delay(150).springify()} style={styles.grid}>
            <Metric icon={PackageCheck} color="#6366F1" label="Completed Orders" value={completedOrders} />
            <Metric icon={DollarSign} color="#EC4899" label="Avg Order Value" value={`$${avgOrderValue.toFixed(2)}`} />
          </Animated.View>

          <Animated.View entering={FadeInRight.duration(600).delay(200).springify()} style={styles.chartSection}>
            <Text style={styles.sectionTitle}>Sales Trend (Last 7 Days)</Text>
            <View style={styles.chartCard}>
              <LineChart
                data={salesTrendData}
                width={width - 48}
                height={200}
                chartConfig={{
                  backgroundColor: '#FFFFFF',
                  backgroundGradientFrom: '#FFFFFF',
                  backgroundGradientTo: '#FFFFFF',
                  decimalPlaces: 0,
                  color: (opacity = 1) => `rgba(16, 185, 129, ${opacity})`,
                  labelColor: (opacity = 1) => `rgba(71, 85, 105, ${opacity})`,
                  style: { borderRadius: 16 },
                  propsForDots: { r: '4', strokeWidth: '2', stroke: '#10B981' },
                }}
                bezier
                style={styles.chart}
              />
            </View>
          </Animated.View>

          <Animated.View entering={FadeInRight.duration(600).delay(250).springify()} style={styles.chartSection}>
            <Text style={styles.sectionTitle}>Revenue Breakdown</Text>
            <View style={styles.chartCard}>
              <PieChart
                data={revenueBreakdownData}
                width={width - 48}
                height={200}
                chartConfig={{
                  backgroundColor: '#FFFFFF',
                  backgroundGradientFrom: '#FFFFFF',
                  backgroundGradientTo: '#FFFFFF',
                  decimalPlaces: 0,
                  color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  style: { borderRadius: 16 },
                }}
                accessor="population"
                backgroundColor="transparent"
                paddingLeft="15"
                style={styles.chart}
              />
            </View>
          </Animated.View>

          <Animated.View entering={FadeInRight.duration(600).delay(200).springify()} style={styles.actionSection}>
            <Text style={styles.sectionTitle}>Quick Actions</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.actionRow}>
              <ActionCard icon={PlusCircle} color="#10B981" label="Add Listing" onPress={() => navigation.navigate('CreateListing', { token })} />
              <ActionCard icon={ClipboardList} color="#F59E0B" label="My Listings" onPress={() => navigation.navigate('FarmerListings', { token })} />
              <ActionCard icon={PackageCheck} color="#0EA5E9" label="My Orders" onPress={() => navigation.navigate('FarmerOrders', { token, role: 'farmer' })} />
            </ScrollView>
          </Animated.View>

          <Animated.View entering={FadeInUp.duration(600).delay(300).springify()} style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Recent Sales</Text>
              <TouchableOpacity onPress={() => navigation.navigate('FarmerOrders', { token, role: 'farmer' })}>
                <Text style={styles.seeAll}>See All</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.orderList}>
              {orders.slice(0, 3).map((order, i) => (
                <View key={order.id}>
                  <TouchableOpacity style={styles.rowCard} onPress={() => navigation.navigate('OrderDetails', { orderId: order.id, role: 'farmer', token })}>
                    <View style={styles.rowIconWrap}>
                      <PackageCheck size={20} color="#10B981" />
                    </View>
                    <View style={styles.rowInfo}>
                      <Text style={styles.rowTitle} numberOfLines={1}>{order.product || order.product_type || 'Crop Sale'}</Text>
                      <Text style={styles.rowSub}>{order.status || 'PENDING'}</Text>
                    </View>
                    <View style={styles.rowAmountWrap}>
                      <Text style={styles.rowAmount}>${Number(order.total_amount || order.amount || 0).toFixed(2)}</Text>
                      <ChevronRight size={16} color="#CBD5E1" />
                    </View>
                  </TouchableOpacity>
                  {i < Math.min(orders.length, 3) - 1 && <View style={styles.divider} />}
                </View>
              ))}
              {orders.length === 0 && (
                <View style={styles.emptyCard}>
                  <Text style={styles.emptyText}>You haven't made any sales yet. Create a new listing to start selling your produce.</Text>
                </View>
              )}
            </View>
          </Animated.View>
        </>
      )}
    </ScrollView>
  );
}

function Metric({ icon: Icon, color, label, value }) {
  return (
    <View style={styles.metricCard}>
      <View style={[styles.metricIconWrap, { backgroundColor: `${color}15` }]}>
        <Icon size={22} color={color} />
      </View>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

function ActionCard({ icon: Icon, color, label, onPress }) {
  return (
    <TouchableOpacity style={[styles.actionCard, { backgroundColor: color }]} onPress={onPress} activeOpacity={0.85}>
      <View style={styles.actionIconFloat}>
        <Icon size={32} color="rgba(255,255,255,0.2)" />
      </View>
      <View style={styles.actionIconContainer}>
        <Icon size={24} color="#FFF" />
      </View>
      <Text style={styles.actionText}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  content: { paddingBottom: 120 },

  hero: {
    backgroundColor: '#064E3B',
    borderBottomLeftRadius: 40, borderBottomRightRadius: 40,
    padding: 32, paddingTop: 60, paddingBottom: 40,
    shadowColor: '#064E3B', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.1, shadowRadius: 20, elevation: 10,
    position: 'relative', overflow: 'hidden'
  },
  heroGlow: { position: 'absolute', top: -50, right: -50, width: 200, height: 200, borderRadius: 100, backgroundColor: '#10B981', opacity: 0.2, transform: [{ scale: 1.5 }] },
  heroContent: { position: 'relative', zIndex: 2 },
  kicker: { color: '#34D399', fontSize: 12, fontWeight: '900', letterSpacing: 1.5, marginBottom: 8 },
  title: { color: '#FFFFFF', fontSize: 32, lineHeight: 38, fontWeight: '900', marginBottom: 12 },
  subtitle: { color: '#A7F3D0', fontSize: 15, lineHeight: 22, fontWeight: '500', maxWidth: '85%' },

  grid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 20, marginTop: -20, gap: 12 },
  metricCard: {
    width: (width - 52) / 2, backgroundColor: '#FFFFFF', borderRadius: 24, padding: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.05, shadowRadius: 16, elevation: 4,
  },
  metricIconWrap: { width: 44, height: 44, borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  metricValue: { color: '#0F172A', fontSize: 26, fontWeight: '900', marginBottom: 4 },
  metricLabel: { color: '#64748B', fontSize: 12, fontWeight: '700', textTransform: 'uppercase' },

  actionSection: { marginTop: 32 },
  chartSection: { marginTop: 32, paddingHorizontal: 24 },
  sectionTitle: { color: '#0F172A', fontSize: 18, fontWeight: '900', marginBottom: 16 },
  chartCard: {
    backgroundColor: '#FFFFFF', borderRadius: 24,
    shadowColor: '#000', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.04, shadowRadius: 20, elevation: 3,
    borderWidth: 1, borderColor: '#F1F5F9', padding: 16,
  },
  chart: { borderRadius: 16 },
  actionRow: { paddingHorizontal: 24, gap: 12 },
  actionCard: {
    width: 130, height: 130, borderRadius: 28, padding: 16, justifyContent: 'space-between',
    shadowColor: '#000', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.15, shadowRadius: 12, elevation: 6,
    position: 'relative', overflow: 'hidden'
  },
  actionIconFloat: { position: 'absolute', top: -10, right: -10 },
  actionIconContainer: { width: 48, height: 48, borderRadius: 24, backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center' },
  actionText: { color: '#FFFFFF', fontSize: 15, fontWeight: '800', lineHeight: 20 },

  section: { marginTop: 36, paddingHorizontal: 24 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  seeAll: { color: '#10B981', fontSize: 14, fontWeight: '800' },

  orderList: {
    backgroundColor: '#FFFFFF', borderRadius: 28,
    shadowColor: '#000', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.04, shadowRadius: 20, elevation: 3,
    borderWidth: 1, borderColor: '#F1F5F9'
  },
  rowCard: { padding: 20, flexDirection: 'row', alignItems: 'center' },
  rowIconWrap: { width: 44, height: 44, borderRadius: 16, backgroundColor: '#ECFDF5', justifyContent: 'center', alignItems: 'center', marginRight: 16 },
  rowInfo: { flex: 1 },
  rowTitle: { color: '#0F172A', fontSize: 16, fontWeight: '800', marginBottom: 4 },
  rowSub: { color: '#64748B', fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  rowAmountWrap: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  rowAmount: { color: '#0F172A', fontSize: 18, fontWeight: '900' },
  divider: { height: 1, backgroundColor: '#F1F5F9', marginHorizontal: 20 },

  emptyCard: { padding: 32, alignItems: 'center' },
  emptyText: { color: '#94A3B8', fontWeight: '500', lineHeight: 22, textAlign: 'center' },

  stateCard: { backgroundColor: '#FFFFFF', borderRadius: 28, padding: 40, marginHorizontal: 24, marginTop: 24, alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.04, shadowRadius: 20, elevation: 3 },
  errorText: { color: '#EF4444', textAlign: 'center', fontWeight: '800', marginBottom: 20, fontSize: 16 },
  primaryBtn: { backgroundColor: '#10B981', borderRadius: 16, paddingHorizontal: 24, paddingVertical: 14 },
  primaryText: { color: '#FFFFFF', fontWeight: '800', fontSize: 15 },
});
