import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Bell, ClipboardList, Handshake, PlusCircle, ShieldCheck, Wallet } from 'lucide-react-native';
import { getMyListings, getOffersReceived, getProfile, getTransactions, getWalletBalance } from '../api';
import { theme } from '../styles';

function totalAmount(items) {
  return items.reduce((sum, item) => sum + Number(item.total_amount || item.amount || 0), 0);
}

export default function FarmerDashboardScreen({ navigation, route }) {
  const { token, profile: initialProfile = {} } = route.params || {};
  const [profile, setProfile] = useState(initialProfile);
  const [listings, setListings] = useState([]);
  const [offers, setOffers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setError('');
      const [profileData, listingData, offerData, orderData, walletData] = await Promise.all([
        getProfile(token),
        getMyListings(token),
        getOffersReceived(token),
        getTransactions(token),
        getWalletBalance(token),
      ]);
      setProfile(profileData || {});
      setListings(Array.isArray(listingData) ? listingData : listingData?.data || []);
      setOffers(Array.isArray(offerData) ? offerData : offerData?.data || []);
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
  const pendingOffers = offers.filter((item) => String(item.status || '').toUpperCase() === 'PENDING').length;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      <View style={styles.hero}>
        <Text style={styles.kicker}>FARMER PORTAL</Text>
        <Text style={styles.title}>Welcome back, {profile.full_name || profile.name || 'Farmer'}.</Text>
        <Text style={styles.subtitle}>Your listings, offers, wallet, and trust score are loaded from the backend.</Text>
      </View>

      {loading ? (
        <View style={styles.stateCard}>
          <ActivityIndicator color={theme.colors.green} />
          <Text style={styles.stateText}>Loading farmer dashboard...</Text>
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
          <View style={styles.grid}>
            <Metric icon={ClipboardList} label="Active listings" value={activeListings} />
            <Metric icon={Handshake} label="Pending offers" value={pendingOffers} />
            <Metric icon={Wallet} label="Wallet" value={`$${Number(wallet?.available_usd ?? wallet?.available ?? 0).toFixed(2)}`} />
            <Metric icon={ShieldCheck} label="Trust score" value={`${profile.trust_score || 0}/100`} />
          </View>

          <View style={styles.actionRow}>
            <Action icon={PlusCircle} label="Create Listing" onPress={() => navigation.navigate('CreateListing', { token })} />
            <Action icon={Handshake} label="View Offers" onPress={() => navigation.navigate('OffersReceived', { token })} />
            <Action icon={Bell} label="Disputes" onPress={() => navigation.navigate('Disputes', { token })} />
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recent orders</Text>
            {orders.slice(0, 3).map((order) => (
              <TouchableOpacity key={order.id} style={styles.rowCard} onPress={() => navigation.navigate('OrderDetails', { orderId: order.id, role: 'farmer', token })}>
                <View>
                  <Text style={styles.rowTitle}>{order.product || order.product_type || 'Crop order'}</Text>
                  <Text style={styles.rowSub}>{order.status || 'PENDING'}</Text>
                </View>
                <Text style={styles.rowAmount}>${Number(order.total_amount || order.amount || 0).toFixed(2)}</Text>
              </TouchableOpacity>
            ))}
            {orders.length === 0 && <Text style={styles.emptyText}>No orders yet. New accepted offers will appear here.</Text>}
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Sales value</Text>
            <View style={styles.salesCard}>
              <Text style={styles.salesValue}>${totalAmount(orders).toFixed(2)}</Text>
              <Text style={styles.salesLabel}>Total value across your loaded orders</Text>
            </View>
          </View>
        </>
      )}
    </ScrollView>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <View style={styles.metricCard}>
      <Icon size={20} color={theme.colors.green} />
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

function Action({ icon: Icon, label, onPress }) {
  return (
    <TouchableOpacity style={styles.actionCard} onPress={onPress}>
      <Icon size={20} color="#fff" />
      <Text style={styles.actionText}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F0DE' },
  content: { padding: 20, paddingBottom: 120, paddingTop: 28 },
  hero: { backgroundColor: '#19351f', borderRadius: 28, padding: 24, marginBottom: 18 },
  kicker: { color: theme.colors.gold, fontSize: 11, fontWeight: '900', letterSpacing: 1.5 },
  title: { color: '#fff', fontSize: 28, lineHeight: 34, fontWeight: '900', marginTop: 10 },
  subtitle: { color: '#d9ead3', fontSize: 14, lineHeight: 21, marginTop: 10 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  metricCard: { width: '48%', backgroundColor: '#fff', borderRadius: 22, padding: 16, borderWidth: 1, borderColor: '#e5e7eb' },
  metricValue: { color: '#111827', fontSize: 22, fontWeight: '900', marginTop: 10 },
  metricLabel: { color: '#64748b', fontSize: 12, fontWeight: '800', textTransform: 'uppercase', marginTop: 4 },
  actionRow: { flexDirection: 'row', gap: 10, marginTop: 18 },
  actionCard: { flex: 1, backgroundColor: theme.colors.green, borderRadius: 18, padding: 14, alignItems: 'center', gap: 8 },
  actionText: { color: '#fff', fontSize: 12, fontWeight: '900', textAlign: 'center' },
  section: { marginTop: 24 },
  sectionTitle: { color: '#111827', fontSize: 16, fontWeight: '900', marginBottom: 12 },
  rowCard: { backgroundColor: '#fff', borderRadius: 18, padding: 16, marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderWidth: 1, borderColor: '#e5e7eb' },
  rowTitle: { color: '#111827', fontSize: 15, fontWeight: '900' },
  rowSub: { color: '#64748b', fontSize: 12, fontWeight: '700', marginTop: 4 },
  rowAmount: { color: theme.colors.green, fontSize: 16, fontWeight: '900' },
  salesCard: { backgroundColor: '#111827', borderRadius: 24, padding: 24 },
  salesValue: { color: '#fff', fontSize: 36, fontWeight: '900' },
  salesLabel: { color: '#cbd5e1', fontSize: 13, marginTop: 6, fontWeight: '700' },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center' },
  stateText: { color: '#64748b', marginTop: 10, fontWeight: '700' },
  errorText: { color: theme.colors.red, textAlign: 'center', fontWeight: '800', marginBottom: 14 },
  emptyText: { color: '#64748b', fontWeight: '700', lineHeight: 20 },
  primaryBtn: { backgroundColor: theme.colors.green, borderRadius: 14, paddingHorizontal: 20, paddingVertical: 12 },
  primaryText: { color: '#fff', fontWeight: '900' },
});
