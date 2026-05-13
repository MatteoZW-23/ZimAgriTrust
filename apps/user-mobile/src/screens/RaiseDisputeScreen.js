import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Image, Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Camera, Send } from 'lucide-react-native';
import { getTransactions, raiseOrderDispute, uploadDisputeEvidence } from '../api';
import { theme } from '../styles';

const REASONS = ['quality', 'quantity', 'delivery', 'payment', 'other'];

export default function RaiseDisputeScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [orders, setOrders] = useState([]);
  const [orderId, setOrderId] = useState('');
  const [reason, setReason] = useState('quality');
  const [description, setDescription] = useState('');
  const [photos, setPhotos] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTransactions(token)
      .then((data) => {
        const items = Array.isArray(data) ? data : data?.data || [];
        setOrders(items);
        if (items[0]?.id) setOrderId(items[0].id);
      })
      .catch((err) => Alert.alert('Orders failed', err.message || 'Could not load orders.'))
      .finally(() => setLoading(false));
  }, [token]);

  const takePhoto = async () => {
    if (Platform.OS === 'web') {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = (event) => {
        const file = event.target.files?.[0];
        if (file) setPhotos((current) => [...current, { uri: URL.createObjectURL(file), name: file.name, type: file.type }]);
      };
      input.click();
      return;
    }
    const ImagePicker = require('expo-image-picker');
    const result = await ImagePicker.launchCameraAsync({ allowsEditing: true, quality: 0.75 });
    if (!result.canceled) setPhotos((current) => [...current, result.assets[0]]);
  };

  const submit = async () => {
    if (!orderId || description.trim().length < 3) {
      Alert.alert('Missing details', 'Select an order and describe the issue.');
      return;
    }
    try {
      setSaving(true);
      const dispute = await raiseOrderDispute(token, orderId, { reason, type: reason, description });
      if (photos.length > 0) await uploadDisputeEvidence(token, dispute.id, photos);
      Alert.alert('Dispute raised', 'Your case has been submitted.', [{ text: 'OK', onPress: () => navigation.goBack() }]);
    } catch (err) {
      Alert.alert('Submit failed', err.message || 'Could not raise dispute.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Raise Dispute</Text>
      <Text style={styles.subtitle}>Submit clear evidence so agents/admins can resolve the case fairly.</Text>

      {loading ? (
        <ActivityIndicator color={theme.colors.red} />
      ) : (
        <View style={styles.card}>
          <Text style={styles.label}>Order</Text>
          {orders.map((order) => (
            <TouchableOpacity key={order.id} style={[styles.option, orderId === order.id && styles.optionActive]} onPress={() => setOrderId(order.id)}>
              <Text style={[styles.optionText, orderId === order.id && styles.optionTextActive]}>{order.order_number || String(order.id).slice(0, 8)} - {order.status}</Text>
            </TouchableOpacity>
          ))}

          <Text style={styles.label}>Reason</Text>
          <View style={styles.reasonGrid}>
            {REASONS.map((item) => (
              <TouchableOpacity key={item} style={[styles.reason, reason === item && styles.reasonActive]} onPress={() => setReason(item)}>
                <Text style={[styles.reasonText, reason === item && styles.reasonTextActive]}>{item}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Description</Text>
          <TextInput
            style={styles.textarea}
            multiline
            placeholder="Explain what happened..."
            placeholderTextColor="#94a3b8"
            value={description}
            onChangeText={setDescription}
          />

          <Text style={styles.label}>Evidence photos</Text>
          <View style={styles.photos}>
            {photos.map((photo, index) => <Image key={index} source={{ uri: photo.uri }} style={styles.photo} />)}
            <TouchableOpacity style={styles.photoBtn} onPress={takePhoto}>
              <Camera size={22} color="#94a3b8" />
              <Text style={styles.photoText}>Add</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <TouchableOpacity style={[styles.submitBtn, saving && { opacity: 0.6 }]} onPress={submit} disabled={saving}>
        {saving ? <ActivityIndicator color="#fff" /> : <><Send size={18} color="#fff" /><Text style={styles.submitText}>Submit Dispute</Text></>}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff7ed' },
  content: { padding: 20, paddingTop: 56, paddingBottom: 120 },
  title: { color: '#111827', fontSize: 32, fontWeight: '900' },
  subtitle: { color: '#64748b', fontSize: 14, lineHeight: 21, marginTop: 8, marginBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#fed7aa' },
  label: { color: '#475569', fontSize: 12, fontWeight: '900', letterSpacing: 0.8, textTransform: 'uppercase', marginTop: 14, marginBottom: 8 },
  option: { backgroundColor: '#f8fafc', borderRadius: 14, padding: 12, borderWidth: 1, borderColor: '#e2e8f0', marginBottom: 8 },
  optionActive: { backgroundColor: theme.colors.red, borderColor: theme.colors.red },
  optionText: { color: '#334155', fontWeight: '800' },
  optionTextActive: { color: '#fff' },
  reasonGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  reason: { backgroundColor: '#f8fafc', borderRadius: 999, paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: '#e2e8f0' },
  reasonActive: { backgroundColor: theme.colors.red, borderColor: theme.colors.red },
  reasonText: { color: '#334155', fontWeight: '900', textTransform: 'capitalize' },
  reasonTextActive: { color: '#fff' },
  textarea: { minHeight: 130, backgroundColor: '#f8fafc', borderRadius: 16, borderWidth: 1, borderColor: '#e2e8f0', padding: 14, textAlignVertical: 'top', fontWeight: '700' },
  photos: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  photo: { width: 82, height: 82, borderRadius: 14 },
  photoBtn: { width: 82, height: 82, borderRadius: 14, backgroundColor: '#f8fafc', borderWidth: 1, borderColor: '#e2e8f0', alignItems: 'center', justifyContent: 'center' },
  photoText: { color: '#94a3b8', fontWeight: '900', marginTop: 4 },
  submitBtn: { backgroundColor: theme.colors.red, borderRadius: 16, paddingVertical: 15, marginTop: 16, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8 },
  submitText: { color: '#fff', fontWeight: '900', fontSize: 15 },
});
