import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Image, Alert } from 'react-native';
import { theme } from '../styles';

export default function VerificationScreen({ navigation }) {
  const [uploads, setUploads] = useState({ front: false, back: false, selfie: false });

  const handleUpload = (type) => {
    setUploads({ ...uploads, [type]: true });
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}><Text style={styles.backBtn}>← Back</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>Account Verification</Text>
        <View style={{ width: 60 }} />
      </View>

      <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>📋 ID VERIFICATION</Text>
          <Text style={styles.infoText}>To increase your trust score and unlock full platform features, please verify your identity.</Text>
          <View style={styles.trustProgress}>
              <View style={styles.trustScoreTrack}>
                  <View style={[styles.trustScoreFill, { width: '45%' }]} />
              </View>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
                  <Text style={styles.trustLabel}>Current: 45/100</Text>
                  <Text style={[styles.trustLabel, { color: theme.colors.green }]}>Target: 65/100</Text>
              </View>
          </View>
      </View>

      <View style={styles.section}>
          <Text style={styles.sectionTitle}>REQUIRED DOCUMENTS</Text>
          
          <View style={styles.uploadCard}>
              <Text style={styles.uploadLabel}>National ID (Front)</Text>
              <TouchableOpacity style={[styles.uploadBtn, uploads.front && styles.uploadBtnSuccess]} onPress={() => handleUpload('front')}>
                  <Text style={styles.uploadBtnText}>{uploads.front ? '✅ Uploaded' : '📷 Take Photo / Upload'}</Text>
              </TouchableOpacity>
          </View>

          <View style={styles.uploadCard}>
              <Text style={styles.uploadLabel}>National ID (Back)</Text>
              <TouchableOpacity style={[styles.uploadBtn, uploads.back && styles.uploadBtnSuccess]} onPress={() => handleUpload('back')}>
                  <Text style={styles.uploadBtnText}>{uploads.back ? '✅ Uploaded' : '📷 Take Photo / Upload'}</Text>
              </TouchableOpacity>
          </View>

          <View style={styles.uploadCard}>
              <Text style={styles.uploadLabel}>Selfie with ID</Text>
              <TouchableOpacity style={[styles.uploadBtn, uploads.selfie && styles.uploadBtnSuccess]} onPress={() => handleUpload('selfie')}>
                  <Text style={styles.uploadBtnText}>{uploads.selfie ? '✅ Uploaded' : '📷 Take Photo / Upload'}</Text>
              </TouchableOpacity>
              <Text style={styles.hint}>Hold your ID clearly next to your face.</Text>
          </View>
      </View>

      <TouchableOpacity style={styles.submitBtn} onPress={() => Alert.alert('Submitted', 'Verification documents received. Agents will review within 24 hours.')}>
          <Text style={styles.submitBtnText}>Submit for Verification</Text>
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
  infoBox: { margin: 24, padding: 24, backgroundColor: '#F9F9F9', borderRadius: 20 },
  infoTitle: { fontSize: 14, fontWeight: '800', color: theme.colors.black, marginBottom: 8 },
  infoText: { fontSize: 14, color: '#666', lineHeight: 20 },
  trustProgress: { marginTop: 24 },
  trustScoreTrack: { height: 12, backgroundColor: '#EEE', borderRadius: 6, overflow: 'hidden' },
  trustScoreFill: { height: '100%', backgroundColor: theme.colors.orange },
  trustLabel: { fontSize: 12, fontWeight: '800', color: '#999' },
  section: { paddingHorizontal: 24, marginTop: 12 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#999', letterSpacing: 1.2, marginBottom: 16 },
  uploadCard: { marginBottom: 24 },
  uploadLabel: { fontSize: 14, fontWeight: '700', color: theme.colors.black, marginBottom: 12 },
  uploadBtn: { height: 64, borderRadius: 16, borderStyle: 'dashed', borderWidth: 2, borderColor: '#DDD', justifyContent: 'center', alignItems: 'center', backgroundColor: '#F9F9F9' },
  uploadBtnSuccess: { borderColor: theme.colors.green, backgroundColor: '#E8F5E9', borderStyle: 'solid' },
  uploadBtnText: { fontSize: 14, fontWeight: '700', color: '#666' },
  hint: { fontSize: 12, color: '#999', fontStyle: 'italic', marginTop: 8 },
  submitBtn: { margin: 24, height: 60, backgroundColor: theme.colors.black, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  submitBtnText: { color: '#FFF', fontSize: 16, fontWeight: '800' }
});
