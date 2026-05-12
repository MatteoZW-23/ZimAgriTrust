import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, SafeAreaView, ScrollView, Alert } from 'react-native';
import { Save, X } from 'lucide-react-native';
import { updateProfile } from '../api';
import { theme } from '../styles';

export default function EditProfileScreen({ route, navigation }) {
  const { token, profile = {}, onProfileUpdated } = route.params || {};
  const [fullName, setFullName] = useState(profile.full_name || profile.name || '');
  const [email, setEmail] = useState(profile.email || '');
  const [province, setProvince] = useState(profile.province || '');
  const [district, setDistrict] = useState(profile.district || '');
  const [preferredLanguage, setPreferredLanguage] = useState(profile.preferred_language || 'en');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!fullName.trim() || fullName.trim().length < 2) {
      Alert.alert('Check your name', 'Your full name must be at least 2 characters.');
      return;
    }

    try {
      setSaving(true);
      const updated = await updateProfile(token, {
        full_name: fullName.trim(),
        email: email.trim() || null,
        province: province.trim() || null,
        district: district.trim() || null,
        preferred_language: preferredLanguage.trim() || 'en',
      });
      if (onProfileUpdated) onProfileUpdated(updated);
      Alert.alert('Profile updated', 'Your personal details were saved securely.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err) {
      Alert.alert('Update failed', err.message || 'Could not update your profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.iconBtn} onPress={() => navigation.goBack()}>
            <X size={22} color={theme.colors.black} />
          </TouchableOpacity>
          <Text style={styles.title}>Account Settings</Text>
          <View style={styles.iconBtn} />
        </View>

        <View style={styles.card}>
          <Field label="Full name" value={fullName} onChangeText={setFullName} autoCapitalize="words" />
          <Field label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
          <Field label="Province" value={province} onChangeText={setProvince} autoCapitalize="words" />
          <Field label="District" value={district} onChangeText={setDistrict} autoCapitalize="words" />
          <Field label="Preferred language" value={preferredLanguage} onChangeText={setPreferredLanguage} autoCapitalize="none" />
        </View>

        <TouchableOpacity style={[styles.saveBtn, saving && styles.disabledBtn]} onPress={handleSave} disabled={saving}>
          <Save size={20} color="#FFF" />
          <Text style={styles.saveText}>{saving ? 'Saving...' : 'Save Changes'}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function Field({ label, ...props }) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput style={styles.input} placeholderTextColor="#999" {...props} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { padding: 20, paddingBottom: 60 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 },
  iconBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#FFF', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#EEE' },
  title: { fontSize: 22, fontWeight: '800', color: theme.colors.black },
  card: { backgroundColor: '#FFF', borderRadius: 20, padding: 18, borderWidth: 1, borderColor: '#F0F0F0' },
  field: { marginBottom: 16 },
  label: { fontSize: 13, fontWeight: '800', color: '#666', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.6 },
  input: { borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 14, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16, color: theme.colors.black, backgroundColor: '#FAFAFA' },
  saveBtn: { marginTop: 24, backgroundColor: theme.colors.green, borderRadius: 16, paddingVertical: 16, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 10 },
  disabledBtn: { opacity: 0.6 },
  saveText: { color: '#FFF', fontSize: 16, fontWeight: '800' },
});
