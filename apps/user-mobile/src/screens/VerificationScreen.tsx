import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, ActivityIndicator, Alert, Platform
} from 'react-native';
import {
  ArrowLeft as IconArrowLeft,
  ClipboardList as IconClipboard,
  Clock as IconClock,
  CheckCircle2 as IconCheckCircle,
  XCircle as IconXCircle,
  Camera as IconCamera,
  Image as IconImage,
  Check as IconCheck
} from 'lucide-react-native';
import { theme } from '../styles';
import { submitIdDocuments, getVerificationStatus } from '../api';

// Expo ImagePicker — gracefully falls back if not available
let launchImageLibraryAsync, launchCameraAsync, MediaTypeOptions;
try {
  const ip = require('expo-image-picker');
  launchImageLibraryAsync = ip.launchImageLibraryAsync;
  launchCameraAsync = ip.launchCameraAsync;
  MediaTypeOptions = ip.MediaTypeOptions;
} catch {
  launchImageLibraryAsync = null;
}

const STATUS_CONFIG = {
  not_submitted: { color: '#94a3b8', icon: IconClipboard, label: 'Not Submitted' },
  pending:       { color: '#f59e0b', icon: IconClock, label: 'Under Review' },
  approved:      { color: '#22c55e', icon: IconCheckCircle, label: 'Verified' },
  rejected:      { color: '#ef4444', icon: IconXCircle, label: 'Rejected — Resubmit' },
};

export default function VerificationScreen({ navigation, route }) {
  const { token } = route?.params || {};

  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [nationalId, setNationalId] = useState('');
  const [front, setFront] = useState(null);
  const [back, setBack] = useState(null);
  const [selfie, setSelfie] = useState(null);
  const hasLoaded = useRef(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    if (hasLoaded.current) return; // Prevent repeated calls
    hasLoaded.current = true;
    if (!token) { setLoading(false); return; }
    try {
      const data = await getVerificationStatus(token);
      setStatus(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const pickImage = async (slot) => {
    if (!launchImageLibraryAsync) {
      Alert.alert('Not available', 'Image picker requires Expo. Please use the web upload instead.');
      return;
    }
    Alert.alert(
      'Choose Source',
      'How would you like to add this photo?',
      [
        {
          text: 'Camera',
          onPress: async () => {
            const result = await launchCameraAsync({ mediaTypes: MediaTypeOptions.Images, quality: 0.8, allowsEditing: true });
            if (!result.canceled && result.assets?.[0]) {
              const asset = result.assets[0];
              const file = { uri: asset.uri, name: `${slot}.jpg`, type: 'image/jpeg' };
              if (slot === 'front') setFront(file);
              else if (slot === 'back') setBack(file);
              else setSelfie(file);
            }
          }
        },
        {
          text: 'Gallery',
          onPress: async () => {
            const result = await launchImageLibraryAsync({ mediaTypes: MediaTypeOptions.Images, quality: 0.8, allowsEditing: true });
            if (!result.canceled && result.assets?.[0]) {
              const asset = result.assets[0];
              const file = { uri: asset.uri, name: `${slot}.jpg`, type: 'image/jpeg' };
              if (slot === 'front') setFront(file);
              else if (slot === 'back') setBack(file);
              else setSelfie(file);
            }
          }
        },
        { text: 'Cancel', style: 'cancel' }
      ]
    );
  };

  const handleSubmit = async () => {
    if (!front) { setError('Front of ID is required.'); return; }
    if (!token) { setError('You must be logged in.'); return; }
    setSubmitting(true); setError(''); setSuccess('');
    try {
      await submitIdDocuments(token, { front, back, selfie, nationalIdNumber: nationalId });
      setSuccess('Documents submitted! An agent will review within 24 hours. You will be notified via WhatsApp & SMS.');
      await loadStatus();
    } catch (e) {
      setError(e.message || 'Upload failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const cfg = STATUS_CONFIG[status?.status || 'not_submitted'];
  const canSubmit = status?.status !== 'pending' && status?.status !== 'approved';

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={theme.colors.green} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 120 }} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtnBox}>
          <IconArrowLeft size={22} color={theme.colors.black} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>ID Verification</Text>
        <View style={{ width: 44 }} />
      </View>

      {/* Status Banner */}
      <View style={[styles.statusBanner, { borderColor: cfg.color, backgroundColor: cfg.color + '15' }]}>
        <cfg.icon size={32} color={cfg.color} />
        <View style={{ flex: 1 }}>
          <Text style={[styles.statusLabel, { color: cfg.color }]}>{cfg.label}</Text>
          {status?.reviewer_note && (
            <Text style={styles.statusNote}>{status.reviewer_note}</Text>
          )}
          {status?.status === 'approved' && (
            <Text style={styles.statusNote}>Your identity is verified. Trust score +15 applied.</Text>
          )}
        </View>
      </View>

      {/* Info */}
      <View style={styles.infoBox}>
        <View style={styles.rowAlignCenter}>
          <IconClipboard size={18} color={theme.colors.black} style={{ marginRight: 8 }} />
          <Text style={styles.infoTitle}>Why verify?</Text>
        </View>
        <Text style={styles.infoText}>
          Verified users unlock higher transaction limits, appear as trusted sellers, and get priority in the marketplace.
          Your documents are reviewed by a certified ZimAgritrust agent within 24 hours.
        </Text>
      </View>

      {canSubmit && (
        <>
          {/* National ID Number */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>NATIONAL ID NUMBER</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. 63-123456A78"
              value={nationalId}
              onChangeText={setNationalId}
              autoCapitalize="characters"
            />
          </View>

          {/* Document Uploads */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>REQUIRED DOCUMENTS</Text>

            <UploadSlot
              label="National ID — Front *"
              hint="Clear photo of the front of your National ID card."
              file={front}
              onPick={() => pickImage('front')}
              onClear={() => setFront(null)}
            />
            <UploadSlot
              label="National ID — Back"
              hint="Back of your ID card (optional but recommended)."
              file={back}
              onPick={() => pickImage('back')}
              onClear={() => setBack(null)}
            />
            <UploadSlot
              label="Selfie Holding ID"
              hint="Hold your ID clearly next to your face."
              file={selfie}
              onPick={() => pickImage('selfie')}
              onClear={() => setSelfie(null)}
            />
          </View>

          {error ? <Text style={styles.errorText}>{error}</Text> : null}
          {success ? <Text style={styles.successText}>{success}</Text> : null}

          <TouchableOpacity
            style={[styles.submitBtn, (!front || submitting) && { opacity: 0.5 }]}
            onPress={handleSubmit}
            disabled={!front || submitting}
          >
            {submitting
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.submitBtnText}>Submit for Verification</Text>
            }
          </TouchableOpacity>
        </>
      )}

      {status?.status === 'pending' && (
        <View style={styles.pendingBox}>
          <Text style={styles.pendingText}>
            Your documents are being reviewed. You will receive a WhatsApp and SMS notification once the review is complete.
          </Text>
          <Text style={styles.pendingMeta}>
            Submitted: {status.submitted_at ? new Date(status.submitted_at).toLocaleDateString('en-ZW', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

function UploadSlot({ label, hint, file, onPick, onClear }) {
  return (
    <View style={styles.uploadCard}>
      <Text style={styles.uploadLabel}>{label}</Text>
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
      {file ? (
        <View style={styles.uploadedRow}>
          <IconCheck size={18} color="#166534" style={{ marginRight: 8 }} />
          <Text style={styles.uploadedName} numberOfLines={1}>{file.name}</Text>
          <TouchableOpacity onPress={onClear} style={styles.clearBtn}>
            <Text style={styles.clearBtnText}>Remove</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity style={styles.uploadBtn} onPress={onPick}>
          <IconCamera size={20} color="#64748b" style={{ marginRight: 10 }} />
          <Text style={styles.uploadBtnText}>Take Photo / Choose File</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.gray50 },
  header: { padding: 24, paddingTop: 60, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backBtnBox: { width: 46, height: 46, borderRadius: 23, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#E2E8F0', shadowColor: '#0F172A', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.05, shadowRadius: 14, elevation: 3 },
  headerTitle: { fontSize: 19, fontWeight: '900', color: theme.colors.ink },

  statusBanner: { marginHorizontal: 24, marginBottom: 8, padding: 20, borderRadius: 20, borderWidth: 1.5, flexDirection: 'row', alignItems: 'center', gap: 16, backgroundColor: '#FFFFFF', shadowColor: '#0F172A', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.05, shadowRadius: 16, elevation: 3 },
  statusLabel: { fontSize: 16, fontWeight: '900' },
  statusNote: { fontSize: 13, color: '#475569', fontWeight: '600', marginTop: 4 },

  infoBox: { marginHorizontal: 24, marginVertical: 16, padding: 20, backgroundColor: '#FFFFFF', borderRadius: 20, borderWidth: 1, borderColor: '#E2E8F0' },
  rowAlignCenter: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  infoTitle: { fontSize: 14, fontWeight: '900', color: theme.colors.ink },
  infoText: { fontSize: 13, color: '#64748b', lineHeight: 20 },

  section: { paddingHorizontal: 24, marginTop: 8 },
  sectionTitle: { fontSize: 11, fontWeight: '900', color: '#94a3b8', letterSpacing: 1.2, marginBottom: 12, textTransform: 'uppercase' },

  input: { height: 56, borderRadius: 16, backgroundColor: '#ffffff', borderWidth: 1.5, borderColor: '#e2e8f0', paddingHorizontal: 16, fontSize: 15, fontWeight: '700', color: theme.colors.ink, marginBottom: 8 },

  uploadCard: { marginBottom: 20 },
  uploadLabel: { fontSize: 14, fontWeight: '800', color: theme.colors.black, marginBottom: 4 },
  hint: { fontSize: 12, color: '#94a3b8', fontWeight: '600', marginBottom: 10 },
  uploadBtn: { height: 64, borderRadius: 16, borderStyle: 'dashed', borderWidth: 2, borderColor: '#cbd5e1', justifyContent: 'center', alignItems: 'center', backgroundColor: '#ffffff', flexDirection: 'row' },
  uploadBtnText: { fontSize: 14, fontWeight: '700', color: '#64748b' },
  uploadedRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 14, backgroundColor: '#f0fdf4', borderRadius: 16, borderWidth: 1.5, borderColor: '#86efac' },
  uploadedName: { flex: 1, fontSize: 13, fontWeight: '700', color: '#166534' },
  clearBtn: { paddingHorizontal: 12, paddingVertical: 6, backgroundColor: '#fee2e2', borderRadius: 8 },
  clearBtnText: { fontSize: 12, fontWeight: '800', color: '#ef4444' },

  errorText: { marginHorizontal: 24, marginTop: 8, color: '#ef4444', fontWeight: '700', fontSize: 13 },
  successText: { marginHorizontal: 24, marginTop: 8, color: '#16a34a', fontWeight: '700', fontSize: 13, lineHeight: 20 },

  submitBtn: { margin: 24, height: 60, backgroundColor: theme.colors.ink, borderRadius: 18, justifyContent: 'center', alignItems: 'center', shadowColor: '#0F172A', shadowOffset: { width: 0, height: 12 }, shadowOpacity: 0.16, shadowRadius: 18, elevation: 6 },
  submitBtnText: { color: '#FFF', fontSize: 16, fontWeight: '800' },

  pendingBox: { marginHorizontal: 24, marginTop: 16, padding: 24, backgroundColor: '#fffbeb', borderRadius: 20, borderWidth: 1.5, borderColor: '#fde68a' },
  pendingText: { fontSize: 14, color: '#92400e', fontWeight: '700', lineHeight: 22 },
  pendingMeta: { fontSize: 12, color: '#b45309', fontWeight: '600', marginTop: 12 },
});
