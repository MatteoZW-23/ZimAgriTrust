import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  SafeAreaView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { Lock as IconLock, ShieldCheck as IconShieldCheck, Check as IconCheck } from 'lucide-react-native';
import { theme } from '../styles';
import { changeDriverPin } from '../api';

export default function ChangePinScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    current_pin: '',
    new_pin: '',
    confirm_pin: '',
  });

  const handleChangePin = async () => {
    const { current_pin, new_pin, confirm_pin } = form;

    if (!current_pin || !new_pin || !confirm_pin) {
      Alert.alert('Error', 'Please fill all fields');
      return;
    }

    if (new_pin.length < 4) {
      Alert.alert('Error', 'PIN must be at least 4 digits');
      return;
    }

    if (new_pin !== confirm_pin) {
      Alert.alert('Error', 'New PIN and confirmation do not match');
      return;
    }

    // Basic PIN rules
    if (/^(\d)\1+$/.test(new_pin)) {
      Alert.alert('Error', 'PIN cannot be repeating digits');
      return;
    }

    setLoading(true);
    try {
      await changeDriverPin(token, current_pin, new_pin);
      Alert.alert('Success', 'PIN changed successfully', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (err) {
      Alert.alert('Error', err.message || 'Failed to change PIN');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <View style={styles.content}>
          <View style={styles.header}>
            <View style={styles.iconCircle}>
              <IconShieldCheck size={32} color={theme.colors.sky} />
            </View>
            <Text style={styles.title}>Change PIN</Text>
            <Text style={styles.subtitle}>Protect your account with a secure PIN</Text>
          </View>

          <View style={styles.form}>
            <PinInput
              label="Current PIN"
              value={form.current_pin}
              onChangeText={(t) => setForm({ ...form, current_pin: t })}
              placeholder="••••"
            />

            <PinInput
              label="New PIN"
              value={form.new_pin}
              onChangeText={(t) => setForm({ ...form, new_pin: t })}
              placeholder="••••"
            />

            <PinInput
              label="Confirm New PIN"
              value={form.confirm_pin}
              onChangeText={(t) => setForm({ ...form, confirm_pin: t })}
              placeholder="••••"
            />
          </View>

          <TouchableOpacity
            style={[styles.saveBtn, loading && styles.saveBtnDisabled]}
            onPress={handleChangePin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <>
                <IconCheck size={20} color="#FFF" />
                <Text style={styles.saveBtnText}>Update PIN</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function PinInput({ label, value, onChangeText, placeholder }) {
  return (
    <View style={styles.inputGroup}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.inputWrapper}>
        <IconLock size={18} color="#BBB" style={{ marginRight: 10 }} />
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor="#BBB"
          keyboardType="number-pad"
          secureTextEntry
          maxLength={6}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.gray50 },
  content: { flex: 1, padding: 24 },
  
  header: { alignItems: 'center', marginBottom: 40, marginTop: 20 },
  iconCircle: {
    width: 80, height: 80, borderRadius: 40,
    backgroundColor: '#F0F9FF', justifyContent: 'center', alignItems: 'center',
    marginBottom: 16, shadowColor: '#0EA5E9', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.12, shadowRadius: 16, elevation: 4,
  },
  title: { fontSize: 26, fontWeight: '900', color: theme.colors.ink, letterSpacing: -0.5 },
  subtitle: { fontSize: 14, color: '#64748B', marginTop: 8, textAlign: 'center', fontWeight: '600' },

  form: { gap: 24 },
  inputGroup: {},
  label: { fontSize: 13, fontWeight: '900', color: '#94A3B8', textTransform: 'uppercase', marginBottom: 8, letterSpacing: 0.5 },
  inputWrapper: {
    flexDirection: 'row', alignItems: 'center',
    borderBottomWidth: 2, borderBottomColor: '#E2E8F0', paddingBottom: 10,
  },
  input: { flex: 1, height: 40, color: theme.colors.ink, fontSize: 18, fontWeight: '800', letterSpacing: 4 },

  saveBtn: {
    backgroundColor: theme.colors.dark, flexDirection: 'row',
    height: 56, borderRadius: 18, justifyContent: 'center', alignItems: 'center',
    marginTop: 'auto', marginBottom: 20, gap: 10, shadowColor: '#0F172A', shadowOffset: { width: 0, height: 12 }, shadowOpacity: 0.16, shadowRadius: 18, elevation: 6,
  },
  saveBtnDisabled: { opacity: 0.7 },
  saveBtnText: { color: '#FFF', fontSize: 16, fontWeight: '800' },
});
