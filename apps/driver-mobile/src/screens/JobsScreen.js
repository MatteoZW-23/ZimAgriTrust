import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl, SafeAreaView, ActivityIndicator, Alert } from 'react-native';
import { MapPin, Navigation, Package, Clock, DollarSign, Zap, ChevronRight } from 'lucide-react-native';
import { theme } from '../styles';
import { getAvailableJobs, acceptJob } from '../api';

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function estimateTime(km) {
  if (!km) return '—';
  const hrs = Math.round(km / 60);
  return hrs < 1 ? `${Math.round(km)} min` : `~${hrs}h ${Math.round((km / 60 - hrs) * 60)}m`;
}

export default function JobsScreen({ route, navigation }) {
  const { token, profile = {} } = route.params || {};
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [online, setOnline] = useState(true);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await getAvailableJobs(token);
      setJobs(Array.isArray(data) ? data : data?.jobs || []);
    } catch (err) {
      console.warn('Failed to fetch jobs:', err);
      setJobs([
        { id: '1', pickup_location: 'Harare - Mbare Musika', delivery_location: 'Bulawayo - Renkini', distance_km: 440, weight_kg: 2000, crop_type: 'Maize', payment_amount: 150, currency: 'USD', status: 'available', urgent: true },
        { id: '2', pickup_location: 'Mutare - Sakubva Market', delivery_location: 'Harare - Mbare Musika', distance_km: 260, weight_kg: 1500, crop_type: 'Tobacco', payment_amount: 90, currency: 'USD', status: 'available' },
        { id: '3', pickup_location: 'Gweru - Kudzanayi', delivery_location: 'Masvingo - Mucheke', distance_km: 180, weight_kg: 800, crop_type: 'Groundnuts', payment_amount: 65, currency: 'USD', status: 'available' },
        { id: '4', pickup_location: 'Chinhoyi - Gadzema', delivery_location: 'Kariba Town', distance_km: 210, weight_kg: 600, crop_type: 'Soya Beans', payment_amount: 75, currency: 'USD', status: 'available' },
      ]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const onRefresh = useCallback(() => { setRefreshing(true); fetchJobs(); }, [fetchJobs]);

  const handleAccept = async (jobId) => {
    Alert.alert('Accept Job?', 'You will be assigned this delivery.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Accept', onPress: async () => {
        try {
          await acceptJob(token, jobId);
          Alert.alert('Accepted!', 'Check your Deliveries tab for details.');
          fetchJobs();
        } catch (err) {
          Alert.alert('Error', err.message || 'Failed to accept job');
        }
      }},
    ]);
  };

  const firstName = (profile.full_name || 'Driver').split(' ')[0];
  const totalEarnable = jobs.reduce((s, j) => s + (j.payment_amount || 0), 0);

  const renderJob = ({ item, index }) => {
    const isUrgent = item.urgent || item.payment_amount >= 100;
    const perKm = item.distance_km ? (item.payment_amount / item.distance_km).toFixed(2) : '—';

    return (
      <TouchableOpacity
        style={[styles.jobCard, isUrgent && styles.jobCardUrgent]}
        onPress={() => navigation.navigate('JobDetails', { job: item, token })}
        activeOpacity={0.7}
      >
        {isUrgent && (
          <View style={styles.urgentBadge}>
            <Zap size={10} color="#FFF" />
            <Text style={styles.urgentText}>HIGH VALUE</Text>
          </View>
        )}

        <View style={styles.routeSection}>
          <View style={styles.routeIcons}>
            <View style={[styles.routeDot, { backgroundColor: theme.colors.sky }]} />
            <View style={styles.routeLine} />
            <View style={[styles.routeDot, { backgroundColor: '#4CAF50' }]} />
          </View>
          <View style={styles.routeInfo}>
            <Text style={styles.locationText} numberOfLines={1}>{item.pickup_location}</Text>
            <Text style={styles.locationSub}>Pickup point</Text>
            <View style={{ height: 10 }} />
            <Text style={styles.locationText} numberOfLines={1}>{item.delivery_location}</Text>
            <Text style={styles.locationSub}>Drop-off point</Text>
          </View>
          <View style={styles.priceBlock}>
            <Text style={styles.priceCurrency}>USD</Text>
            <Text style={styles.priceAmount}>${item.payment_amount}</Text>
          </View>
        </View>

        <View style={styles.metaRow}>
          <View style={styles.metaChip}>
            <Navigation size={12} color="#666" />
            <Text style={styles.metaText}>{item.distance_km} km</Text>
          </View>
          <View style={styles.metaChip}>
            <Clock size={12} color="#666" />
            <Text style={styles.metaText}>{estimateTime(item.distance_km)}</Text>
          </View>
          <View style={styles.metaChip}>
            <Package size={12} color="#666" />
            <Text style={styles.metaText}>{item.weight_kg} kg</Text>
          </View>
          <View style={[styles.metaChip, { backgroundColor: '#FFF8E1' }]}>
            <Text style={styles.metaText}>🌾 {item.crop_type}</Text>
          </View>
        </View>

        <View style={styles.cardFooter}>
          <Text style={styles.rateText}>${perKm}/km</Text>
          <TouchableOpacity style={styles.acceptBtn} onPress={() => handleAccept(item.id)}>
            <Text style={styles.acceptText}>Accept</Text>
            <ChevronRight size={16} color="#FFF" />
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Greeting Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.greeting}>{getGreeting()},</Text>
            <Text style={styles.driverName}>{firstName} 👋</Text>
          </View>
          <TouchableOpacity style={[styles.onlineToggle, !online && styles.offlineToggle]} onPress={() => setOnline(o => !o)}>
            <View style={[styles.onlineDot, !online && styles.offlineDot]} />
            <Text style={[styles.onlineText, !online && styles.offlineText]}>{online ? 'Online' : 'Offline'}</Text>
          </TouchableOpacity>
        </View>
        {online && jobs.length > 0 && (
          <View style={styles.summaryBar}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryNum}>{jobs.length}</Text>
              <Text style={styles.summaryLabel}>Jobs</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <Text style={styles.summaryNum}>${totalEarnable}</Text>
              <Text style={styles.summaryLabel}>Earnable</Text>
            </View>
          </View>
        )}
      </View>

      {!online ? (
        <View style={styles.offlineState}>
          <Text style={{ fontSize: 48 }}>😴</Text>
          <Text style={styles.offlineTitle}>You're offline</Text>
          <Text style={styles.offlineSub}>Go online to see available jobs</Text>
          <TouchableOpacity style={styles.goOnlineBtn} onPress={() => setOnline(true)}>
            <Text style={styles.goOnlineText}>Go Online</Text>
          </TouchableOpacity>
        </View>
      ) : loading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color={theme.colors.sky} />
          <Text style={{ color: '#999', marginTop: 12, fontWeight: '600' }}>Finding jobs near you...</Text>
        </View>
      ) : (
        <FlatList
          data={jobs}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderJob}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.sky} />}
          contentContainerStyle={{ paddingBottom: 120, paddingHorizontal: 20 }}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <MapPin size={48} color="#DDD" />
              <Text style={styles.emptyTitle}>No Jobs Right Now</Text>
              <Text style={styles.emptyText}>New jobs are posted frequently.{'\n'}Pull down to refresh.</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 },
  headerTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  greeting: { fontSize: 15, color: '#999', fontWeight: '600' },
  driverName: { fontSize: 26, fontWeight: '900', color: theme.colors.dark, marginTop: 2 },
  onlineToggle: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#E8F5E9', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 24 },
  offlineToggle: { backgroundColor: '#F5F5F5' },
  onlineDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#4CAF50' },
  offlineDot: { backgroundColor: '#999' },
  onlineText: { fontSize: 13, fontWeight: '800', color: '#4CAF50' },
  offlineText: { color: '#999' },
  summaryBar: { flexDirection: 'row', backgroundColor: '#FFF', borderRadius: 16, padding: 16, marginTop: 16, ...theme.shadows.xs, borderWidth: 1, borderColor: '#F0F0F0' },
  summaryItem: { flex: 1, alignItems: 'center' },
  summaryNum: { fontSize: 20, fontWeight: '900', color: theme.colors.dark },
  summaryLabel: { fontSize: 11, color: '#999', fontWeight: '600', marginTop: 2 },
  summaryDivider: { width: 1, backgroundColor: '#F0F0F0' },

  jobCard: { backgroundColor: '#FFF', borderRadius: 20, padding: 20, marginBottom: 14, ...theme.shadows.sm, borderWidth: 1, borderColor: '#F0F0F0' },
  jobCardUrgent: { borderColor: '#FFE082', borderWidth: 2 },
  urgentBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'flex-start', backgroundColor: '#FF9800', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8, marginBottom: 12 },
  urgentText: { fontSize: 10, fontWeight: '900', color: '#FFF', letterSpacing: 1 },
  routeSection: { flexDirection: 'row', marginBottom: 16 },
  routeIcons: { alignItems: 'center', marginRight: 12, paddingTop: 4 },
  routeDot: { width: 10, height: 10, borderRadius: 5 },
  routeLine: { width: 2, height: 36, backgroundColor: '#E8E8E8', marginVertical: 4 },
  routeInfo: { flex: 1 },
  locationText: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  locationSub: { fontSize: 11, color: '#BBB', fontWeight: '500', marginTop: 1 },
  priceBlock: { alignItems: 'flex-end', justifyContent: 'center' },
  priceCurrency: { fontSize: 10, fontWeight: '700', color: '#999', letterSpacing: 1 },
  priceAmount: { fontSize: 24, fontWeight: '900', color: theme.colors.sky },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  metaChip: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#F5F5F5', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 10 },
  metaText: { fontSize: 12, fontWeight: '700', color: '#666' },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: 14, borderTopWidth: 1, borderTopColor: '#F5F5F5' },
  rateText: { fontSize: 13, fontWeight: '700', color: '#999' },
  acceptBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: theme.colors.sky, paddingHorizontal: 20, paddingVertical: 12, borderRadius: 14 },
  acceptText: { color: '#FFF', fontSize: 14, fontWeight: '800' },

  offlineState: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingBottom: 80 },
  offlineTitle: { fontSize: 22, fontWeight: '800', color: theme.colors.dark, marginTop: 16 },
  offlineSub: { fontSize: 14, color: '#999', marginTop: 6 },
  goOnlineBtn: { backgroundColor: '#4CAF50', paddingHorizontal: 40, paddingVertical: 14, borderRadius: 16, marginTop: 24 },
  goOnlineText: { color: '#FFF', fontSize: 16, fontWeight: '800' },

  emptyState: { alignItems: 'center', paddingTop: 80 },
  emptyTitle: { fontSize: 20, fontWeight: '800', color: '#999', marginTop: 16 },
  emptyText: { fontSize: 14, color: '#CCC', marginTop: 8, textAlign: 'center', lineHeight: 22 },
});
