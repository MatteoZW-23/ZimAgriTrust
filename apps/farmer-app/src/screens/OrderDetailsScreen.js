import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { theme } from '../styles';

export default function OrderDetailsScreen({ navigation, route }) {
  const { role, orderId, order } = route.params || {};

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.backBtn}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Order #{orderId}</Text>
        <View style={{ width: 60 }} />
      </View>

      {/* Role Indicator Banner */}
      <View style={[styles.roleBanner, { backgroundColor: role === 'farmer' ? '#E8F5E9' : '#E1F5FE' }]}>
         <Text style={[styles.roleTextBanner, { color: role === 'farmer' ? '#2E7D32' : '#0288D1' }]}>
            Viewing as: {role.toUpperCase()}
         </Text>
      </View>

      {/* Status Stepper */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ORDER STATUS</Text>
        <View style={styles.stepperBox}>
            <View style={styles.stepperRow}>
                <View style={[styles.stepCircle, styles.stepActive]}>
                    <Text style={styles.stepText}>✅</Text>
                </View>
                <View style={styles.stepLineActive} />
                <View style={[styles.stepCircle, styles.stepOngoing]}>
                    <Text style={styles.stepText}>🟡</Text>
                </View>
                <View style={styles.stepLine} />
                <View style={styles.stepCircle}>
                    <Text style={styles.stepText}>○</Text>
                </View>
                <View style={styles.stepLine} />
                <View style={styles.stepCircle}>
                    <Text style={styles.stepText}>○</Text>
                </View>
            </View>
            <View style={styles.stepLabels}>
                <Text style={styles.stepLabel}>Paid</Text>
                <Text style={[styles.stepLabel, { left: '18%' }]}>Pending Delivery</Text>
                <Text style={[styles.stepLabel, { left: '48%' }]}>Delivered</Text>
                <Text style={[styles.stepLabel, { left: '78%' }]}>Completed</Text>
            </View>
            <View style={styles.escrowBanner}>
                <Text style={styles.escrowText}>🛡️ Funds in Escrow: <Text style={{fontWeight: '800'}}>{order?.escrow_amount ? `$${order.escrow_amount}` : '--'}</Text></Text>
                <Text style={styles.deliveryDate}>{order?.expected_delivery ? `Expected: ${order.expected_delivery}` : ''}</Text>
            </View>
        </View>
      </View>

      {/* Product Details */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>PRODUCT DETAILS</Text>
        <View style={styles.card}>
            <Text style={styles.cardRow}><Text style={styles.cardLabel}>Product:</Text> {order?.product_type || '--'}</Text>
            <Text style={styles.cardRow}><Text style={styles.cardLabel}>Quantity:</Text> {order?.quantity ? `${order.quantity} ${order.unit || ''}` : '--'}</Text>
            <Text style={styles.cardRow}><Text style={styles.cardLabel}>Price:</Text> {order?.price_per_unit ? `$${order.price_per_unit}/unit` : '--'}</Text>
            <Text style={styles.cardRow}><Text style={styles.cardLabel}>{role === 'buyer' ? 'Seller' : 'Buyer'}:</Text> {role === 'buyer' ? (order?.seller_name || '--') : (order?.buyer_name || '--')}</Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actionGrid}>
        {role === 'buyer' ? (
            <>
                <TouchableOpacity style={styles.secondaryBtn}><Text style={styles.secondaryBtnText}>Message Seller</Text></TouchableOpacity>
                <TouchableOpacity style={[styles.secondaryBtn, { backgroundColor: '#FFF0F0', borderColor: '#FFBABA' }]}><Text style={[styles.secondaryBtnText, { color: theme.colors.red }]}>Raise Dispute</Text></TouchableOpacity>
                <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate('ConfirmDelivery', { orderId })}>
                    <Text style={styles.primaryBtnText}>Confirm Delivery</Text>
                </TouchableOpacity>
            </>
        ) : (
            <>
                <TouchableOpacity style={styles.secondaryBtn}><Text style={styles.secondaryBtnText}>Message Buyer</Text></TouchableOpacity>
                <TouchableOpacity style={[styles.secondaryBtn, { backgroundColor: '#FFF0F0', borderColor: '#FFBABA' }]}><Text style={[styles.secondaryBtnText, { color: theme.colors.red }]}>Raise Dispute</Text></TouchableOpacity>
                <TouchableOpacity style={[styles.primaryBtn, { backgroundColor: theme.colors.gold }]}>
                    <Text style={styles.primaryBtnText}>Scan Delivery QR</Text>
                </TouchableOpacity>
            </>
        )}
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { padding: 24, paddingTop: 60, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backBtn: { fontSize: 16, fontWeight: '700', color: theme.colors.sky },
  headerTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.black },
  roleBanner: { paddingVertical: 6, alignItems: 'center' },
  roleTextBanner: { fontSize: 11, fontWeight: '900' },
  section: { marginTop: 24, paddingHorizontal: 24 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#999', letterSpacing: 1.2, marginBottom: 12 },
  stepperBox: { padding: 24, backgroundColor: '#F9F9F9', borderRadius: 16 },
  stepperRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  stepCircle: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#EEE', justifyContent: 'center', alignItems: 'center' },
  stepActive: { backgroundColor: theme.colors.green },
  stepOngoing: { backgroundColor: theme.colors.gold },
  stepLine: { flex: 1, height: 2, backgroundColor: '#EEE', marginHorizontal: 4 },
  stepLineActive: { flex: 1, height: 2, backgroundColor: theme.colors.green, marginHorizontal: 4 },
  stepText: { fontSize: 14 },
  stepLabels: { flexDirection: 'row', marginTop: 12, position: 'relative', height: 40 },
  stepLabel: { position: 'absolute', fontSize: 10, fontWeight: '700', color: '#666', textAlign: 'center', width: 60 },
  escrowBanner: { marginTop: 16, backgroundColor: '#FFF', borderRadius: 12, padding: 16, borderLeftWidth: 4, borderLeftColor: theme.colors.gold },
  escrowText: { fontSize: 14, color: theme.colors.gold },
  deliveryDate: { fontSize: 12, color: '#999', marginTop: 4 },
  card: { padding: 20, backgroundColor: '#FFF', borderRadius: 16, borderWeight: 1, borderColor: '#EEE', borderWidth: 1 },
  cardRow: { fontSize: 14, color: theme.colors.black, marginBottom: 8, fontWeight: '600' },
  cardLabel: { color: '#999', fontWeight: '800', width: 100 },
  actionGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, padding: 24, marginTop: 12 },
  secondaryBtn: { width: '47%', paddingVertical: 14, borderRadius: 12, borderWidth: 1, borderColor: '#DDD', alignItems: 'center' },
  secondaryBtnText: { fontSize: 13, fontWeight: '700', color: '#666' },
  primaryBtn: { width: '100%', paddingVertical: 18, borderRadius: 12, backgroundColor: theme.colors.green, alignItems: 'center', marginTop: 12 },
  primaryBtnText: { fontSize: 16, fontWeight: '800', color: '#FFF' }
});

