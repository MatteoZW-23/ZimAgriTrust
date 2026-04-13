import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, TextInput, StyleSheet, Alert } from 'react-native';
import { theme } from '../styles';

export default function MakeOfferScreen({ navigation, route }) {
  const { product = {} } = route.params || {};
  const [qty, setQty] = useState('500');
  const [price, setPrice] = useState('0.42');
  const [delivery, setDelivery] = useState('pickup');

  const calculateTotal = () => {
    const amount = parseFloat(qty) * parseFloat(price);
    const fee = amount * 0.01;
    return { amount, fee, total: amount + fee };
  };

  const { amount, fee, total } = calculateTotal();

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}><Text style={styles.backBtn}>← Back</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>Make Offer</Text>
        <View style={{ width: 60 }} />
      </View>

      {/* Seller Summary */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>SELLER INFORMATION</Text>
        <View style={styles.card}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                <Text style={styles.sellerName}>Tendai M.</Text>
                <Text style={styles.sellerRating}>⭐ 4.9 (47 trades)</Text>
            </View>
            <View style={{ flexDirection: 'row', gap: 10, marginTop: 8 }}>
                <Text style={styles.sellerBadge}>✅ Verified ID</Text>
                <Text style={styles.sellerBadge}>📍 Chegutu</Text>
            </View>
        </View>
      </View>

      {/* Listing Details */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>LISTING DETAILS</Text>
        <View style={styles.card}>
            <Text style={styles.detailRow}>Product: <Text style={styles.detailVal}>Grade A Maize</Text></Text>
            <Text style={styles.detailRow}>Available: <Text style={styles.detailVal}>5,000kg</Text></Text>
            <Text style={styles.detailRow}>Asking Price: <Text style={[styles.detailVal, { color: theme.colors.sky }]}>$0.45/kg</Text></Text>
            <Text style={styles.detailRow}>Min Order: <Text style={styles.detailVal}>100kg</Text></Text>
        </View>
      </View>

      {/* Offer Form */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>YOUR OFFER</Text>
        <View style={styles.formCard}>
            <Text style={styles.inputLabel}>Quantity (kg):</Text>
            <View style={styles.stepperInput}>
                <TouchableOpacity onPress={() => setQty(Math.max(100, parseInt(qty)-10).toString())} style={styles.stepBtn}><Text style={styles.stepBtnText}>-</Text></TouchableOpacity>
                <TextInput style={styles.input} value={qty} onChangeText={setQty} keyboardType="numeric" />
                <TouchableOpacity onPress={() => setQty((parseInt(qty)+10).toString())} style={styles.stepBtn}><Text style={styles.stepBtnText}>+</Text></TouchableOpacity>
            </View>

            <Text style={[styles.inputLabel, { marginTop: 24 }]}>Price per kg ($):</Text>
            <View style={styles.stepperInput}>
                <TouchableOpacity onPress={() => setPrice(Math.max(0.1, parseFloat(price)-0.01).toFixed(2))} style={styles.stepBtn}><Text style={styles.stepBtnText}>-</Text></TouchableOpacity>
                <TextInput style={styles.input} value={price} onChangeText={setPrice} keyboardType="numeric" />
                <TouchableOpacity onPress={() => setPrice((parseFloat(price)+0.01).toFixed(2))} style={styles.stepBtn}><Text style={styles.stepBtnText}>+</Text></TouchableOpacity>
            </View>
            <Text style={styles.hint}>Asking: $0.45/kg | Market Avg: $0.44/kg</Text>

            <Text style={[styles.inputLabel, { marginTop: 24 }]}>Delivery Method:</Text>
            <TouchableOpacity style={styles.radio} onPress={() => setDelivery('seller')}>
                <View style={[styles.radioCircle, delivery === 'seller' && styles.radioActive]} />
                <Text style={styles.radioText}>Seller Transport ($50)</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.radio} onPress={() => setDelivery('pickup')}>
                <View style={[styles.radioCircle, delivery === 'pickup' && styles.radioActive]} />
                <Text style={styles.radioText}>Buyer Pickup (Free)</Text>
            </TouchableOpacity>
        </View>
      </View>

      {/* Summary */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ESCROW SUMMARY</Text>
        <View style={styles.card}>
            <View style={styles.summaryRow}><Text style={styles.summaryLabel}>Offer Amount:</Text><Text style={styles.summaryVal}>${amount.toFixed(2)}</Text></View>
            <View style={styles.summaryRow}><Text style={styles.summaryLabel}>Platform Fee (1%):</Text><Text style={styles.summaryVal}>${fee.toFixed(2)}</Text></View>
            <View style={[styles.summaryRow, { borderTopWidth: 1, borderTopColor: '#EEE', paddingTop: 12, marginTop: 12 }]}><Text style={[styles.summaryLabel, { fontWeight: '800', color: theme.colors.black }]}>Total to Pay:</Text><Text style={[styles.summaryVal, { fontWeight: '800', color: theme.colors.green, fontSize: 18 }]}>${total.toFixed(2)}</Text></View>
            <View style={styles.escrowInfo}>
                <Text style={styles.escrowInfoText}>🛡️ Your funds will be held securely in escrow until you confirm receipt.</Text>
            </View>
        </View>
      </View>

      <TouchableOpacity style={styles.submitBtn} onPress={() => Alert.alert('Offer Submitted', 'Success! $'+total.toFixed(2)+' has been held in escrow.')}>
        <Text style={styles.submitBtnText}>SUBMIT OFFER & PAY</Text>
      </TouchableOpacity>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { padding: 24, paddingTop: 60, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backBtn: { fontSize: 16, fontWeight: '700', color: theme.colors.sky },
  headerTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.black },
  section: { marginTop: 24, paddingHorizontal: 24 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#999', letterSpacing: 1.2, marginBottom: 12 },
  card: { padding: 20, backgroundColor: '#FFF', borderRadius: 16, borderWidth: 1, borderColor: '#EEE' },
  sellerName: { fontSize: 18, fontWeight: '800', color: theme.colors.black },
  sellerRating: { fontSize: 14, fontWeight: '700', color: theme.colors.gold },
  sellerBadge: { fontSize: 12, fontWeight: '700', color: '#666', backgroundColor: '#F5F5F5', padding: 6, borderRadius: 6 },
  detailRow: { fontSize: 14, color: '#999', marginBottom: 8, fontWeight: '600' },
  detailVal: { color: theme.colors.black, fontWeight: '800' },
  formCard: { padding: 24, backgroundColor: '#F9F9F9', borderRadius: 20 },
  inputLabel: { fontSize: 14, fontWeight: '800', color: theme.colors.black, marginBottom: 12 },
  stepperInput: { flexDirection: 'row', backgroundColor: '#FFF', borderRadius: 12, borderWidth: 1, borderColor: '#DDD', height: 54, alignItems: 'center', overflow: 'hidden' },
  stepBtn: { width: 60, height: '100%', backgroundColor: '#F5F5F5', justifyContent: 'center', alignItems: 'center' },
  stepBtnText: { fontSize: 24, fontWeight: '700', color: '#666' },
  input: { flex: 1, textAlign: 'center', fontSize: 18, fontWeight: '800', color: theme.colors.black },
  hint: { fontSize: 12, color: '#999', marginTop: 8, fontWeight: '600' },
  radio: { flexDirection: 'row', alignItems: 'center', marginTop: 16 },
  radioCircle: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: '#DDD', marginRight: 12 },
  radioActive: { backgroundColor: theme.colors.sky, borderColor: theme.colors.sky },
  radioText: { fontSize: 14, fontWeight: '700', color: '#666' },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  summaryLabel: { fontSize: 14, color: '#666', fontWeight: '600' },
  summaryVal: { fontSize: 14, color: theme.colors.black, fontWeight: '800' },
  escrowInfo: { marginTop: 16, backgroundColor: '#FFFDE7', padding: 12, borderRadius: 12, borderLeftWidth: 4, borderLeftColor: theme.colors.gold },
  escrowInfoText: { fontSize: 12, color: '#856404', fontWeight: '600' },
  submitBtn: { margin: 24, height: 64, backgroundColor: theme.colors.sky, borderRadius: 16, justifyContent: 'center', alignItems: 'center', elevation: 4 },
  submitBtnText: { color: '#FFF', fontSize: 18, fontWeight: '800' }
});
