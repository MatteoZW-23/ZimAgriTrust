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

  const fetchDeliveries = useCallback(async () => {
    try {
      const data = await getMyDeliveries(token);
      setDeliveries(Array.isArray(data) ? data : data?.deliveries || []);
    } catch {
      setDeliveries([
        { id: '1', pickup_location: 'Harare - Mbare', delivery_location: 'Chitungwiza', status: 'in_transit', crop_type: 'Maize', weight_kg: 1200, payment_amount: 45, distance_km: 30 },
        { id: '2', pickup_location: 'Bulawayo - Central', delivery_location: 'Victoria Falls', status: 'delivered', crop_type: 'Tobacco', weight_kg: 800, payment_amount: 120, distance_km: 440 },
        { id: '3', pickup_location: 'Gweru - Market', delivery_location: 'Kwekwe', status: 'pending', crop_type: 'Groundnuts', weight_kg: 500, payment_amount: 30, distance_km: 60 },
        { id: '4', pickup_location: 'Chinhoyi - Depot', delivery_location: 'Kariba Town', status: 'picked_up', crop_type: 'Soya Beans', weight_kg: 900, payment_amount: 75, distance_km: 210 },
      ]);
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
              <Text style={styles.emptyTitle}>No Deliveries</Text>
              <Text style={styles.emptyText}>
                {filter === 'all'
                  ? 'Accept jobs from the Jobs tab to start delivering'
                  : `No ${filter} deliveries found`}
              </Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },

  header: {
    paddingHorizontal: 20, paddingTop: 16, paddingBottom: 4,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end',
  },
  title: { fontSize: 28, fontWeight: '900', color: theme.colors.dark },
  subtitle: { fontSize: 13, color: '#999', fontWeight: '600', marginBottom: 4 },

  activeBanner: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    marginHorizontal: 20, marginTop: 12, backgroundColor: theme.colors.sky,
    borderRadius: 16, padding: 16, ...theme.shadows.md,
  },
  activePulse: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#4CAF50' },
  activeBannerText: { flex: 1 },
  activeTitle: { color: '#FFF', fontSize: 13, fontWeight: '800' },
  activeSub: { color: 'rgba(255,255,255,0.8)', fontSize: 12, fontWeight: '500', marginTop: 2 },

  filterRow: { flexDirection: 'row', paddingHorizontal: 20, gap: 8, marginTop: 16, marginBottom: 12 },
  filterChip: {
    flexDirection: 'row', alignItems: 'center', gap: 5,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20,
    backgroundColor: '#FFF', borderWidth: 1, borderColor: '#F0F0F0',
  },
  filterActive: { backgroundColor: '#E1F5FE', borderColor: theme.colors.sky },
  filterText: { fontSize: 13, fontWeight: '700', color: '#999' },
  filterTextActive: { color: theme.colors.sky },
  filterBadge: {
    backgroundColor: '#F0F0F0', minWidth: 20, height: 20,
    borderRadius: 10, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 4,
  },
  filterBadgeActive: { backgroundColor: '#FFF' },
  filterBadgeText: { fontSize: 10, fontWeight: '800', color: '#999' },

  listContent: { paddingBottom: 120, paddingHorizontal: 20, paddingTop: 4 },

  card: {
    backgroundColor: '#FFF', borderRadius: 20, padding: 18, marginBottom: 12,
    borderWidth: 1, borderColor: '#F0F0F0', ...theme.shadows.xs,
  },
  cardActive: { borderColor: '#BBDEFB', borderWidth: 2 },

  cardTop: { flexDirection: 'row', marginBottom: 14 },
  routeCol: { flex: 1 },
  routeRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  routeConnector: { width: 2, height: 10, backgroundColor: '#E8E8E8', marginLeft: 3, marginVertical: 3 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  locationText: { fontSize: 14, fontWeight: '700', color: theme.colors.dark, flex: 1 },
  cardRight: { alignItems: 'flex-end', gap: 6 },
  statusBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 9, paddingVertical: 4, borderRadius: 10,
  },
  statusText: { fontSize: 11, fontWeight: '800' },
  priceText: { fontSize: 18, fontWeight: '900', color: theme.colors.sky },

  progressSection: { marginBottom: 12 },
  progressBg: { height: 5, backgroundColor: '#F0F0F0', borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 3 },
  progressMeta: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 5 },
  progressLabel: { fontSize: 10, fontWeight: '600', color: '#BBB' },

  cardFooter: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingTop: 10, borderTopWidth: 1, borderTopColor: '#F5F5F5',
  },
  metaChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#F8F9FA', paddingHorizontal: 9, paddingVertical: 4, borderRadius: 8,
  },
  metaText: { fontSize: 11, fontWeight: '700', color: '#666' },

  loadingState: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#999', marginTop: 12, fontWeight: '600', fontSize: 14 },

  emptyState: { alignItems: 'center', paddingTop: 60 },
  emptyIcon: {
    width: 88, height: 88, borderRadius: 44, backgroundColor: '#F5F5F5',
    justifyContent: 'center', alignItems: 'center', marginBottom: 16,
  },
  emptyTitle: { fontSize: 18, fontWeight: '800', color: '#999' },
  emptyText: { fontSize: 13, color: '#CCC', marginTop: 8, textAlign: 'center', lineHeight: 20 },
});
