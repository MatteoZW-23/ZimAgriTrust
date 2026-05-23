import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, Alert, ActivityIndicator,
} from 'react-native';
import {
  ArrowLeft as IconArrowLeft, MapPin as IconMapPin,
  Navigation as IconNavigation, Package as IconPackage,
  Truck as IconTruck, Clock as IconClock,
  DollarSign as IconDollarSign, Wheat as IconWheat,
  CheckCircle as IconCheckCircle, Phone as IconPhone,
  User as IconUser, Fuel as IconFuel, TrendingUp as IconTrendingUp,
} from 'lucide-react-native';
import { theme } from '../styles';
import { acceptJob } from '../api';

export default function JobDetailsScreen({ route, navigation }) {
  const { job = {}, token } = route.params || {};
  const [accepting, setAccepting] = useState(false);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await acceptJob(token, job.id);
      Alert.alert(
        'Job Accepted',
        'Head to the Deliveries tab to start this delivery.',
        [{ text: 'OK', onPress: () => navigation.goBack() }],
      );
    } catch (err) {
      Alert.alert('Failed to Accept', err.message || 'Please try again.');
    } finally {
      setAccepting(false);
    }
  };

  const perKm = job.distance_km
    ? (job.payment_amount / job.distance_km).toFixed(2)
    : null;

  return (
    <SafeAreaView style={styles.container}>
      {/* Top bar */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <IconArrowLeft size={22} color={theme.colors.dark} />
        </TouchableOpacity>
        <Text style={styles.topTitle}>Job Details</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>

        {/* Payment hero */}
        <View style={styles.paymentCard}>
          <IconDollarSign size={20} color="rgba(255,255,255,0.7)" />
          <Text style={styles.paymentLabel}>Delivery Payment</Text>
          <Text style={styles.paymentAmount}>${job.payment_amount || 0}</Text>
          <Text style={styles.paymentCurrency}>{job.currency || 'USD'}</Text>
          {perKm && (
            <View style={styles.rateChip}>
              <Text style={styles.rateText}>${perKm} per km</Text>
            </View>
          )}
        </View>

        {/* Route card */}
        <View style={styles.routeCard}>
          <Text style={styles.cardLabel}>Route</Text>
          <View style={styles.routeRow}>
            <View style={styles.routeIcons}>
              <View style={[styles.routeDot, { backgroundColor: theme.colors.sky }]} />
              <View style={styles.routeLine} />
              <View style={[styles.routeDot, { backgroundColor: '#4CAF50' }]} />
            </View>
            <View style={styles.routeDetails}>
              <View style={styles.routeStop}>
                <Text style={styles.routeStopLabel}>PICKUP</Text>
                <Text style={styles.routeLocation}>{job.pickup_location || 'TBD'}</Text>
              </View>
              <View style={[styles.routeStop, { marginTop: 18 }]}>
                <Text style={styles.routeStopLabel}>DROP-OFF</Text>
                <Text style={styles.routeLocation}>{job.delivery_location || 'TBD'}</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Pickup Section */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <IconMapPin size={18} color={theme.colors.sky} />
            <Text style={styles.sectionTitle}>Pickup Details</Text>
          </View>
          <View style={styles.contactRow}>
            <View style={styles.contactItem}>
              <IconUser size={14} color="#666" />
              <Text style={styles.contactText}>{job.pickup_contact_name || 'Contact on arrival'}</Text>
            </View>
            <TouchableOpacity style={styles.contactItem}>
              <IconPhone size={14} color={theme.colors.sky} />
              <Text style={[styles.contactText, styles.contactPhone]}>{job.pickup_phone || 'Call on arrival'}</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.addressBox}>
            <Text style={styles.addressLabel}>Address</Text>
            <Text style={styles.addressText}>{job.pickup_address || job.pickup_location || 'TBD'}</Text>
          </View>
          {job.pickup_instructions && (
            <View style={styles.instructionsBox}>
              <Text style={styles.instructionsLabel}>Special Instructions</Text>
              <Text style={styles.instructionsText}>{job.pickup_instructions}</Text>
            </View>
          )}
        </View>

        {/* Delivery Section */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <IconTruck size={18} color="#4CAF50" />
            <Text style={styles.sectionTitle}>Delivery Details</Text>
          </View>
          <View style={styles.contactRow}>
            <View style={styles.contactItem}>
              <IconUser size={14} color="#666" />
              <Text style={styles.contactText}>{job.delivery_contact_name || 'Contact on arrival'}</Text>
            </View>
            <TouchableOpacity style={styles.contactItem}>
              <IconPhone size={14} color={theme.colors.sky} />
              <Text style={[styles.contactText, styles.contactPhone]}>{job.delivery_phone || 'Call on arrival'}</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.addressBox}>
            <Text style={styles.addressLabel}>Address</Text>
            <Text style={styles.addressText}>{job.delivery_address || job.delivery_location || 'TBD'}</Text>
          </View>
          {job.delivery_instructions && (
            <View style={styles.instructionsBox}>
              <Text style={styles.instructionsLabel}>Special Instructions</Text>
              <Text style={styles.instructionsText}>{job.delivery_instructions}</Text>
            </View>
          )}
        </View>

        {/* Earnings Breakdown */}
        <View style={styles.earningsCard}>
          <View style={styles.sectionHeader}>
            <IconTrendingUp size={18} color="#16a34a" />
            <Text style={styles.sectionTitle}>Earnings Breakdown</Text>
          </View>
          <View style={styles.earningsRow}>
            <Text style={styles.earningsLabel}>Base Payment</Text>
            <Text style={styles.earningsValue}>${job.payment_amount || 0}</Text>
          </View>
          <View style={styles.earningsRow}>
            <Text style={styles.earningsLabel}>Distance Rate</Text>
            <Text style={styles.earningsValue}>${perKm || '0.00'}/km</Text>
          </View>
          <View style={styles.earningsRow}>
            <Text style={styles.earningsLabel}>Est. Fuel Cost</Text>
            <Text style={[styles.earningsValue, styles.earningsDeduction]}>-${((job.distance_km || 0) * 0.15).toFixed(2)}</Text>
          </View>
          <View style={[styles.earningsRow, styles.earningsTotal]}>
            <Text style={styles.earningsTotalLabel}>Net Earnings</Text>
            <Text style={styles.earningsTotalValue}>${((job.payment_amount || 0) - ((job.distance_km || 0) * 0.15)).toFixed(2)}</Text>
          </View>
        </View>

        {/* Details grid */}
        <View style={styles.detailsGrid}>
          <DetailCard
            icon={<IconNavigation size={18} color={theme.colors.sky} />}
            bg="#E1F5FE"
            label="Distance"
            value={job.distance_km ? `${job.distance_km} km` : '—'}
          />
          <DetailCard
            icon={<IconPackage size={18} color="#F59E0B" />}
            bg="#FFFBEB"
            label="Weight"
            value={job.weight_kg ? `${job.weight_kg} kg` : '—'}
          />
          <DetailCard
            icon={<IconWheat size={18} color="#16a34a" />}
            bg="#F0FDF4"
            label="Cargo"
            value={job.crop_type || 'General'}
          />
          <DetailCard
            icon={<IconClock size={18} color="#9C27B0" />}
            bg="#F5F3FF"
            label="Est. Time"
            value={job.distance_km ? estimateTime(job.distance_km) : '—'}
          />
        </View>

        {/* Info note */}
        <View style={styles.infoBox}>
          <IconCheckCircle size={16} color={theme.colors.sky} />
          <Text style={styles.infoText}>
            Payment is released after successful delivery confirmation.
          </Text>
        </View>

        {/* Action Buttons */}
        <View style={{ marginHorizontal: 20, marginTop: 24, gap: 12 }}>
          <TouchableOpacity
            style={[styles.acceptBtn, accepting && styles.acceptBtnLoading]}
            onPress={handleAccept}
            disabled={accepting}
            activeOpacity={0.85}
          >
            {accepting ? (
              <ActivityIndicator color="#FFF" size="small" />
            ) : (
              <>
                <IconCheckCircle size={20} color="#FFF" />
                <Text style={styles.acceptText}>Accept This Job</Text>
              </>
            )}
          </TouchableOpacity>

          <View style={{ flexDirection: 'row', gap: 12 }}>
            <TouchableOpacity 
              style={[styles.actionBtn, styles.declineBtn]}
              onPress={() => Alert.alert('Job Declined', 'The job has been removed from your list.')}
            >
              <Text style={styles.declineText}>Decline</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.actionBtn, styles.negotiateBtn]}
              onPress={() => Alert.alert('Negotiation', 'Send a counter-offer for this job?', [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Send +10%', onPress: () => Alert.alert('Sent', 'Counter-offer sent to customer.') }
              ])}
            >
              <Text style={styles.negotiateText}>Negotiate</Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity style={styles.backLink} onPress={() => navigation.goBack()}>
          <IconArrowLeft size={14} color="#999" />
          <Text style={styles.backLinkText}>Back to Jobs</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function DetailCard({ icon, bg, label, value }) {
  return (
    <View style={styles.detailCard}>
      <View style={[styles.detailIconWrap, { backgroundColor: bg }]}>{icon}</View>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

function estimateTime(km) {
  const hrs = km / 60;
  if (hrs < 1) return `${Math.round(hrs * 60)} min`;
  const h = Math.floor(hrs);
  const m = Math.round((hrs - h) * 60);
  return m > 0 ? `~${h}h ${m}m` : `~${h}h`;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  topBar: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 14,
  },
  backBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: '#F0F0F0', justifyContent: 'center', alignItems: 'center',
  },
  topTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.dark },
  scrollContent: { paddingBottom: 40 },

  paymentCard: {
    marginHorizontal: 20, backgroundColor: theme.colors.sky,
    borderRadius: 24, padding: 28, alignItems: 'center', ...theme.shadows.lg,
  },
  paymentLabel: { color: 'rgba(255,255,255,0.75)', fontSize: 13, fontWeight: '600', marginTop: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  paymentAmount: { color: '#FFF', fontSize: 52, fontWeight: '900', marginTop: 4, letterSpacing: -1 },
  paymentCurrency: { color: 'rgba(255,255,255,0.7)', fontSize: 14, fontWeight: '600', marginTop: 2 },
  rateChip: {
    marginTop: 12, backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20,
  },
  rateText: { color: '#FFF', fontSize: 12, fontWeight: '700' },

  routeCard: {
    marginHorizontal: 20, marginTop: 20, backgroundColor: '#FFF',
    borderRadius: 20, padding: 20, ...theme.shadows.xs, borderWidth: 1, borderColor: '#F0F0F0',
  },
  cardLabel: { fontSize: 11, fontWeight: '800', color: '#BBB', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 16 },
  routeRow: { flexDirection: 'row' },
  routeIcons: { alignItems: 'center', marginRight: 16, paddingTop: 4 },
  routeDot: { width: 12, height: 12, borderRadius: 6 },
  routeLine: { width: 2, height: 28, backgroundColor: '#E0E0E0', marginVertical: 4 },
  routeDetails: { flex: 1 },
  routeStop: {},
  routeStopLabel: { fontSize: 10, fontWeight: '700', color: '#BBB', letterSpacing: 1 },
  routeLocation: { fontSize: 16, fontWeight: '700', color: theme.colors.dark, marginTop: 3 },

  sectionCard: {
    marginHorizontal: 20, marginTop: 16, backgroundColor: '#FFF',
    borderRadius: 20, padding: 20, ...theme.shadows.xs, borderWidth: 1, borderColor: '#F0F0F0',
  },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 },
  sectionTitle: { fontSize: 15, fontWeight: '800', color: theme.colors.dark },
  contactRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  contactItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  contactText: { fontSize: 13, fontWeight: '600', color: '#666' },
  contactPhone: { color: theme.colors.sky },
  addressBox: { backgroundColor: '#F8F9FA', borderRadius: 12, padding: 14, marginBottom: 12 },
  addressLabel: { fontSize: 10, fontWeight: '700', color: '#999', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 },
  addressText: { fontSize: 14, fontWeight: '600', color: theme.colors.dark, lineHeight: 20 },
  instructionsBox: { backgroundColor: '#FFF7ED', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#FFEDD5' },
  instructionsLabel: { fontSize: 10, fontWeight: '700', color: '#C2410C', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 },
  instructionsText: { fontSize: 13, fontWeight: '600', color: '#9A3412', lineHeight: 18 },

  earningsCard: {
    marginHorizontal: 20, marginTop: 16, backgroundColor: '#F0FDF4',
    borderRadius: 20, padding: 20, borderWidth: 1, borderColor: '#BBF7D0',
  },
  earningsRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8 },
  earningsLabel: { fontSize: 13, fontWeight: '600', color: '#374151' },
  earningsValue: { fontSize: 15, fontWeight: '800', color: '#374151' },
  earningsDeduction: { color: '#DC2626' },
  earningsTotal: { marginTop: 8, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#BBF7D0' },
  earningsTotalLabel: { fontSize: 14, fontWeight: '800', color: '#16a34a' },
  earningsTotalValue: { fontSize: 20, fontWeight: '900', color: '#16a34a' },

  detailsGrid: {
    flexDirection: 'row', flexWrap: 'wrap',
    marginHorizontal: 16, marginTop: 16, gap: 10,
  },
  detailCard: {
    width: '47%', backgroundColor: '#FFF', borderRadius: 16, padding: 16,
    ...theme.shadows.xs, borderWidth: 1, borderColor: '#F0F0F0', flexGrow: 1,
  },
  detailIconWrap: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center', marginBottom: 10 },
  detailLabel: { fontSize: 11, color: '#999', fontWeight: '600' },
  detailValue: { fontSize: 16, fontWeight: '800', color: theme.colors.dark, marginTop: 3 },

  infoBox: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    marginHorizontal: 20, marginTop: 16, backgroundColor: '#E1F5FE',
    borderRadius: 14, padding: 14,
  },
  infoText: { flex: 1, fontSize: 13, color: '#0369a1', fontWeight: '600', lineHeight: 18 },

  acceptBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    marginHorizontal: 20, marginTop: 24, backgroundColor: theme.colors.sky,
    paddingVertical: 18, borderRadius: 16, ...theme.shadows.md,
  },
  acceptBtnLoading: { opacity: 0.7 },
  acceptText: { color: '#FFF', fontSize: 17, fontWeight: '800', letterSpacing: 0.3 },

  actionBtn: { flex: 1, height: 50, borderRadius: 14, justifyContent: 'center', alignItems: 'center', borderWidth: 1.5 },
  declineBtn: { borderColor: '#E5E7EB', backgroundColor: '#F9FAFB' },
  negotiateBtn: { borderColor: theme.colors.sky, backgroundColor: '#FFF' },
  declineText: { fontSize: 14, fontWeight: '700', color: '#6B7280' },
  negotiateText: { fontSize: 14, fontWeight: '700', color: theme.colors.sky },

  backLink: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 6, marginTop: 16, paddingVertical: 12,
  },
  backLinkText: { fontSize: 13, fontWeight: '600', color: '#999' },
});
