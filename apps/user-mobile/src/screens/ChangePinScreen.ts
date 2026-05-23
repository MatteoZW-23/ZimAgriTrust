import React, { useState } from 'react';
import { ActivityIndicator, Alert, SafeAreaView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { LockKeyhole } from 'lucide-react-native';
import { changePin } from '../api';
import { theme } from '../styles';

export default function ChangePinScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [currentPin, setCurrentPin] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!/^\d{4,6}$/.test(newPin)) {
      Alert.alert('Invalid PIN', 'PIN must be 4 to 6 digits.');
      return;
    }
    if (newPin !== confirmPin) {
      Alert.alert('PIN mismatch', 'Please confirm the same new PIN.');
      return;
    }
    try {
      setSaving(true);
      await changePin(token, currentPin, newPin);
      Alert.alert('PIN changed', 'Your PIN has been updated.', [{ text: 'OK', onPress: () => navigation.goBack() }]);
    } catch (err) {
      Alert.alert('Change failed', err.message || 'Could not change PIN.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.card}>
        <LockKeyhole size={36} color={theme.colors.green} />
        <Text style={styles.title}>Change PIN</Text>
        <Text style={styles.subtitle}>Use a secure 4-6 digit PIN. Avoid repeated or obvious numbers.</Text>
        <PinInput placeholder="Current PIN" value={currentPin} onChangeText={setCurrentPin} />
        <PinInput placeholder="New PIN" value={newPin} onChangeText={setNewPin} />
        <PinInput placeholder="Confirm new PIN" value={confirmPin} onChangeText={setConfirmPin} />
        <TouchableOpacity style={[styles.button, saving && { opacity: 0.6 }]} onPress={submit} disabled={saving}>
          {saving ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Update PIN</Text>}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

function PinInput(props) {
  return <TextInput {...props} style={styles.input} secureTextEntry keyboardType="number-pad" maxLength={6} placeholderTextColor="#94a3b8" />;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F0DE', justifyContent: 'center', padding: 20 },
  card: { backgroundColor: '#fff', borderRadius: 28, padding: 24, borderWidth: 1, borderColor: '#e5e7eb' },
  title: { color: '#111827', fontSize: 28, fontWeight: '900', marginTop: 14 },
  subtitle: { color: '#64748b', fontSize: 14, lineHeight: 21, marginTop: 8, marginBottom: 18 },
  input: { backgroundColor: '#f8fafc', borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 16, padding: 15, fontSize: 18, fontWeight: '900', marginBottom: 12, letterSpacing: 4 },
  button: { backgroundColor: theme.colors.green, borderRadius: 16, paddingVertical: 16, alignItems: 'center', marginTop: 8 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '900' },
});
