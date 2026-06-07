import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  RefreshControl, SafeAreaView, ActivityIndicator,
} from 'react-native';
import {
  Truck as IconTruck, Package as IconPackage, 
  CheckCircle as IconCheckCircle, Clock as IconClock, 
  XCircle as IconXCircle, ChevronRight as IconChevronRight, 
  Inbox as IconInbox,
} from 'lucide-react-native';
import { theme } from '../styles';
import { getMyDeliveries } from '../api';

const STATUS_CONFIG = {
  picked_up:  { label: 'Picked Up',  color: '#F59E0B', bg: '#FFFBEB', icon: IconPackage,     progress: 40 },
  in_transit: { label: 'In Transit', color: '#29B6F6', bg: '#E1F5FE', icon: IconTruck,        progress: 65 },
  delivered:  { label: 'Delivered',  color: '#4CAF50', bg: '#F0FDF4', icon: IconCheckCircle,  progress: 100 },
  completed:  { label: 'Completed',  color: '#4CAF50', bg: '#F0FDF4', icon: IconCheckCircle,  progress: 100 },
  pending:    { label: 'Pending',    color: '#9E9E9E', bg: '#F5F5F5', icon: IconClock,        progress: 10 },
  cancelled:  { label: 'Cancelled',  color: '#EF4444', bg: '#FEF2F2', icon: IconXCircle,      progress: 0 },
};

function ProgressBar({ progress, color }) {
  return (
    <View style={styles.progressBg}>
      <View style={[styles.progressFill, { width: `${progress}%`, backgroundColor: color }]} />
    </View>
  );
}

const FILTERS = [
  { key: 'all',     label: 'All' },
  { key: 'active',  label: 'Active' },
  { key: 'pending', label: 'Pending' },
  { key: 'done',    label: 'Done' },
];

export default function DeliveriesScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');

  const fetchDeliveries = useCallback(async () => {
    try {
      setError('');
      const data = await getMyDeliveries(token);
      setDeliveries(Array.isArray(data) ? data : data?.deliveries || []);
    } catch (err) {
      setDeliveries([]);
      setError(err.message || 'Could not load deliveries from the server.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { fetchDeliveries(); }, [fetchDeliveries]);
  const onRefresh = useCallback(() => { setRefreshing(true); fetchDeliveries(); }, [fetchDeliveries]);

  const counts = {
    all:     deliveries.length,
    active:  deliveries.filter(d => ['in_transit', 'picked_up'].includes(d.status)).length,
    pending: deliveries.filter(d => d.status === 'pending').length,
    done:    deliveries.filter(d => ['delivered', 'completed'].includes(d.status)).length,
  };

  const filtered = filter === 'all' ? deliveries : deliveries.filter(d =>
    filter === 'active'  ? ['in_transit', 'picked_up'].includes(d.status) :
    filter === 'done'    ? ['delivered', 'completed'].includes(d.status) :
    d.status === filter
  );

  const activeDelivery = deliveries.find(d => ['in_transit', 'picked_up'].includes(d.status));

  const renderDelivery = ({ item }) => {
    const st = STATUS_CONFIG[item.status] || STATUS_CONFIG.pending;
    const Icon = st.icon;
    const isActive = ['in_transit', 'picked_up'].includes(item.status);

    return (
      <TouchableOpacity
        style={[styles.card, isActive && styles.cardActive]}
        onPress={() => navigation.navigate('DeliveryTracking', { delivery: item, token })}
        activeOpacity={0.75}
      >
        {/* Top row: route + status + price */}
        <View style={styles.cardTop}>
          <View style={styles.routeCol}>
            <View style={styles.routeRow}>
              <View style={[styles.dot, { backgroundColor: theme.colors.sky }]} />
              <Text style={styles.locationText} numberOfLines={1}>{item.pickup_location}</Text>
            </View>
            <View style={styles.routeConnector} />
            <View style={styles.routeRow}>
              <View style={[styles.dot, { backgroundColor: '#4CAF50' }]} />
              <Text style={styles.locationText} numberOfLines={1}>{item.delivery_location}</Text>
            </View>
          </View>
          <View style={styles.cardRight}>
            <View style={[styles.statusBadge, { backgroundColor: st.bg }]}>
              <Icon size={11} color={st.color} />
              <Text style={[styles.statusText, { color: st.color }]}>{st.label}</Text>
            </View>
            <Text style={styles.priceText}>${item.payment_amount}</Text>
          </View>
        </View>

        {/* Progress bar */}
        <View style={styles.progressSection}>
          <ProgressBar progress={st.progress} color={st.color} />
          <View style={styles.progressMeta}>
            <Text style={styles.progressLabel}>{st.progress}% complete</Text>
            {item.distance_km ? <Text style={styles.progressLabel}>{item.distance_km} km</Text> : null}
          </View>
        </View>

        {/* Footer chips */}
        <View style={styles.cardFooter}>
          <View style={styles.metaChip}>
            <IconPackage size={11} color="#666" />
            <Text style={styles.metaText}>{item.crop_type}</Text>
          </View>
          <View style={styles.metaChip}>
            <IconTruck size={11} color="#666" />
            <Text style={styles.metaText}>{item.weight_kg} kg</Text>
          </View>
          <View style={{ flex: 1 }} />
          <IconChevronRight size={18} color="#CCC" />
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Deliveries</Text>
        <Text style={styles.subtitle}>{deliveries.length} total</Text>
      </View>

      {/* Active delivery banner */}
      {activeDelivery && filter === 'all' && (
        <TouchableOpacity
          style={styles.activeBanner}
          onPress={() => navigation.navigate('DeliveryTracking', { delivery: activeDelivery, token })}
          activeOpacity={0.85}
        >
          <View style={styles.activePulse} />
          <IconTruck size={20} color="#FFF" />
          <View style={styles.activeBannerText}>
            <Text style={styles.activeTitle}>Active Delivery</Text>
            <Text style={styles.activeSub} numberOfLines={1}>
              {activeDelivery.pickup_location} → {activeDelivery.delivery_location}
            </Text>
          </View>
          <IconChevronRight size={20} color="rgba(255,255,255,0.7)" />
        </TouchableOpacity>
      )}

      {/* Filter tabs */}
      <View style={styles.filterRow}>
        {FILTERS.map(f => (
          <TouchableOpacity
            key={f.key}
            style={[styles.filterChip, filter === f.key && styles.filterActive]}
            onPress={() => setFilter(f.key)}
          >
            <Text style={[styles.filterText, filter === f.key && styles.filterTextActive]}>{f.label}</Text>
            {counts[f.key] > 0 && (
              <View style={[styles.filterBadge, filter === f.key && styles.filterBadgeActive]}>
                <Text style={[styles.filterBadgeText, filter === f.key && { color: theme.colors.sky }]}>
                  {counts[f.key]}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.loadingState}>
          <ActivityIndicator size="large" color={theme.colors.sky} />
          <Text style={styles.loadingText}>Loading deliveries...</Text>
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={item => String(item.id)}
          renderItem={renderDelivery}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.sky} />
          }
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <View style={styles.emptyIcon}>
                <IconInbox size={40} color="#CCC" />
              </View>
              <Text style={styles.emptyTitle}>{error ? 'Deliveries Could Not Load' : 'No Deliveries'}</Text>
              <Text style={styles.emptyText}>
                {error || (filter === 'all'
                  ? 'Accept jobs from the Jobs tab to start delivering'
                  : `No ${filter} deliveries found`)}
              </Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.gray50 },

  header: {
    paddingHorizontal: 20, paddingTop: 18, paddingBottom: 6,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end',
  },
  title: { fontSize: 30, fontWeight: '900', color: theme.colors.ink, letterSpacing: -0.8 },
  subtitle: { fontSize: 13, color: '#64748B', fontWeight: '700', marginBottom: 4 },

  activeBanner: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    marginHorizontal: 20, marginTop: 14, backgroundColor: theme.colors.sky,
    borderRadius: 24, padding: 18, ...theme.shadows.lg,
  },
  activePulse: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#4CAF50' },
  activeBannerText: { flex: 1 },
  activeTitle: { color: '#FFF', fontSize: 13, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.5 },
  activeSub: { color: 'rgba(255,255,255,0.82)', fontSize: 12, fontWeight: '700', marginTop: 4 },

  filterRow: { flexDirection: 'row', paddingHorizontal: 20, gap: 8, marginTop: 18, marginBottom: 14 },
  filterChip: {
    flexDirection: 'row', alignItems: 'center', gap: 5,
    paddingHorizontal: 14, paddingVertical: 10, borderRadius: 20,
    backgroundColor: '#FFF', borderWidth: 1, borderColor: '#E2E8F0',
  },
  filterActive: { backgroundColor: '#EAF6FF', borderColor: theme.colors.sky },
  filterText: { fontSize: 13, fontWeight: '800', color: '#64748B' },
  filterTextActive: { color: theme.colors.sky },
  filterBadge: {
    backgroundColor: '#F1F5F9', minWidth: 20, height: 20,
    borderRadius: 10, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 4,
  },
  filterBadgeActive: { backgroundColor: '#FFF' },
  filterBadgeText: { fontSize: 10, fontWeight: '800', color: '#999' },

  listContent: { paddingBottom: 120, paddingHorizontal: 20, paddingTop: 4 },

  card: {
    backgroundColor: '#FFF', borderRadius: 26, padding: 20, marginBottom: 14,
    borderWidth: 1, borderColor: '#E2E8F0', ...theme.shadows.md,
  },
  cardActive: { borderColor: '#BBDEFB', borderWidth: 2 },

  cardTop: { flexDirection: 'row', marginBottom: 14 },
  routeCol: { flex: 1 },
  routeRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  routeConnector: { width: 2, height: 10, backgroundColor: '#DCE6F2', marginLeft: 3, marginVertical: 3 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  locationText: { fontSize: 14, fontWeight: '800', color: theme.colors.ink, flex: 1 },
  cardRight: { alignItems: 'flex-end', gap: 6 },
  statusBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12,
  },
  statusText: { fontSize: 11, fontWeight: '800' },
  priceText: { fontSize: 20, fontWeight: '900', color: theme.colors.sky },

  progressSection: { marginBottom: 12 },
  progressBg: { height: 6, backgroundColor: '#E2E8F0', borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 3 },
  progressMeta: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 5 },
  progressLabel: { fontSize: 10, fontWeight: '700', color: '#94A3B8' },

  cardFooter: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingTop: 12, borderTopWidth: 1, borderTopColor: '#EEF2F7',
  },
  metaChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#F8FAFC', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 10, borderWidth: 1, borderColor: '#E2E8F0',
  },
  metaText: { fontSize: 11, fontWeight: '800', color: '#475569' },

  loadingState: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#64748B', marginTop: 12, fontWeight: '700', fontSize: 14 },

  emptyState: { alignItems: 'center', paddingTop: 60, paddingHorizontal: 24 },
  emptyIcon: {
    width: 88, height: 88, borderRadius: 44, backgroundColor: '#FFFFFF',
    justifyContent: 'center', alignItems: 'center', marginBottom: 16,
    borderWidth: 1, borderColor: '#E2E8F0',
  },
  emptyTitle: { fontSize: 18, fontWeight: '900', color: '#475569' },
  emptyText: { fontSize: 13, color: '#94A3B8', marginTop: 8, textAlign: 'center', lineHeight: 20 },
});
