import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ScrollView, SafeAreaView, Alert, ActivityIndicator,
  TextInputProps,
} from 'react-native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';
import {
  User, Mail, Phone, MapPin, Camera, Check, Truck,
} from 'lucide-react-native';
import { theme } from '../styles';
import ScreenHeader from '../components/ScreenHeader';
import { updateDriverProfile, updateVehicleInfo } from '../api';

const VEHICLE_TYPES = ['Pickup', 'Truck', 'Lorry', 'Van', 'Bakkie', 'Flatbed'];

interface RouteParams {
  token: string;
  profile?: {
    full_name?: string;
    email?: string;
    phone_number?: string;
    address?: string;
    operating_district?: string;
    vehicle_type?: string;
    vehicle_reg?: string;
    vehicle_model?: string;
    vehicle_year?: string;
    carrying_capacity_kg?: number;
  };
}

interface EditProfileScreenProps {
  route: RouteProp<{ params: RouteParams }, 'params'>;
  navigation: NativeStackNavigationProp<any>;
}

export default function EditProfileScreen({ route, navigation }: EditProfileScreenProps) {
  const { token, profile = {} } = route.params || {};
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('personal');

  const [personal, setPersonal] = useState({
    full_name: profile.full_name || '',
    email: profile.email || '',
    phone_number: profile.phone_number || '',
    address: profile.address || profile.operating_district || '',
  });

  const [vehicle, setVehicle] = useState({
    vehicle_type: profile.vehicle_type || '',
    vehicle_reg: profile.vehicle_reg || '',
    vehicle_model: profile.vehicle_model || '',
    vehicle_year: profile.vehicle_year || '',
    carrying_capacity_kg: String(profile.carrying_capacity_kg || ''),
  });

  const handleSavePersonal = async () => {
    if (!personal.full_name.trim()) {
      Alert.alert('Required', 'Full name cannot be empty.');
      return;
    }
    setLoading(true);
    try {
      await updateDriverProfile(token, personal);
      Alert.alert('Saved', 'Personal info updated.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err) {
      Alert.alert('Error', err.message || 'Could not save changes.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveVehicle = async () => {
    if (!vehicle.vehicle_type || !vehicle.vehicle_reg) {
      Alert.alert('Required', 'Vehicle type and registration are required.');
      return;
    }
    setLoading(true);
    try {
      await updateVehicleInfo(token, {
        ...vehicle,
        carrying_capacity_kg: Number(vehicle.carrying_capacity_kg) || 0,
      });
      Alert.alert('Saved', 'Vehicle info updated.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err) {
      Alert.alert('Error', err.message || 'Could not save changes.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScreenHeader
        title="Edit Profile"
        navigation={navigation}
        rightElement={
          <TouchableOpacity
            style={styles.saveBtn}
            onPress={activeTab === 'personal' ? handleSavePersonal : handleSaveVehicle}
            disabled={loading}
          >
            {loading
              ? <ActivityIndicator size="small" color="#FFF" />
              : <Check size={18} color="#FFF" />
            }
          </TouchableOpacity>
        }
      />

      {/* Tab switcher */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'personal' && styles.tabActive]}
          onPress={() => setActiveTab('personal')}
        >
          <User size={16} color={activeTab === 'personal' ? theme.colors.sky : '#999'} />
          <Text style={[styles.tabText, activeTab === 'personal' && styles.tabTextActive]}>
            Personal
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'vehicle' && styles.tabActive]}
          onPress={() => setActiveTab('vehicle')}
        >
          <Truck size={16} color={activeTab === 'vehicle' ? theme.colors.sky : '#999'} />
          <Text style={[styles.tabText, activeTab === 'vehicle' && styles.tabTextActive]}>
            Vehicle
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        {activeTab === 'personal' ? (
          <>
            {/* Avatar */}
            <View style={styles.avatarSection}>
              <View style={styles.avatarWrap}>
                <View style={styles.avatar}>
                  <User size={40} color={theme.colors.sky} />
                </View>
                <TouchableOpacity style={styles.cameraBtn} activeOpacity={0.8}>
                  <Camera size={16} color="#FFF" />
                </TouchableOpacity>
              </View>
              <Text style={styles.avatarHint}>Tap to change photo</Text>
            </View>

            <Field
              label="Full Name"
              icon={<User size={18} color="#BBB" />}
              value={personal.full_name}
              onChangeText={t => setPersonal(p => ({ ...p, full_name: t }))}
              placeholder="Your full name"
            />
            <Field
              label="Email Address"
              icon={<Mail size={18} color="#BBB" />}
              value={personal.email}
              onChangeText={t => setPersonal(p => ({ ...p, email: t }))}
              placeholder="you@example.com"
              keyboardType="email-address"
              autoCapitalize="none"
            />
            <Field
              label="Phone Number"
              icon={<Phone size={18} color="#BBB" />}
              value={personal.phone_number}
              onChangeText={t => setPersonal(p => ({ ...p, phone_number: t }))}
              placeholder="+263 7..."
              keyboardType="phone-pad"
              editable={false}
              note="Phone number cannot be changed here."
            />
            <Field
              label="Home Address"
              icon={<MapPin size={18} color="#BBB" />}
              value={personal.address}
              onChangeText={t => setPersonal(p => ({ ...p, address: t }))}
              placeholder="Your physical address"
            />

            <TouchableOpacity
              style={[styles.primaryBtn, loading && styles.primaryBtnDisabled]}
              onPress={handleSavePersonal}
              disabled={loading}
            >
              {loading
                ? <ActivityIndicator color="#FFF" />
                : <><Check size={20} color="#FFF" /><Text style={styles.primaryBtnText}>Save Personal Info</Text></>
              }
            </TouchableOpacity>
          </>
        ) : (
          <>
            {/* Vehicle type chips */}
            <Text style={styles.fieldLabel}>Vehicle Type</Text>
            <View style={styles.chipRow}>
              {VEHICLE_TYPES.map(t => (
                <TouchableOpacity
                  key={t}
                  style={[styles.chip, vehicle.vehicle_type === t && styles.chipActive]}
                  onPress={() => setVehicle(v => ({ ...v, vehicle_type: t }))}
                >
                  <Text style={[styles.chipText, vehicle.vehicle_type === t && styles.chipTextActive]}>
                    {t}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Field
              label="Registration Plate"
              icon={<Truck size={18} color="#BBB" />}
              value={vehicle.vehicle_reg}
              onChangeText={t => setVehicle(v => ({ ...v, vehicle_reg: t.toUpperCase() }))}
              placeholder="e.g. ABC 1234"
              autoCapitalize="characters"
            />
            <Field
              label="Make & Model"
              icon={<Truck size={18} color="#BBB" />}
              value={vehicle.vehicle_model}
              onChangeText={t => setVehicle(v => ({ ...v, vehicle_model: t }))}
              placeholder="e.g. Toyota Hilux"
            />
            <Field
              label="Year"
              icon={<Truck size={18} color="#BBB" />}
              value={vehicle.vehicle_year}
              onChangeText={t => setVehicle(v => ({ ...v, vehicle_year: t }))}
              placeholder="e.g. 2020"
              keyboardType="number-pad"
              maxLength={4}
            />
            <Field
              label="Carrying Capacity (kg)"
              icon={<Truck size={18} color="#BBB" />}
              value={vehicle.carrying_capacity_kg}
              onChangeText={t => setVehicle(v => ({ ...v, carrying_capacity_kg: t }))}
              placeholder="e.g. 5000"
              keyboardType="number-pad"
            />

            <TouchableOpacity
              style={[styles.primaryBtn, loading && styles.primaryBtnDisabled]}
              onPress={handleSaveVehicle}
              disabled={loading}
            >
              {loading
                ? <ActivityIndicator color="#FFF" />
                : <><Check size={20} color="#FFF" /><Text style={styles.primaryBtnText}>Save Vehicle Info</Text></>
              }
            </TouchableOpacity>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

interface FieldProps {
  label: string;
  icon: React.ReactNode;
  note?: string;
}

function Field({ label, icon, note, ...inputProps }: FieldProps & TextInputProps) {
  return (
    <View style={styles.fieldGroup}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={[styles.fieldWrap, inputProps.editable === false && styles.fieldDisabled]}>
        <View style={styles.fieldIcon}>{icon}</View>
        <TextInput
          style={styles.fieldInput}
          placeholderTextColor="#CCC"
          {...inputProps}
        />
      </View>
      {note ? <Text style={styles.fieldNote}>{note}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  scroll: { padding: 20, paddingBottom: 60 },

  saveBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: theme.colors.sky,
    justifyContent: 'center', alignItems: 'center',
  },

  tabs: {
    flexDirection: 'row', backgroundColor: '#FFF',
    borderBottomWidth: 1, borderBottomColor: '#F0F0F0',
  },
  tab: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 6, paddingVertical: 14, borderBottomWidth: 2, borderBottomColor: 'transparent',
  },
  tabActive: { borderBottomColor: theme.colors.sky },
  tabText: { fontSize: 14, fontWeight: '700', color: '#999' },
  tabTextActive: { color: theme.colors.sky },

  avatarSection: { alignItems: 'center', marginBottom: 28, marginTop: 8 },
  avatarWrap: { width: 100, height: 100, position: 'relative' },
  avatar: {
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: '#E1F5FE', justifyContent: 'center', alignItems: 'center',
    borderWidth: 2, borderColor: '#B3E5FC',
  },
  cameraBtn: {
    position: 'absolute', bottom: 0, right: 0,
    backgroundColor: theme.colors.sky, width: 32, height: 32, borderRadius: 16,
    justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: '#FFF',
  },
  avatarHint: { fontSize: 12, color: '#999', marginTop: 8, fontWeight: '600' },

  fieldGroup: { marginBottom: 18 },
  fieldLabel: {
    fontSize: 11, fontWeight: '800', color: '#BBB',
    textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8,
  },
  fieldWrap: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    borderRadius: 14, borderWidth: 1.5, borderColor: '#E8E8E8',
    paddingHorizontal: 14, height: 52,
  },
  fieldDisabled: { backgroundColor: '#F8F9FA', borderColor: '#F0F0F0' },
  fieldIcon: { marginRight: 10 },
  fieldInput: { flex: 1, fontSize: 15, fontWeight: '600', color: theme.colors.dark },
  fieldNote: { fontSize: 11, color: '#BBB', marginTop: 5, marginLeft: 4 },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
  chip: {
    paddingHorizontal: 16, paddingVertical: 9, borderRadius: 20,
    borderWidth: 1.5, borderColor: '#E0E0E0', backgroundColor: '#FFF',
  },
  chipActive: { borderColor: theme.colors.sky, backgroundColor: '#E1F5FE' },
  chipText: { fontSize: 13, fontWeight: '700', color: '#666' },
  chipTextActive: { color: theme.colors.sky },

  primaryBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    backgroundColor: theme.colors.sky, height: 56, borderRadius: 18,
    marginTop: 12, ...theme.shadows.sm,
  },
  primaryBtnDisabled: { opacity: 0.7 },
  primaryBtnText: { color: '#FFF', fontSize: 16, fontWeight: '800' },
});
