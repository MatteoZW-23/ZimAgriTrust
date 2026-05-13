import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Bookmark, HandCoins, PackageCheck, Search, ShieldCheck, Wallet } from 'lucide-react-native';
import { getOffersMade, getProfile, getSavedListings, getTransactions, getWalletBalance } from '../api';
import { theme } from '../styles';

export default function BuyerDashboardScreen({ navigation, route }) {
  const { token, profile: initialProfile = {} } = route.params || {};
  const [profile, setProfile] = useState(initialProfile);
  const [offers, setOffers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [saved, setSaved] = useState([]);
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setError('');
      const [profileData, offerData, orderData, savedData, walletData] = await Promise.all([
        getProfile(token),
        getOffersMade(token),
        getTransactions(token),
        getSavedListings(token).catch(() => []),
        getWalletBalance(token),
      ]);
      setProfile(profileData || {});
      setOffers(Array.isArray(offerData) ? offerData : offerData?.data || []);
      setOrders(Array.isArray(orderData) ? orderData : orderData?.data || []);
      setSaved(Array.isArray(savedData) ? savedData : savedData?.data || []);
      setWallet(walletData || null);
    } catch (err) {
      setError(err.message || 'Could not load your buyer dashboard.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const pendingOffers = offers.filter((item) => String(item.status || '').toUpperCase() === 'PENDING').length;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      <View style={styles.hero}>
        <Text style={styles.kicker}>BUYER PORTAL</Text>
        <Text style={styles.title}>Find verified crops, {profile.full_name || profile.name || 'Buyer'}.</Text>
        <Text style={styles.subtitle}>Track offers, escrow orders, wallet balance, and trusted sellers from one app.</Text>
      </View>

      {loading ? (
        <View style={styles.stateCard}>
          <ActivityIndicator color={theme.colors.sky} />
          <Text style={styles.stateText}>Loading buyer dashboard...</Text>
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
            <Metric icon={HandCoins} label="Pending offers" value={pendingOffers} />
            <Metric icon={PackageCheck} label="Orders" value={orders.length} />
            <Metric icon={Bookmark} label="Saved" value={saved.length} />
            <Metric icon={Wallet} label="Wallet" value={`$${Number(wallet?.available_usd ?? wallet?.available ?? 0).toFixed(2)}`} />
          </View>

          <View style={styles.actionRow}>
            <Action icon={Search} label="Browse Market" onPress={() => navigation.navigate('Marketplace', { token, role: 'buyer' })} />
            <Action icon={HandCoins} label="My Offers" onPress={() => navigation.navigate('MyOffers', { token })} />
            <Action icon={ShieldCheck} label="Saved Listings" onPress={() => navigation.navigate('SavedListings', { token })} />
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recent orders</Text>
            {orders.slice(0, 3).map((order) => (
              <TouchableOpacity key={order.id} style={styles.rowCard} onPress={() => navigation.navigate('OrderDetails', { orderId: order.id, role: 'buyer', token })}>
                <View>
                  <Text style={styles.rowTitle}>{order.product || order.product_type || 'Crop order'}</Text>
                  <Text style={styles.rowSub}>{order.status || 'PENDING'}</Text>
                </View>
                <Text style={styles.rowAmount}>${Number(order.total_amount || order.amount || 0).toFixed(2)}</Text>
              </TouchableOpacity>
            ))}
            {orders.length === 0 && <Text style={styles.emptyText}>No orders yet. Accepted offers and escrow purchases will appear here.</Text>}
          </View>
        </>
      )}
    </ScrollView>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <View style={styles.metricCard}>
      <Icon size={20} color={theme.colors.sky} />
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
  container: { flex: 1, backgroundColor: '#eff6ff' },
  content: { padding: 20, paddingBottom: 120, paddingTop: 28 },
  hero: { backgroundColor: '#0f2f45', borderRadius: 28, padding: 24, marginBottom: 18 },
  kicker: { color: theme.colors.gold, fontSize: 11, fontWeight: '900', letterSpacing: 1.5 },
  title: { color: '#fff', fontSize: 28, lineHeight: 34, fontWeight: '900', marginTop: 10 },
  subtitle: { color: '#d7efff', fontSize: 14, lineHeight: 21, marginTop: 10 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  metricCard: { width: '48%', backgroundColor: '#fff', borderRadius: 22, padding: 16, borderWidth: 1, borderColor: '#dbeafe' },
  metricValue: { color: '#111827', fontSize: 22, fontWeight: '900', marginTop: 10 },
  metricLabel: { color: '#64748b', fontSize: 12, fontWeight: '800', textTransform: 'uppercase', marginTop: 4 },
  actionRow: { flexDirection: 'row', gap: 10, marginTop: 18 },
  actionCard: { flex: 1, backgroundColor: theme.colors.sky, borderRadius: 18, padding: 14, alignItems: 'center', gap: 8 },
  actionText: { color: '#fff', fontSize: 12, fontWeight: '900', textAlign: 'center' },
  section: { marginTop: 24 },
  sectionTitle: { color: '#111827', fontSize: 16, fontWeight: '900', marginBottom: 12 },
  rowCard: { backgroundColor: '#fff', borderRadius: 18, padding: 16, marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderWidth: 1, borderColor: '#dbeafe' },
  rowTitle: { color: '#111827', fontSize: 15, fontWeight: '900' },
  rowSub: { color: '#64748b', fontSize: 12, fontWeight: '700', marginTop: 4 },
  rowAmount: { color: theme.colors.sky, fontSize: 16, fontWeight: '900' },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center' },
  stateText: { color: '#64748b', marginTop: 10, fontWeight: '700' },
  errorText: { color: theme.colors.red, textAlign: 'center', fontWeight: '800', marginBottom: 14 },
  emptyText: { color: '#64748b', fontWeight: '700', lineHeight: 20 },
  primaryBtn: { backgroundColor: theme.colors.sky, borderRadius: 14, paddingHorizontal: 20, paddingVertical: 12 },
  primaryText: { color: '#fff', fontWeight: '900' },
});
