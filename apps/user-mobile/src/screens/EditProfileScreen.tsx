import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, SafeAreaView, ScrollView, Alert, Image, Platform } from 'react-native';
import { Save as IconSave, X as IconX, Camera, Upload } from 'lucide-react-native';
import { updateProfile, uploadProfilePhoto } from '../api';
import { theme } from '../styles';

export default function EditProfileScreen({ route, navigation }) {
  const { token, profile = {}, onProfileUpdated } = route.params || {};
  const [fullName, setFullName] = useState(profile.full_name || profile.name || '');
  const [email, setEmail] = useState(profile.email || '');
  const [province, setProvince] = useState(profile.province || '');
  const [district, setDistrict] = useState(profile.district || '');
  const [preferredLanguage, setPreferredLanguage] = useState(profile.preferred_language || 'en');
  const [saving, setSaving] = useState(false);
  const [photoUri, setPhotoUri] = useState(profile.photo_url || null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

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
        photo_url: photoUri,
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

  const handlePhotoUpload = async () => {
    Alert.alert(
      'Upload Photo',
      'Choose photo source',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Camera', onPress: () => Alert.alert('Camera', 'Camera functionality would be implemented here') },
        { text: 'Gallery', onPress: () => Alert.alert('Gallery', 'Gallery functionality would be implemented here') },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.iconBtn} onPress={() => navigation.goBack()}>
            <IconX size={22} color={theme.colors.black} />
          </TouchableOpacity>
          <Text style={styles.title}>Account Settings</Text>
          <View style={styles.iconBtn} />
        </View>

        <View style={styles.card}>
          <View style={styles.photoSection}>
            <View style={styles.photoContainer}>
              {photoUri ? (
                <Image source={{ uri: photoUri }} style={styles.photo} />
              ) : (
                <View style={styles.photoPlaceholder}>
                  <Upload size={32} color="#cbd5e1" />
                </View>
              )}
            </View>
            <TouchableOpacity style={styles.photoBtn} onPress={handlePhotoUpload}>
              <Camera size={16} color={theme.colors.green} />
              <Text style={styles.photoBtnText}>Change Photo</Text>
            </TouchableOpacity>
          </View>

          <Field label="Full name" value={fullName} onChangeText={setFullName} autoCapitalize="words" />
          <Field label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
          <Field label="Province" value={province} onChangeText={setProvince} autoCapitalize="words" />
          <Field label="District" value={district} onChangeText={setDistrict} autoCapitalize="words" />
          <Field label="Preferred language" value={preferredLanguage} onChangeText={setPreferredLanguage} autoCapitalize="none" />
        </View>

        <TouchableOpacity style={[styles.saveBtn, saving && styles.disabledBtn]} onPress={handleSave} disabled={saving}>
          <IconSave size={20} color="#FFF" />
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
  container: { flex: 1, backgroundColor: theme.colors.gray50 },
  content: { padding: 20, paddingBottom: 60 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 26, paddingTop: 8 },
  iconBtn: { width: 46, height: 46, borderRadius: 23, backgroundColor: '#FFF', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#E2E8F0', shadowColor: '#0F172A', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.05, shadowRadius: 14, elevation: 3 },
  title: { fontSize: 24, fontWeight: '900', color: theme.colors.ink, letterSpacing: -0.5 },
  card: { backgroundColor: '#FFF', borderRadius: 26, padding: 20, borderWidth: 1, borderColor: '#E2E8F0', shadowColor: '#0F172A', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.06, shadowRadius: 18, elevation: 4 },
  photoSection: { alignItems: 'center', marginBottom: 24, paddingBottom: 24, borderBottomWidth: 1, borderBottomColor: '#F0F0F0' },
  photoContainer: { width: 100, height: 100, borderRadius: 50, overflow: 'hidden', marginBottom: 12 },
  photo: { width: '100%', height: '100%' },
  photoPlaceholder: { width: '100%', height: '100%', backgroundColor: '#F8FAFC', justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: '#E2E8F0' },
  photoBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 18, paddingVertical: 10, backgroundColor: '#F0FDF4', borderRadius: 14, borderWidth: 1, borderColor: '#BBF7D0' },
  photoBtnText: { fontSize: 13, fontWeight: '800', color: theme.colors.green },
  field: { marginBottom: 16 },
  label: { fontSize: 13, fontWeight: '900', color: '#94A3B8', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.7 },
  input: { borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 16, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: theme.colors.ink, backgroundColor: '#FFFFFF' },
  saveBtn: { marginTop: 24, backgroundColor: theme.colors.green, borderRadius: 18, paddingVertical: 16, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 10, shadowColor: '#16A34A', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.18, shadowRadius: 16, elevation: 6 },
  disabledBtn: { opacity: 0.6 },
  saveText: { color: '#FFF', fontSize: 16, fontWeight: '800' },
});
