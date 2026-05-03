import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView, Alert } from 'react-native';
import { ArrowLeft, MapPin, Navigation, Package, Truck, DollarSign, Clock } from 'lucide-react-native';
import { theme } from '../styles';
import { acceptJob } from '../api';

export default function JobDetailsScreen({ route, navigation }) {
  const { job = {}, token } = route.params || {};
  const [accepting, setAccepting] = useState(false);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await acceptJob(token, job.id);
      Alert.alert('Job Accepted!', 'Check your Deliveries tab to start this delivery.', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (err) {
      Alert.alert('Error', err.message || 'Failed to accept job');
    } finally {
      setAccepting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <ArrowLeft size={22} color={theme.colors.dark} />
        </TouchableOpacity>
        <Text style={styles.topTitle}>Job Details</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
        {/* Payment Hero */}
        <View style={styles.paymentCard}>
          <Text style={styles.paymentLabel}>Delivery Payment</Text>
          <Text style={styles.paymentAmount}>${job.payment_amount || job.price || 0}</Text>
          <Text style={styles.paymentCurrency}>{job.currency || 'USD'}</Text>
        </View>

        {/* Route */}
        <View style={styles.routeCard}>
          <View style={styles.routeRow}>
            <View style={styles.routeIcons}>
              <View style={[styles.routeDot, { backgroundColor: theme.colors.sky }]} />
              <View style={styles.routeLine} />
              <View style={[styles.routeDot, { backgroundColor: '#4CAF50' }]} />
            </View>
            <View style={styles.routeDetails}>
              <View style={styles.routeStop}>
                <Text style={styles.routeLabel}>PICKUP</Text>
                <Text style={styles.routeLocation}>{job.pickup_location || job.pickup || 'TBD'}</Text>
              </View>
              <View style={[styles.routeStop, { marginTop: 20 }]}>
                <Text style={styles.routeLabel}>DELIVERY</Text>
                <Text style={styles.routeLocation}>{job.delivery_location || job.destination || 'TBD'}</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Details Grid */}
        <View style={styles.detailsGrid}>
          <DetailCard icon={<Navigation size={18} color={theme.colors.sky} />} label="Distance" value={`${job.distance_km || job.distance || '—'} km`} />
          <DetailCard icon={<Package size={18} color="#FF9800" />} label="Weight" value={`${job.weight_kg || '—'} kg`} />
          <DetailCard icon={<Truck size={18} color="#4CAF50" />} label="Cargo" value={job.crop_type || 'General'} />
          <DetailCard icon={<Clock size={18} color="#9C27B0" />} label="Status" value={(job.status || 'available').replace('_', ' ')} />
        </View>

        {/* Accept Button */}
        <TouchableOpacity
          style={[styles.acceptBtn, accepting && { opacity: 0.7 }]}
          onPress={handleAccept}
          disabled={accepting}
        >
          <Text style={styles.acceptText}>{accepting ? 'Accepting...' : 'Accept This Job'}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function DetailCard({ icon, label, value }) {
  return (
    <View style={styles.detailCard}>
      {icon}
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F0F0F0', justifyContent: 'center', alignItems: 'center' },
  topTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.dark },
  paymentCard: {
    marginHorizontal: 20,
    backgroundColor: theme.colors.sky,
    borderRadius: 24,
    padding: 28,
    alignItems: 'center',
    ...theme.shadows.lg,
  },
  paymentLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 13, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1 },
  paymentAmount: { color: '#FFF', fontSize: 48, fontWeight: '900', marginTop: 4 },
  paymentCurrency: { color: 'rgba(255,255,255,0.8)', fontSize: 14, fontWeight: '600', marginTop: 4 },
  routeCard: {
    marginHorizontal: 20,
    marginTop: 20,
    backgroundColor: '#FFF',
    borderRadius: 20,
    padding: 24,
    ...theme.shadows.xs,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  routeRow: { flexDirection: 'row' },
  routeIcons: { alignItems: 'center', marginRight: 16, paddingTop: 4 },
  routeDot: { width: 12, height: 12, borderRadius: 6 },
  routeLine: { width: 2, height: 30, backgroundColor: '#E0E0E0', marginVertical: 4 },
  routeDetails: { flex: 1 },
  routeStop: {},
  routeLabel: { fontSize: 11, fontWeight: '700', color: '#999', letterSpacing: 1 },
  routeLocation: { fontSize: 16, fontWeight: '700', color: theme.colors.dark, marginTop: 4 },
  detailsGrid: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: 16, marginTop: 16, gap: 8 },
  detailCard: {
    width: '48%',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    ...theme.shadows.xs,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    flexGrow: 1,
  },
  detailLabel: { fontSize: 11, color: '#999', fontWeight: '600', marginTop: 8 },
  detailValue: { fontSize: 16, fontWeight: '800', color: theme.colors.dark, marginTop: 2, textTransform: 'capitalize' },
  acceptBtn: {
    marginHorizontal: 20,
    marginTop: 28,
    backgroundColor: theme.colors.sky,
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: 'center',
    ...theme.shadows.md,
  },
  acceptText: { color: '#FFF', fontSize: 17, fontWeight: '700', letterSpacing: 0.5 },
});
