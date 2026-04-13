import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, TextInput, StyleSheet, Alert } from 'react-native';
import { theme } from '../styles';

export default function ConfirmationScreen({ navigation, route }) {
  const { orderId = 'AG-067' } = route.params || {};
  const [rating, setRating] = useState(4);
  const [quality, setQuality] = useState('A');

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}><Text style={styles.backBtn}>← Back</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>Confirm Receipt</Text>
        <View style={{ width: 60 }} />
      </View>

      <View style={styles.heroSection}>
         <Text style={styles.heroTitle}>✅ DELIVERY RECEIVED?</Text>
         <Text style={styles.heroSub}>Please confirm that you have inspected the product. Once confirmed, funds will be released to the seller.</Text>
      </View>

      {/* Inspection Form */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>PRODUCT INSPECTION</Text>
        <View style={styles.card}>
            <Text style={styles.inputLabel}>Quality Grade Verified:</Text>
            {['Grade A (As described)', 'Grade B (Acceptable)', 'Grade C (Not as described)'].map((g, i) => (
                <TouchableOpacity key={i} style={styles.radio} onPress={() => setQuality(String.fromCharCode(65+i))}>
                    <View style={[styles.radioCircle, quality === String.fromCharCode(65+i) && styles.radioActive]} />
                    <Text style={styles.radioText}>{g}</Text>
                </TouchableOpacity>
            ))}

            <Text style={[styles.inputLabel, { marginTop: 24 }]}>Arrival Photos (Optional):</Text>
            <View style={styles.photoRow}>
               <TouchableOpacity style={styles.photoBox}><Text style={{ fontSize: 24, color: '#999' }}>+</Text></TouchableOpacity>
               <View style={styles.photoBox} />
               <View style={styles.photoBox} />
            </View>
        </View>
      </View>

      {/* Rating Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>RATE YOUR EXPERIENCE</Text>
        <View style={styles.card}>
            <Text style={styles.inputLabel}>Seller Rating:</Text>
            <View style={styles.starRow}>
                {[1,2,3,4,5].map(s => (
                    <TouchableOpacity key={s} onPress={() => setRating(s)}>
                        <Text style={[styles.star, { color: s <= rating ? theme.colors.gold : '#DDD' }]}>★</Text>
                    </TouchableOpacity>
                ))}
                <Text style={styles.starVal}>({rating.toFixed(1)})</Text>
            </View>

            <Text style={[styles.inputLabel, { marginTop: 24 }]}>Review (Optional):</Text>
            <TextInput
              style={styles.textArea}
              placeholder="How was the product and delivery service?"
              multiline
              numberOfLines={4}
            />
        </View>
      </View>

      {/* Warnings */}
      <View style={styles.warningBox}>
          <Text style={styles.warningTitle}>⚠️ IMPORTANT</Text>
          <Text style={styles.warningText}>• Confirming delivery releases funds immediately.</Text>
          <Text style={styles.warningText}>• This action cannot be undone.</Text>
          <Text style={styles.warningText}>• If there is an issue, raise a dispute instead.</Text>
      </View>

      <View style={styles.actionRow}>
           <TouchableOpacity style={styles.disputeBtn} onPress={() => Alert.alert('Dispute Raised', 'A market agent will be assigned to review your case.')}>
               <Text style={styles.disputeBtnText}>Raise Dispute</Text>
           </TouchableOpacity>
           <TouchableOpacity style={styles.confirmBtn} onPress={() => Alert.alert('Payment Released', 'Thank you! The seller has been notified.')}>
               <Text style={styles.confirmBtnText}>CONFIRM & RELEASE</Text>
           </TouchableOpacity>
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
  heroSection: { padding: 40, backgroundColor: '#F9F9F9', alignItems: 'center', textAlign: 'center' },
  heroTitle: { fontSize: 20, fontWeight: '800', color: theme.colors.black, marginBottom: 12 },
  heroSub: { fontSize: 14, color: '#666', textAlign: 'center', lineHeight: 20 },
  section: { marginTop: 24, paddingHorizontal: 24 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#999', letterSpacing: 1.2, marginBottom: 12 },
  card: { padding: 20, backgroundColor: '#FFF', borderRadius: 16, borderWidth: 1, borderColor: '#EEE' },
  inputLabel: { fontSize: 14, fontWeight: '800', color: theme.colors.black, marginBottom: 16 },
  radio: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  radioCircle: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: '#DDD', marginRight: 12 },
  radioActive: { backgroundColor: theme.colors.green, borderColor: theme.colors.green },
  radioText: { fontSize: 14, fontWeight: '700', color: '#666' },
  photoRow: { flexDirection: 'row', gap: 12 },
  photoBox: { width: 80, height: 80, borderRadius: 8, backgroundColor: '#F5F5F5', justifyContent: 'center', alignItems: 'center' },
  starRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  star: { fontSize: 32 },
  starVal: { fontSize: 18, fontWeight: '800', color: theme.colors.gold, marginLeft: 8 },
  textArea: { backgroundColor: '#F9F9F9', borderRadius: 12, padding: 16, minHeight: 100, textAlignVertical: 'top', fontSize: 14 },
  warningBox: { margin: 24, padding: 20, backgroundColor: '#FFF5F5', borderRadius: 12, borderLeftWidth: 4, borderLeftColor: theme.colors.red },
  warningTitle: { fontSize: 14, fontWeight: '800', color: theme.colors.red, marginBottom: 8 },
  warningText: { fontSize: 12, color: theme.colors.red, marginBottom: 4, fontWeight: '600' },
  actionRow: { flexDirection: 'row', paddingHorizontal: 24, gap: 12 },
  disputeBtn: { flex: 1, height: 54, backgroundColor: '#F5F5F5', borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  disputeBtnText: { color: '#666', fontWeight: '700' },
  confirmBtn: { flex: 2, height: 54, backgroundColor: theme.colors.green, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  confirmBtnText: { color: '#FFF', fontWeight: '800' }
});
