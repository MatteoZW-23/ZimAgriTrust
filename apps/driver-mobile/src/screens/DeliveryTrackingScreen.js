import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView, Alert } from 'react-native';
import { ArrowLeft, MapPin, CheckCircle, Truck, Package, Camera, Phone } from 'lucide-react-native';
import { theme } from '../styles';
import { updateDeliveryStatus } from '../api';

const STEPS = [
  { key: 'pending', label: 'Job Accepted', icon: CheckCircle },
  { key: 'picked_up', label: 'Cargo Picked Up', icon: Package },
  { key: 'in_transit', label: 'In Transit', icon: Truck },
  { key: 'delivered', label: 'Delivered', icon: MapPin },
];

export default function DeliveryTrackingScreen({ route, navigation }) {
  const { delivery = {}, token } = route.params || {};
  const [status, setStatus] = useState(delivery.status || 'pending');
  const [updating, setUpdating] = useState(false);

  const currentIdx = STEPS.findIndex(s => s.key === status);

  const handleUpdateStatus = async (newStatus) => {
    setUpdating(true);
    try {
      await updateDeliveryStatus(token, delivery.id, newStatus);
      setStatus(newStatus);
      if (newStatus === 'delivered') {
        Alert.alert('Delivery Complete!', 'Great job! Payment will be processed shortly.');
      }
    } catch (err) {
      Alert.alert('Error', err.message || 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  const nextStep = STEPS[currentIdx + 1];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <ArrowLeft size={22} color={theme.colors.dark} />
        </TouchableOpacity>
        <Text style={styles.topTitle}>Delivery Tracking</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
        {/* Route Card */}
        <View style={styles.routeCard}>
          <View style={styles.routeRow}>
            <View style={[styles.dot, { backgroundColor: theme.colors.sky }]} />
            <Text style={styles.routeText} numberOfLines={1}>{delivery.pickup_location || 'Pickup'}</Text>
          </View>
          <View style={styles.routeDivider} />
          <View style={styles.routeRow}>
            <View style={[styles.dot, { backgroundColor: '#4CAF50' }]} />
            <Text style={styles.routeText} numberOfLines={1}>{delivery.delivery_location || 'Destination'}</Text>
          </View>
          <View style={styles.routeMeta}>
            <Text style={styles.metaText}>🌾 {delivery.crop_type || 'Cargo'}</Text>
            <Text style={styles.metaText}>📦 {delivery.weight_kg || '—'} kg</Text>
            <Text style={[styles.metaText, { fontWeight: '800', color: theme.colors.sky }]}>${delivery.payment_amount || 0}</Text>
          </View>
        </View>

        {/* Status Timeline */}
        <View style={styles.timelineCard}>
          <Text style={styles.sectionTitle}>Delivery Progress</Text>
          {STEPS.map((step, idx) => {
            const StepIcon = step.icon;
            const isComplete = idx <= currentIdx;
            const isCurrent = idx === currentIdx;
            return (
              <View key={step.key} style={styles.timelineRow}>
                <View style={styles.timelineLeft}>
                  <View style={[
                    styles.timelineDot,
                    isComplete ? { backgroundColor: theme.colors.sky } : { backgroundColor: '#E0E0E0' },
                    isCurrent && { borderWidth: 3, borderColor: 'rgba(41,182,246,0.3)' },
                  ]}>
                    <StepIcon size={14} color={isComplete ? '#FFF' : '#999'} />
                  </View>
                  {idx < STEPS.length - 1 && (
                    <View style={[styles.timelineLine, isComplete && { backgroundColor: theme.colors.sky }]} />
                  )}
                </View>
                <View style={styles.timelineContent}>
                  <Text style={[styles.timelineLabel, isComplete && { color: theme.colors.dark }]}>{step.label}</Text>
                  {isCurrent && <Text style={styles.timelineStatus}>Current</Text>}
                </View>
              </View>
            );
          })}
        </View>

        {/* Action Buttons */}
        {nextStep && (
          <TouchableOpacity
            style={[styles.actionBtn, updating && { opacity: 0.6 }]}
            onPress={() => handleUpdateStatus(nextStep.key)}
            disabled={updating}
          >
            <Text style={styles.actionText}>{updating ? 'Updating...' : `Mark as ${nextStep.label}`}</Text>
          </TouchableOpacity>
        )}

        {status === 'delivered' && (
          <View style={styles.completeCard}>
            <CheckCircle size={32} color="#4CAF50" />
            <Text style={styles.completeTitle}>Delivery Complete</Text>
            <Text style={styles.completeText}>Payment is being processed</Text>
          </View>
        )}

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.quickBtn}>
            <Camera size={20} color={theme.colors.sky} />
            <Text style={styles.quickLabel}>Photo Proof</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickBtn}>
            <Phone size={20} color={theme.colors.sky} />
            <Text style={styles.quickLabel}>Call Customer</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F0F0F0', justifyContent: 'center', alignItems: 'center' },
  topTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.dark },
  routeCard: {
    marginHorizontal: 20,
    backgroundColor: '#FFF',
    borderRadius: 20,
    padding: 20,
    ...theme.shadows.xs,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  routeRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  dot: { width: 10, height: 10, borderRadius: 5 },
  routeText: { fontSize: 15, fontWeight: '600', color: theme.colors.dark, flex: 1 },
  routeDivider: { width: 2, height: 16, backgroundColor: '#E0E0E0', marginLeft: 4, marginVertical: 4 },
  routeMeta: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 16, paddingTop: 14, borderTopWidth: 1, borderTopColor: '#F5F5F5' },
  metaText: { fontSize: 13, fontWeight: '600', color: '#666' },
  timelineCard: {
    marginHorizontal: 20,
    marginTop: 20,
    backgroundColor: '#FFF',
    borderRadius: 20,
    padding: 24,
    ...theme.shadows.xs,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  sectionTitle: { fontSize: 14, fontWeight: '800', color: '#999', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 20 },
  timelineRow: { flexDirection: 'row', minHeight: 52 },
  timelineLeft: { alignItems: 'center', width: 36, marginRight: 14 },
  timelineDot: { width: 30, height: 30, borderRadius: 15, justifyContent: 'center', alignItems: 'center' },
  timelineLine: { width: 2, flex: 1, backgroundColor: '#E0E0E0', marginVertical: 4 },
  timelineContent: { flex: 1, paddingBottom: 16 },
  timelineLabel: { fontSize: 15, fontWeight: '600', color: '#BBB' },
  timelineStatus: { fontSize: 11, fontWeight: '700', color: theme.colors.sky, marginTop: 4, textTransform: 'uppercase' },
  actionBtn: {
    marginHorizontal: 20,
    marginTop: 24,
    backgroundColor: theme.colors.sky,
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: 'center',
    ...theme.shadows.md,
  },
  actionText: { color: '#FFF', fontSize: 16, fontWeight: '700', letterSpacing: 0.5 },
  completeCard: { marginHorizontal: 20, marginTop: 24, backgroundColor: '#E8F5E9', borderRadius: 20, padding: 28, alignItems: 'center' },
  completeTitle: { fontSize: 20, fontWeight: '800', color: '#2E7D32', marginTop: 12 },
  completeText: { fontSize: 14, color: '#4CAF50', marginTop: 6, fontWeight: '500' },
  quickActions: { flexDirection: 'row', marginHorizontal: 20, marginTop: 24, gap: 12 },
  quickBtn: {
    flex: 1,
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 18,
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  quickLabel: { fontSize: 13, fontWeight: '700', color: theme.colors.dark },
});
