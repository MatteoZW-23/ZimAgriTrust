import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput, Alert } from 'react-native';
import { theme } from '../styles';

export default function AgentVerificationScreen({ navigation, route }) {
  const { listingId = 'L-1024', sector = 'CROPS' } = route.params || {};
  const [checklist, setChecklist] = useState({
    q1: false, q2: false, q3: false, q4: false
  });

  const sectorQuestions = {
    CROPS: [
      { id: 'q1', text: 'Moisture content verified < 12.5%?' },
      { id: 'q2', text: 'Pest/mold inspection completed?' },
      { id: 'q3', text: 'Packaging matches listing (50kg bags)?' },
      { id: 'q4', text: 'Farmer ID matches account?' }
    ],
    LIVESTOCK: [
      { id: 'q1', text: 'Vet health certificates presented?' },
      { id: 'q2', text: 'Ear tags / brands match records?' },
      { id: 'q3', text: 'Physical health/weight verified?' },
      { id: 'q4', text: 'Movement permit verified?' }
    ],
    POULTRY: [
      { id: 'q1', text: 'Batch health verified?' },
      { id: 'q2', text: 'Vaccination records confirmed?' },
      { id: 'q3', text: 'Feeding/housing conditions checked?' },
      { id: 'q4', text: 'Processing readiness confirmed?' }
    ]
  };

  const questions = sectorQuestions[sector] || sectorQuestions.CROPS;

  const toggle = (id) => setChecklist({ ...checklist, [id]: !checklist[id] });

  const allDone = Object.values(checklist).every(v => v);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}><Text style={styles.backBtn}>← Back</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>Field Verification</Text>
        <View style={{ width: 60 }} />
      </View>

      <View style={styles.summaryBox}>
          <Text style={styles.summaryTitle}>LISTING ID: {listingId}</Text>
          <Text style={styles.summarySub}>Sector: {sector} | Regional Inspection</Text>
      </View>

      <View style={styles.section}>
          <Text style={styles.sectionTitle}>INSPECTION CHECKLIST</Text>
          <View style={styles.card}>
              {questions.map((q, i) => (
                  <TouchableOpacity key={q.id} style={[styles.checkRow, i === 0 && { borderTopWidth: 0 }]} onPress={() => toggle(q.id)}>
                      <View style={[styles.checkBox, checklist[q.id] && styles.checkActive]}>
                          {checklist[q.id] && <Text style={styles.checkIcon}>✓</Text>}
                      </View>
                      <Text style={[styles.checkText, checklist[q.id] && styles.checkTextActive]}>{q.text}</Text>
                  </TouchableOpacity>
              ))}
          </View>
      </View>

      <View style={styles.section}>
          <Text style={styles.sectionTitle}>AGENT OBSERVATIONS</Text>
          <TextInput
            style={styles.textArea}
            placeholder="Add specific comments about produce quality or farmer feedback..."
            multiline
            numberOfLines={4}
          />
      </View>

      <View style={styles.section}>
          <Text style={styles.sectionTitle}>EVIDENCE CAPTURE</Text>
          <View style={styles.photoRow}>
               <TouchableOpacity style={styles.photoBox}><Text style={{ fontSize: 24, color: '#999' }}>📷</Text></TouchableOpacity>
               <TouchableOpacity style={styles.photoBox}><Text style={{ fontSize: 24, color: '#999' }}>📹</Text></TouchableOpacity>
          </View>
      </View>

      <View style={styles.actionRow}>
           <TouchableOpacity style={styles.rejectBtn} onPress={() => Alert.alert('Rejected', 'Produce marked as suspicious. Alerting regional HQ.')}>
               <Text style={styles.rejectBtnText}>REJECT</Text>
           </TouchableOpacity>
           <TouchableOpacity 
             style={[styles.verifyBtn, !allDone && { opacity: 0.5 }]} 
             disabled={!allDone}
             onPress={() => Alert.alert('Verified!', 'Digital certificate issued. Listing is now public.')}
           >
               <Text style={styles.verifyBtnText}>APPROVE & VERIFY</Text>
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
  summaryBox: { marginHorizontal: 24, padding: 20, backgroundColor: theme.colors.black, borderRadius: 16 },
  summaryTitle: { fontSize: 18, fontWeight: '900', color: '#FFF' },
  summarySub: { fontSize: 12, color: theme.colors.sky, fontWeight: '700', marginTop: 4 },
  section: { marginTop: 24, paddingHorizontal: 24 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#999', letterSpacing: 1.2, marginBottom: 12 },
  card: { backgroundColor: '#FFF', borderRadius: 16, borderWidth: 1, borderColor: '#EEE', overflow: 'hidden' },
  checkRow: { flexDirection: 'row', alignItems: 'center', padding: 20, borderTopWidth: 1, borderTopColor: '#EEE' },
  checkBox: { width: 24, height: 24, borderRadius: 6, borderWidth: 2, borderColor: '#DDD', marginRight: 16, justifyContent: 'center', alignItems: 'center' },
  checkActive: { backgroundColor: theme.colors.green, borderColor: theme.colors.green },
  checkIcon: { color: '#FFF', fontSize: 14, fontWeight: '900' },
  checkText: { fontSize: 14, fontWeight: '700', color: '#666', flex: 1 },
  checkTextActive: { color: theme.colors.black },
  textArea: { backgroundColor: '#F9F9F9', borderRadius: 12, padding: 16, minHeight: 100, textAlignVertical: 'top', fontSize: 14 },
  photoRow: { flexDirection: 'row', gap: 12 },
  photoBox: { width: 80, height: 80, borderRadius: 16, backgroundColor: '#F5F5F5', justifyContent: 'center', alignItems: 'center', borderStyle: 'dashed', borderWidth: 2, borderColor: '#DDD' },
  actionRow: { flexDirection: 'row', padding: 24, gap: 12 },
  rejectBtn: { flex: 1, height: 54, backgroundColor: '#FFF5F5', borderRadius: 12, justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: theme.colors.red },
  rejectBtnText: { color: theme.colors.red, fontWeight: '800' },
  verifyBtn: { flex: 2, height: 54, backgroundColor: theme.colors.green, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  verifyBtnText: { color: '#FFF', fontWeight: '800' }
});
