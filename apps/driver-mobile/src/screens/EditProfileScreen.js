import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ScrollView, SafeAreaView, Alert, ActivityIndicator,
} from 'react-native';
import { 
  User as IconUser, Mail as IconMail, Phone as IconPhone, 
  MapPin as IconMapPin, Camera as IconCamera, Check as IconCheck 
} from 'lucide-react-native';
import { theme } from '../styles';
import { updateDriverProfile } from '../api';

export default function EditProfileScreen({ route, navigation }) {
  const { token, profile = {} } = route.params || {};
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    full_name: profile.full_name || '',
    email: profile.email || '',
    phone_number: profile.phone_number || '',
    address: profile.address || '',
  });

  const handleSave = async () => {
    if (!form.full_name.trim()) {
      Alert.alert('Error', 'Full name is required');
      return;
    }

    setLoading(true);
    try {
      await updateDriverProfile(token, form);
      Alert.alert('Success', 'Profile updated successfully', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (err) {
      Alert.alert('Error', err.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Edit Profile</Text>
        </View>

        <View style={styles.avatarSection}>
          <View style={styles.avatarContainer}>
            <View style={styles.avatar}>
              <IconUser size={40} color={theme.colors.sky} />
            </View>
            <TouchableOpacity style={styles.cameraBtn} activeOpacity={0.8}>
              <IconCamera size={18} color="#FFF" />
            </TouchableOpacity>
          </View>
          <Text style={styles.avatarHint}>Tap to change photo</Text>
        </View>

        <View style={styles.form}>
          <InputGroup
            label="Full Name"
            icon={<IconUser size={18} color="#999" />}
            value={form.full_name}
            onChangeText={(t) => setForm({ ...form, full_name: t })}
            placeholder="Enter your full name"
          />

          <InputGroup
            label="Email Address"
            icon={<IconMail size={18} color="#999" />}
            value={form.email}
            onChangeText={(t) => setForm({ ...form, email: t })}
            placeholder="yourname@example.com"
            keyboardType="email-address"
          />

          <InputGroup
            label="Phone Number"
            icon={<IconPhone size={18} color="#999" />}
            value={form.phone_number}
            onChangeText={(t) => setForm({ ...form, phone_number: t })}
            placeholder="+263 7..."
            keyboardType="phone-pad"
          />

          <InputGroup
            label="Address"
            icon={<IconMapPin size={18} color="#999" />}
            value={form.address}
            onChangeText={(t) => setForm({ ...form, address: t })}
            placeholder="Physical address"
            multiline
          />
        </View>

        <TouchableOpacity
          style={[styles.saveBtn, loading && styles.saveBtnDisabled]}
          onPress={handleSave}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <IconCheck size={20} color="#FFF" />
              <Text style={styles.saveBtnText}>Save Changes</Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function InputGroup({ label, icon, value, onChangeText, placeholder, ...props }) {
  return (
    <View style={styles.inputGroup}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.inputWrapper}>
        <View style={styles.inputIcon}>{icon}</View>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor="#BBB"
          {...props}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  scrollContent: { padding: 20 },
  header: { marginBottom: 24 },
  title: { fontSize: 24, fontWeight: '900', color: theme.colors.dark },
  
  avatarSection: { alignItems: 'center', marginBottom: 32 },
  avatarContainer: { width: 100, height: 100, position: 'relative' },
  avatar: {
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: '#E1F5FE', justifyContent: 'center', alignItems: 'center',
    borderWidth: 1, borderColor: '#B3E5FC',
  },
  cameraBtn: {
    position: 'absolute', bottom: 0, right: 0,
    backgroundColor: theme.colors.sky, width: 32, height: 32, borderRadius: 16,
    justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: '#FFF',
  },
  avatarHint: { fontSize: 12, color: '#999', marginTop: 8, fontWeight: '600' },

  form: { gap: 20 },
  inputGroup: {},
  label: { fontSize: 13, fontWeight: '800', color: '#BBB', textTransform: 'uppercase', marginBottom: 8, marginLeft: 4 },
  inputWrapper: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    borderRadius: 14, borderWidth: 1, borderColor: '#E8E8E8', paddingHorizontal: 12,
  },
  inputIcon: { marginRight: 10 },
  input: { flex: 1, height: 50, color: theme.colors.dark, fontSize: 15, fontWeight: '600' },

  saveBtn: {
    backgroundColor: theme.colors.sky, flexDirection: 'row',
    height: 56, borderRadius: 18, justifyContent: 'center', alignItems: 'center',
    marginTop: 40, gap: 10, ...theme.shadows.sm,
  },
  saveBtnDisabled: { opacity: 0.7 },
  saveBtnText: { color: '#FFF', fontSize: 16, fontWeight: '800' },
});
