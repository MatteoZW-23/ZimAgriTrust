import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  SafeAreaView, RefreshControl, ActivityIndicator
} from 'react-native';
import { getTransactions } from '../api';
import { theme } from '../styles';

const STATUS_CONFIG = {
  COMPLETED:  { color: '#22c55e', bg: '#f0fdf4', icon: '🟢', label: 'COMPLETED' },
  DELIVERED:  { color: '#3b82f6', bg: '#eff6ff', icon: '🟡', label: 'DELIVERED' },
  IN_ESCROW:  { color: '#f59e0b', bg: '#fffbeb', icon: '🟡', label: 'IN ESCROW' },
  DISPUTED:   { color: '#ef4444', bg: '#fef2f2', icon: '🔴', label: 'DISPUTED' },
  PENDING:    { color: '#f59e0b', bg: '#fffbeb', icon: '⏳', label: 'PENDING' },
  CANCELLED:  { color: '#94a3b8', bg: '#f8fafc', icon: '⚫', label: 'CANCELLED' },
};

function getStatusConfig(status = '') {
  return STATUS_CONFIG[status.toUpperCase()] || { color: '#64748b', bg: '#f8fafc', icon: '⚪', label: status };
}

export default function MyOrdersScreen({ navigation, route }) {
  const { token, role = 'farmer' } = route.params || {};
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  const load = useCallback(async () => {
    try {
      setError('');
      const data = await getTransactions(token);
      setOrders(Array.isArray(data) ? data : data?.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load orders.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  const tabs = [
    { key: 'all', label: 'All' },
    { key: 'active', label: 'Active' },
    { key: 'completed', label: 'Done' },
    { key: 'disputed', label: 'Disputed' },
  ];

  const filtered = orders.filter(o => {
    if (activeTab === 'all') return true;
    if (activeTab === 'active') return ['PENDING', 'IN_ESCROW', 'DELIVERED'].includes((o.status || '').toUpperCase());
    if (activeTab === 'completed') return (o.status || '').toUpperCase() === 'COMPLETED';
    if (activeTab === 'disputed') return (o.status || '').toUpperCase() === 'DISPUTED';
    return true;
  });

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>My Orders</Text>
        <View style={{ width: 60 }} />
      </View>

      {/* Tabs */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabsScroll} contentContainerStyle={styles.tabs}>
        {tabs.map(tab => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>{tab.label}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.green} />
          <Text style={styles.loadingText}>Loading orders...</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={load}>
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.green} />}
          contentContainerStyle={{ paddingBottom: 120 }}
        >
          {filtered.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>📦</Text>
              <Text style={styles.emptyTitle}>No orders here</Text>
              <Text style={styles.emptyText}>Your orders will appear once you start trading.</Text>
            </View>
          ) : (
            filtered.map(order => (
              <OrderCard
                key={order.id}
                order={order}
                role={role}
                onPress={() => navigation.navigate('OrderDetails', { orderId: order.id, role, token })}
                onConfirm={() => navigation.navigate('ConfirmDelivery', { orderId: order.id, token })}
                onRate={() => navigation.navigate('RateUser', { orderId: order.id, token, role })}
                onDispute={() => navigation.navigate('OrderDetails', { orderId: order.id, role, token })}
              />
            ))
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function OrderCard({ order, role, onPress, onConfirm, onRate, onDispute }) {
  const status = order.status || 'PENDING';
  const cfg = getStatusConfig(status);
  const crop = order.product_type || order.crop || 'Order';
  const qty = order.quantity ? `${Number(order.quantity).toLocaleString()} ${order.quantity_unit || 'kg'}` : '';
  const amount = order.total_amount ? `$${Number(order.total_amount).toFixed(2)}` : order.amount ? `$${Number(order.amount).toFixed(2)}` : '—';
  const counterparty = role === 'farmer' ? (order.buyer_name || 'Buyer') : (order.seller_name || order.farmer_name || 'Farmer');
  const date = order.created_at ? new Date(order.created_at).toLocaleDateString('en-ZW', { day: 'numeric', month: 'short', year: 'numeric' }) : '';
  const shortId = order.id ? `#TRX-${String(order.id).slice(0, 6).toUpperCase()}` : '#—';
  const isReviewed = order.is_reviewed || order.reviewed;

  return (
    <TouchableOpacity style={[styles.card, { borderLeftColor: cfg.color, borderLeftWidth: 4 }]} onPress={onPress} activeOpacity={0.85}>
      <View style={styles.cardTop}>
        <View style={[styles.statusBadge, { backgroundColor: cfg.bg }]}>
          <Text style={[styles.statusText, { color: cfg.color }]}>{cfg.icon} {cfg.label}</Text>
        </View>
        <Text style={styles.orderId}>{shortId}</Text>
      </View>

      <Text style={styles.cropName}>{crop}{qty ? ` | ${qty}` : ''}</Text>
      <Text style={styles.counterparty}>{role === 'farmer' ? 'Buyer' : 'Farmer'}: {counterparty}</Text>
      {date ? <Text style={styles.date}>{date}</Text> : null}

      <View style={styles.amountRow}>
        <Text style={styles.amount}>{amount}</Text>
        {order.escrow_held && <Text style={styles.escrowTag}>🛡️ In Escrow</Text>}
      </View>

      <View style={styles.actions}>
        {status.toUpperCase() === 'DELIVERED' && (
          <TouchableOpacity style={styles.primaryAction} onPress={onConfirm}>
            <Text style={styles.primaryActionText}>✅ Confirm Delivery</Text>
          </TouchableOpacity>
        )}
        {status.toUpperCase() === 'COMPLETED' && !isReviewed && (
          <TouchableOpacity style={[styles.primaryAction, { backgroundColor: '#f59e0b' }]} onPress={onRate}>
            <Text style={styles.primaryActionText}>⭐ Rate {role === 'farmer' ? 'Buyer' : 'Farmer'}</Text>
          </TouchableOpacity>
        )}
        {['PENDING', 'IN_ESCROW', 'DELIVERED'].includes(status.toUpperCase()) && (
          <TouchableOpacity style={styles.secondaryAction} onPress={onDispute}>
            <Text style={styles.secondaryActionText}>⚠️ Dispute</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={styles.detailAction} onPress={onPress}>
          <Text style={styles.detailActionText}>View Details →</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 24, paddingTop: 60 },
  back: { fontSize: 16, fontWeight: '700', color: theme.colors.sky },
  title: { fontSize: 18, fontWeight: '900', color: theme.colors.black },
  tabsScroll: { maxHeight: 56 },
  tabs: { paddingHorizontal: 20, gap: 8, alignItems: 'center' },
  tab: { paddingHorizontal: 18, paddingVertical: 8, borderRadius: 20, backgroundColor: '#f1f5f9', borderWidth: 1, borderColor: '#e2e8f0' },
  tabActive: { backgroundColor: theme.colors.green, borderColor: theme.colors.green },
  tabText: { fontSize: 13, fontWeight: '800', color: '#64748b' },
  tabTextActive: { color: '#fff' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  loadingText: { marginTop: 12, color: '#64748b', fontWeight: '600' },
  errorText: { color: '#ef4444', fontWeight: '700', textAlign: 'center', marginBottom: 16 },
  retryBtn: { backgroundColor: theme.colors.green, paddingHorizontal: 24, paddingVertical: 12, borderRadius: 12 },
  retryText: { color: '#fff', fontWeight: '800' },
  empty: { alignItems: 'center', paddingTop: 80, paddingHorizontal: 40 },
  emptyIcon: { fontSize: 64, marginBottom: 16 },
  emptyTitle: { fontSize: 22, fontWeight: '900', color: theme.colors.black, marginBottom: 8 },
  emptyText: { fontSize: 14, color: '#64748b', textAlign: 'center', lineHeight: 22 },
  card: { marginHorizontal: 20, marginBottom: 14, backgroundColor: '#fff', borderRadius: 20, borderWidth: 1, borderColor: '#e5e7eb', padding: 20, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.06, shadowRadius: 12, elevation: 3 },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  statusText: { fontSize: 11, fontWeight: '900' },
  orderId: { fontSize: 11, fontWeight: '800', color: '#94a3b8' },
  cropName: { fontSize: 17, fontWeight: '900', color: theme.colors.black, marginBottom: 4 },
  counterparty: { fontSize: 13, color: '#475569', fontWeight: '600', marginBottom: 2 },
  date: { fontSize: 12, color: '#94a3b8', fontWeight: '600', marginBottom: 8 },
  amountRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 14 },
  amount: { fontSize: 20, fontWeight: '900', color: theme.colors.black },
  escrowTag: { fontSize: 12, color: '#f59e0b', fontWeight: '800' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  primaryAction: { backgroundColor: theme.colors.green, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12 },
  primaryActionText: { color: '#fff', fontWeight: '900', fontSize: 12 },
  secondaryAction: { backgroundColor: '#fef2f2', paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12, borderWidth: 1, borderColor: '#fecaca' },
  secondaryActionText: { color: '#ef4444', fontWeight: '900', fontSize: 12 },
  detailAction: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12, borderWidth: 1, borderColor: '#e2e8f0' },
  detailActionText: { color: '#475569', fontWeight: '800', fontSize: 12 },
});
