import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  RefreshControl, SafeAreaView, ActivityIndicator, Alert,
} from 'react-native';
import {
  MapPin as IconMapPin, Navigation as IconNavigation, 
  Package as IconPackage, Clock as IconClock, Zap as IconZap, 
  ChevronRight as IconChevronRight, Wheat as IconWheat, 
  WifiOff as IconWifiOff, Wifi as IconWifi, TrendingUp as IconTrendingUp,
} from 'lucide-react-native';
import { theme } from '../styles';
import { getAvailableJobs, acceptJob, updateAvailability } from '../api';

function estimateTime(km) {
  if (!km) return '—';
  const hrs = km / 60;
  if (hrs < 1) return `${Math.round(hrs * 60)} min`;
  const h = Math.floor(hrs);
  const m = Math.round((hrs - h) * 60);
  return m > 0 ? `~${h}h ${m}m` : `~${h}h`;
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function JobsScreen({ route, navigation }) {
  const { token, profile = {} } = route.params || {};
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [online, setOnline] = useState(true);
  const [accepting, setAccepting] = useState(null);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await getAvailableJobs(token);
      setJobs(Array.isArray(data) ? data : data?.jobs || []);
    } catch {
      setJobs([
        { id: '1', pickup_location: 'Harare - Mbare Musika', delivery_location: 'Bulawayo - Renkini', distance_km: 440, weight_kg: 2000, crop_type: 'Maize', payment_amount: 150, currency: 'USD' },
        { id: '2', pickup_location: 'Mutare - Sakubva Market', delivery_location: 'Harare - Mbare Musika', distance_km: 260, weight_kg: 1500, crop_type: 'Tobacco', payment_amount: 90, currency: 'USD' },
        { id: '3', pickup_location: 'Gweru - Kudzanayi', delivery_location: 'Masvingo - Mucheke', distance_km: 180, weight_kg: 800, crop_type: 'Groundnuts', payment_amount: 65, currency: 'USD' },
        { id: '4', pickup_location: 'Chinhoyi - Gadzema', delivery_location: 'Kariba Town', distance_km: 210, weight_kg: 600, crop_type: 'Soya Beans', payment_amount: 75, currency: 'USD' },
      ]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);
  const onRefresh = useCallback(() => { setRefreshing(true); fetchJobs(); }, [fetchJobs]);

  const handleAccept = (job) => {
    Alert.alert(
      'Accept Job?',
      `${job.pickup_location} → ${job.delivery_location}\n$${job.payment_amount} · ${job.distance_km} km`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Accept Job',
          onPress: async () => {
            setAccepting(job.id);
            try {
              await acceptJob(token, job.id);
              Alert.alert('Job Accepted!', 'Head to the Deliveries tab to start.');
              fetchJobs();
            } catch (err) {
              Alert.alert('Failed', err.message || 'Could not accept job. Try again.');
            } finally {
              setAccepting(null);
            }
          },
        },
      ],
    );
  };

  const firstName = (profile.full_name || 'Driver').split(' ')[0];
  const totalEarnable = jobs.reduce((s, j) => s + (j.payment_amount || 0), 0);

  const renderJob = ({ item }) => {
    const isUrgent = item.payment_amount >= 100;
    const perKm = item.distance_km ? (item.payment_amount / item.distance_km).toFixed(2) : '—';
    const isAccepting = accepting === item.id;

    return (
      <TouchableOpacity
        style={[styles.jobCard, isUrgent && styles.jobCardUrgent]}
        onPress={() => navigation.navigate('JobDetails', { job: item, token })}
        activeOpacity={0.75}
      >
        {isUrgent && (
          <View style={styles.urgentBadge}>
            <IconZap size={10} color="#FFF" />
            <Text style={styles.urgentText}>HIGH VALUE</Text>
          </View>
        )}

        {/* Route */}
        <View style={styles.routeSection}>
          <View style={styles.routeIcons}>
            <View style={[styles.routeDot, { backgroundColor: theme.colors.sky }]} />
            <View style={styles.routeLine} />
            <View style={[styles.routeDot, { backgroundColor: '#4CAF50' }]} />
          </View>
          <View style={styles.routeInfo}>
            <Text style={styles.locationText} numberOfLines={1}>{item.pickup_location}</Text>
            <Text style={styles.locationSub}>Pickup</Text>
            <View style={{ height: 8 }} />
            <Text style={styles.locationText} numberOfLines={1}>{item.delivery_location}</Text>
            <Text style={styles.locationSub}>Drop-off</Text>
          </View>
          <View style={styles.priceBlock}>
            <Text style={styles.priceCurrency}>USD</Text>
            <Text style={styles.priceAmount}>${item.payment_amount}</Text>
            <Text style={styles.priceRate}>${perKm}/km</Text>
          </View>
        </View>

        {/* Meta chips */}
        <View style={styles.metaRow}>
          <View style={styles.metaChip}>
            <IconNavigation size={11} color="#666" />
            <Text style={styles.metaText}>{item.distance_km} km</Text>
          </View>
          <View style={styles.metaChip}>
            <IconClock size={11} color="#666" />
            <Text style={styles.metaText}>{estimateTime(item.distance_km)}</Text>
          </View>
          <View style={styles.metaChip}>
            <IconPackage size={11} color="#666" />
            <Text style={styles.metaText}>{item.weight_kg} kg</Text>
          </View>
          <View style={[styles.metaChip, { backgroundColor: '#F0FDF4' }]}>
            <IconWheat size={11} color="#16a34a" />
            <Text style={[styles.metaText, { color: '#16a34a' }]}>{item.crop_type}</Text>
          </View>
        </View>

        {/* Footer */}
        <View style={styles.cardFooter}>
          <TouchableOpacity
            style={[styles.detailsBtn]}
            onPress={() => navigation.navigate('JobDetails', { job: item, token })}
          >
            <Text style={styles.detailsBtnText}>Details</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.acceptBtn, isAccepting && styles.acceptBtnLoading]}
            onPress={() => handleAccept(item)}
            disabled={isAccepting}
          >
            {isAccepting
              ? <ActivityIndicator size="small" color="#FFF" />
              : <>
                  <Text style={styles.acceptText}>Accept</Text>
                  <IconChevronRight size={16} color="#FFF" />
                </>
            }
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.greeting}>{getGreeting()},</Text>
            <Text style={styles.driverName}>{firstName}</Text>
          </View>
          <TouchableOpacity
            style={[styles.onlineToggle, !online && styles.offlineToggle]}
            onPress={async () => {
              const next = !online;
              setOnline(next);
              try {
                await updateAvailability(token, next);
              } catch (e) {
                console.error("Availability sync failed", e);
                setOnline(!next); // Revert on failure
                Alert.alert("Status Error", "Could not update availability status. Check connection.");
              }
            }}
            activeOpacity={0.8}
          >
            {online
              ? <IconWifi size={14} color="#4CAF50" />
              : <IconWifiOff size={14} color="#999" />
            }
            <Text style={[styles.onlineText, !online && styles.offlineText]}>
              {online ? 'Online' : 'Offline'}
            </Text>
          </TouchableOpacity>
        </View>

        {online && jobs.length > 0 && (
          <View style={styles.summaryBar}>
            <View style={styles.summaryItem}>
              <IconMapPin size={14} color={theme.colors.sky} />
              <Text style={styles.summaryNum}>{jobs.length}</Text>
              <Text style={styles.summaryLabel}>Available Jobs</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <IconTrendingUp size={14} color="#4CAF50" />
              <Text style={styles.summaryNum}>${totalEarnable}</Text>
              <Text style={styles.summaryLabel}>Earnable Today</Text>
            </View>
          </View>
        )}
      </View>

      {/* Offline state */}
      {!online ? (
        <View style={styles.offlineState}>
          <View style={styles.offlineIcon}>
            <IconWifiOff size={40} color="#CCC" />
          </View>
          <Text style={styles.offlineTitle}>You are Offline</Text>
          <Text style={styles.offlineSub}>Go online to see available jobs near you</Text>
          <TouchableOpacity style={styles.goOnlineBtn} onPress={async () => {
            setOnline(true);
            try { await updateAvailability(token, true); }
            catch { setOnline(false); }
          }}>
            <IconWifi size={18} color="#FFF" />
            <Text style={styles.goOnlineText}>Go Online</Text>
          </TouchableOpacity>
        </View>
      ) : loading ? (
        <View style={styles.loadingState}>
          <ActivityIndicator size="large" color={theme.colors.sky} />
          <Text style={styles.loadingText}>Finding jobs near you...</Text>
        </View>
      ) : (
        <FlatList
          data={jobs}
          keyExtractor={item => String(item.id)}
          renderItem={renderJob}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.sky} />
          }
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <View style={styles.emptyIcon}>
                <IconMapPin size={40} color="#CCC" />
              </View>
              <Text style={styles.emptyTitle}>No Jobs Available</Text>
              <Text style={styles.emptyText}>New jobs are posted frequently.{'\n'}Pull down to refresh.</Text>
              <TouchableOpacity style={styles.refreshBtn} onPress={onRefresh}>
                <Text style={styles.refreshBtnText}>Refresh</Text>
              </TouchableOpacity>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },

  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 12 },
  headerTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  greeting: { fontSize: 14, color: '#999', fontWeight: '600' },
  driverName: { fontSize: 24, fontWeight: '900', color: theme.colors.dark, marginTop: 2 },

  onlineToggle: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: '#E8F5E9', paddingHorizontal: 14, paddingVertical: 9, borderRadius: 24,
  },
  offlineToggle: { backgroundColor: '#F5F5F5' },
  onlineText: { fontSize: 13, fontWeight: '800', color: '#4CAF50' },
  offlineText: { color: '#999' },

  summaryBar: {
    flexDirection: 'row', backgroundColor: '#FFF', borderRadius: 16,
    padding: 14, marginTop: 14, borderWidth: 1, borderColor: '#F0F0F0',
    ...theme.shadows.xs,
  },
  summaryItem: { flex: 1, alignItems: 'center', gap: 4 },
  summaryNum: { fontSize: 18, fontWeight: '900', color: theme.colors.dark },
  summaryLabel: { fontSize: 10, color: '#999', fontWeight: '600' },
  summaryDivider: { width: 1, backgroundColor: '#F0F0F0' },

  listContent: { paddingBottom: 120, paddingHorizontal: 20, paddingTop: 4 },

  jobCard: {
    backgroundColor: '#FFF', borderRadius: 20, padding: 18, marginBottom: 14,
    borderWidth: 1, borderColor: '#F0F0F0', ...theme.shadows.sm,
  },
  jobCardUrgent: { borderColor: '#FDE68A', borderWidth: 2 },

  urgentBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    alignSelf: 'flex-start', backgroundColor: '#F59E0B',
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8, marginBottom: 12,
  },
  urgentText: { fontSize: 10, fontWeight: '900', color: '#FFF', letterSpacing: 0.5 },

  routeSection: { flexDirection: 'row', marginBottom: 14 },
  routeIcons: { alignItems: 'center', marginRight: 12, paddingTop: 3 },
  routeDot: { width: 10, height: 10, borderRadius: 5 },
  routeLine: { width: 2, height: 32, backgroundColor: '#E8E8E8', marginVertical: 4 },
  routeInfo: { flex: 1 },
  locationText: { fontSize: 14, fontWeight: '700', color: theme.colors.dark },
  locationSub: { fontSize: 11, color: '#BBB', fontWeight: '500', marginTop: 1 },
  priceBlock: { alignItems: 'flex-end', justifyContent: 'center', minWidth: 64 },
  priceCurrency: { fontSize: 9, fontWeight: '700', color: '#BBB', letterSpacing: 1 },
  priceAmount: { fontSize: 22, fontWeight: '900', color: theme.colors.sky },
  priceRate: { fontSize: 10, fontWeight: '600', color: '#BBB', marginTop: 2 },

  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 14 },
  metaChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#F5F5F5', paddingHorizontal: 9, paddingVertical: 5, borderRadius: 8,
  },
  metaText: { fontSize: 11, fontWeight: '700', color: '#666' },

  cardFooter: { flexDirection: 'row', gap: 10, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#F5F5F5' },
  detailsBtn: {
    flex: 1, paddingVertical: 11, borderRadius: 12,
    borderWidth: 1.5, borderColor: '#E0E0E0', alignItems: 'center',
  },
  detailsBtnText: { fontSize: 13, fontWeight: '700', color: '#666' },
  acceptBtn: {
    flex: 2, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 4, backgroundColor: theme.colors.sky, paddingVertical: 11, borderRadius: 12,
    ...theme.shadows.sm,
  },
  acceptBtnLoading: { opacity: 0.7 },
  acceptText: { color: '#FFF', fontSize: 14, fontWeight: '800' },

  loadingState: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#999', marginTop: 12, fontWeight: '600', fontSize: 14 },

  offlineState: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingBottom: 80, paddingHorizontal: 40 },
  offlineIcon: {
    width: 88, height: 88, borderRadius: 44, backgroundColor: '#F5F5F5',
    justifyContent: 'center', alignItems: 'center', marginBottom: 20,
  },
  offlineTitle: { fontSize: 20, fontWeight: '800', color: theme.colors.dark, marginBottom: 8 },
  offlineSub: { fontSize: 14, color: '#999', textAlign: 'center', lineHeight: 22 },
  goOnlineBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: '#4CAF50', paddingHorizontal: 32, paddingVertical: 14,
    borderRadius: 16, marginTop: 24, ...theme.shadows.sm,
  },
  goOnlineText: { color: '#FFF', fontSize: 15, fontWeight: '800' },

  emptyState: { alignItems: 'center', paddingTop: 60 },
  emptyIcon: {
    width: 88, height: 88, borderRadius: 44, backgroundColor: '#F5F5F5',
    justifyContent: 'center', alignItems: 'center', marginBottom: 16,
  },
  emptyTitle: { fontSize: 18, fontWeight: '800', color: '#999' },
  emptyText: { fontSize: 13, color: '#CCC', marginTop: 8, textAlign: 'center', lineHeight: 20 },
  refreshBtn: {
    marginTop: 20, paddingHorizontal: 28, paddingVertical: 12,
    borderRadius: 12, borderWidth: 1.5, borderColor: theme.colors.sky,
  },
  refreshBtnText: { fontSize: 13, fontWeight: '700', color: theme.colors.sky },
});
