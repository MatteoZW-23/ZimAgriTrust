import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, Alert, Platform,
} from 'react-native';
import {
  Phone as IconPhone, MapPin as IconMapPin, Truck as IconTruck, 
  Shield as IconShield, Star as IconStar, LogOut as IconLogOut, 
  ChevronRight as IconChevronRight, Bell as IconBell, 
  HelpCircle as IconHelpCircle, Settings as IconSettings, 
  Award as IconAward, FileText as IconFileText, Camera as IconCamera,
  CheckCircle as IconCheckCircle, Clock as IconClock, 
  XCircle as IconXCircle, User as IconUser, Package as IconPackage,
} from 'lucide-react-native';
import { theme } from '../styles';
import { getDriverProfile, updateAvailability } from '../api';
import { clearSession } from '../utils/auth';

// Simple arc-based completion ring using border trick
function CompletionRing({ percent }) {
  const size = 80;
  const color = percent >= 100 ? '#4CAF50' : theme.colors.sky;
  return (
    <View style={{ width: size, height: size, justifyContent: 'center', alignItems: 'center' }}>
      <View style={{
        width: size, height: size, borderRadius: size / 2,
        borderWidth: 6, borderColor: '#F0F0F0',
        position: 'absolute',
      }} />
      <View style={{
        width: size, height: size, borderRadius: size / 2,
        borderWidth: 6, borderColor: color,
        borderTopColor: percent < 25 ? '#F0F0F0' : color,
        borderRightColor: percent < 50 ? '#F0F0F0' : color,
        borderBottomColor: percent < 75 ? '#F0F0F0' : color,
        position: 'absolute',
      }} />
      <Text style={{ fontSize: 17, fontWeight: '900', color: theme.colors.dark }}>{percent}%</Text>
    </View>
  );
}

const DOC_STATUS = {
  verified: { color: '#4CAF50', bg: '#F0FDF4', icon: IconCheckCircle, label: 'Verified' },
  pending:  { color: '#F59E0B', bg: '#FFFBEB', icon: IconClock,        label: 'Under Review' },
  missing:  { color: '#9E9E9E', bg: '#F5F5F5', icon: IconXCircle,      label: 'Not uploaded' },
};

const DOCUMENTS = [
  { key: 'license',  label: "Driver's License",    status: 'verified', icon: IconFileText },
  { key: 'vehicle',  label: 'Vehicle Registration', status: 'verified', icon: IconTruck },
  { key: 'insurance',label: 'Insurance Certificate',status: 'pending',  icon: IconShield },
  { key: 'photo',    label: 'Profile Photo',        status: 'missing',  icon: IconCamera },
];

const ACHIEVEMENTS = [
  { label: '100 Deliveries', icon: IconAward,       earned: true },
  { label: 'On-Time Pro',    icon: IconCheckCircle, earned: true },
  { label: '5-Star Rating',  icon: IconStar,        earned: false },
  { label: 'Night Shift',    icon: IconTruck,       earned: false },
];

const MENU_ITEMS = [
  { icon: IconSettings,    color: theme.colors.sky, label: 'Account Settings', sub: 'Name, phone, password' },
  { icon: IconBell,        color: '#F59E0B',         label: 'Notifications',    sub: 'Push, SMS, email' },
  { icon: IconShield,      color: '#4CAF50',         label: 'Privacy & Security', sub: 'Data, permissions' },
  { icon: IconHelpCircle,  color: '#9C27B0',         label: 'Help & Support',   sub: 'FAQ, contact us' },
];

export default function ProfileScreen({ route, navigation, onLogout: onLogoutProp }) {
  const { token, profile: initialProfile = {}, onLogout: onLogoutParam } = route.params || {};
  const onLogout = onLogoutProp || onLogoutParam;
  const [profile, setProfile] = useState(initialProfile);

  useEffect(() => {
    if (token) {
      getDriverProfile(token)
        .then(data => setProfile(prev => ({ ...prev, ...data })))
        .catch(() => {});
    }
  }, [token]);

  const toggleAvailability = async () => {
    const newVal = !profile.is_available;
    try {
      await updateAvailability(token, newVal);
      setProfile({ ...profile, is_available: newVal });
    } catch (err) {
      Alert.alert('Error', 'Failed to update availability');
    }
  };

  const handleLogout = () => {
    if (Platform.OS === 'web') {
      clearSession().then(() => { if (onLogout) onLogout(); });
      return;
    }
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out', style: 'destructive',
          onPress: async () => { await clearSession(); if (onLogout) onLogout(); },
        },
      ],
    );
  };

  const rating = profile.rating || 4.8;
  const completionPercent = 75;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>

        <View style={styles.header}>
          <Text style={styles.headerTitle}>Profile</Text>
        </View>

        {/* Hero card */}
        <View style={styles.heroCard}>
          <View style={styles.avatarRow}>
            <View style={styles.avatar}>
              <IconTruck size={32} color={theme.colors.sky} />
            </View>
            <View style={styles.avatarInfo}>
              <Text style={styles.name}>{profile.full_name || 'Driver'}</Text>
              <View style={styles.roleBadge}>
                <IconCheckCircle size={10} color="#4CAF50" />
                <Text style={styles.roleText}>VERIFIED DRIVER</Text>
              </View>
              <View style={styles.phoneRow}>
                <IconPhone size={12} color="#999" />
                <Text style={styles.phoneText}>{profile.phone_number || '+263 77 •••'}</Text>
              </View>
            </View>
          </View>

          <View style={styles.statsGrid}>
            <View style={styles.statBox}>
              <IconStar size={16} color="#F59E0B" />
              <Text style={styles.statVal}>{rating}</Text>
              <Text style={styles.statLabel}>Rating</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <IconCheckCircle size={16} color="#4CAF50" />
              <Text style={styles.statVal}>{profile.total_deliveries || 142}</Text>
              <Text style={styles.statLabel}>Trips</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <IconAward size={16} color={theme.colors.sky} />
              <Text style={styles.statVal}>98%</Text>
              <Text style={styles.statLabel}>On-Time</Text>
            </View>
          </View>
        </View>

        {/* Profile completion */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Profile Completion</Text>
          <View style={styles.completionCard}>
            <CompletionRing percent={completionPercent} />
            <View style={styles.completionText}>
              <Text style={styles.completionHeading}>
                {completionPercent < 100 ? 'Almost there!' : 'Complete!'}
              </Text>
              <Text style={styles.completionSub}>
                {completionPercent < 100
                  ? 'Upload your profile photo to complete your profile'
                  : 'Your profile is fully verified'}
              </Text>
              {completionPercent < 100 && (
                <TouchableOpacity 
                  style={styles.completeBtn} 
                  activeOpacity={0.8}
                  onPress={() => navigation.navigate('EditProfile', { token, profile })}
                >
                  <IconCamera size={13} color="#FFF" />
                  <Text style={styles.completeBtnText}>Upload Photo</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </View>

        {/* Availability Toggle */}
        <View style={styles.section}>
          <TouchableOpacity 
            style={[styles.onlineToggle, profile.is_available ? styles.onlineBg : styles.offlineBg]}
            onPress={toggleAvailability}
            activeOpacity={0.8}
          >
            <View style={[styles.onlineDot, profile.is_available ? styles.dotGreen : styles.dotGray]} />
            <Text style={styles.onlineText}>
              {profile.is_available ? 'You are ONLINE' : 'You are OFFLINE'}
            </Text>
            <Text style={styles.toggleHint}>
              {profile.is_available ? 'Tap to go offline' : 'Tap to go online'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Vehicle */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Vehicle</Text>
          <View style={styles.vehicleCard}>
            <VehicleRow
              icon={<IconTruck size={18} color={theme.colors.sky} />}
              bg="#E1F5FE"
              label="Type"
              value={profile.vehicle_type || '10-Ton Truck'}
            />
            <View style={styles.vDivider} />
            <VehicleRow
              icon={<IconPackage size={18} color="#F59E0B" />}
              bg="#FFFBEB"
              label="Capacity"
              value={`${profile.carrying_capacity_kg || 5000} kg`}
            />
            <View style={styles.vDivider} />
            <VehicleRow
              icon={<IconMapPin size={18} color="#4CAF50" />}
              bg="#F0FDF4"
              label="Operating Area"
              value={profile.operating_district || 'Harare Metropolitan'}
            />
          </View>
        </View>

        {/* Documents */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Documents</Text>
          {DOCUMENTS.map(doc => {
            const Icon = doc.icon;
            const st = DOC_STATUS[doc.status];
            const StatusIcon = st.icon;
            return (
              <TouchableOpacity key={doc.key} style={styles.docRow} activeOpacity={0.75}>
                <View style={[styles.docIcon, { backgroundColor: st.bg }]}>
                  <Icon size={16} color={st.color} />
                </View>
                <View style={styles.docInfo}>
                  <Text style={styles.docLabel}>{doc.label}</Text>
                  <View style={styles.docStatusRow}>
                    <StatusIcon size={11} color={st.color} />
                    <Text style={[styles.docStatus, { color: st.color }]}>{st.label}</Text>
                  </View>
                </View>
                <IconChevronRight size={16} color="#DDD" />
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Achievements */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Achievements</Text>
          <View style={styles.badgesRow}>
            {ACHIEVEMENTS.map((a, i) => {
              const Icon = a.icon;
              return (
                <View key={i} style={[styles.badgeItem, !a.earned && styles.badgeLocked]}>
                  <View style={[styles.badgeIconWrap, { backgroundColor: a.earned ? '#E1F5FE' : '#F5F5F5' }]}>
                    <Icon size={20} color={a.earned ? theme.colors.sky : '#CCC'} />
                  </View>
                  <Text style={[styles.badgeLabel, !a.earned && styles.badgeLabelLocked]}>
                    {a.label}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Settings</Text>
          <TouchableOpacity 
            style={styles.menuItem} 
            activeOpacity={0.75}
            onPress={() => navigation.navigate('Settings', { token })}
          >
            <View style={styles.menuLeft}>
              <View style={[styles.menuIcon, { backgroundColor: theme.colors.sky + '18' }]}>
                <IconSettings size={20} color={theme.colors.sky} />
              </View>
              <View>
                <Text style={styles.menuLabel}>Account Settings</Text>
                <Text style={styles.menuSub}>Notifications, Security, Privacy</Text>
              </View>
            </View>
            <IconChevronRight size={18} color="#DDD" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.menuItem} 
            activeOpacity={0.75}
            onPress={() => navigation.navigate('ChangePin', { token })}
          >
            <View style={styles.menuLeft}>
              <View style={[styles.menuIcon, { backgroundColor: '#F59E0B18' }]}>
                <IconShield size={20} color="#F59E0B" />
              </View>
              <View>
                <Text style={styles.menuLabel}>Security & PIN</Text>
                <Text style={styles.menuSub}>Change your 4-digit PIN</Text>
              </View>
            </View>
            <IconChevronRight size={18} color="#DDD" />
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.menuItem} 
            activeOpacity={0.75}
            onPress={() => navigation.navigate('Support')}
          >
            <View style={styles.menuLeft}>
              <View style={[styles.menuIcon, { backgroundColor: '#8B5CF618' }]}>
                <IconHelpCircle size={20} color="#8B5CF6" />
              </View>
              <View>
                <Text style={styles.menuLabel}>Help & Support</Text>
                <Text style={styles.menuSub}>FAQ and Contact Us</Text>
              </View>
            </View>
            <IconChevronRight size={18} color="#DDD" />
          </TouchableOpacity>
        </View>

        {/* Sign out */}
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.8}>
          <IconLogOut size={18} color="#EF4444" />
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>

        <Text style={styles.version}>ZimAgriTrust Driver v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function VehicleRow({ icon, bg, label, value }) {
  return (
    <View style={styles.vehicleRow}>
      <View style={[styles.vIcon, { backgroundColor: bg }]}>{icon}</View>
      <View style={{ flex: 1 }}>
        <Text style={styles.vLabel}>{label}</Text>
        <Text style={styles.vVal}>{value}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  scrollContent: { paddingBottom: 120 },

  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 },
  headerTitle: { fontSize: 28, fontWeight: '900', color: theme.colors.dark },

  heroCard: {
    marginHorizontal: 20, backgroundColor: '#FFF', borderRadius: 24,
    padding: 20, ...theme.shadows.sm, borderWidth: 1, borderColor: '#F0F0F0',
  },
  avatarRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  avatar: {
    width: 72, height: 72, borderRadius: 36,
    backgroundColor: '#E1F5FE', justifyContent: 'center', alignItems: 'center',
    borderWidth: 3, borderColor: 'rgba(41,182,246,0.2)',
  },
  avatarInfo: { flex: 1, marginLeft: 16 },
  name: { fontSize: 20, fontWeight: '900', color: theme.colors.dark },
  roleBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#F0FDF4', alignSelf: 'flex-start',
    paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8, marginTop: 4,
  },
  roleText: { fontSize: 10, fontWeight: '800', color: '#4CAF50', letterSpacing: 0.5 },
  phoneRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  phoneText: { fontSize: 13, color: '#999', fontWeight: '500' },

  statsGrid: { flexDirection: 'row', backgroundColor: '#F8F9FA', borderRadius: 16, padding: 14 },
  statBox: { flex: 1, alignItems: 'center', gap: 4 },
  statVal: { fontSize: 18, fontWeight: '900', color: theme.colors.dark },
  statLabel: { fontSize: 11, fontWeight: '600', color: '#999' },
  statDivider: { width: 1, backgroundColor: '#E8E8E8' },

  section: { marginHorizontal: 20, marginTop: 24 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#BBB', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 },

  completionCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    borderRadius: 20, padding: 20, borderWidth: 1, borderColor: '#F0F0F0',
  },
  completionText: { flex: 1, marginLeft: 20 },
  completionHeading: { fontSize: 16, fontWeight: '800', color: theme.colors.dark },
  completionSub: { fontSize: 12, color: '#999', marginTop: 4, lineHeight: 18 },
  completeBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: theme.colors.sky, alignSelf: 'flex-start',
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 10, marginTop: 10,
  },
  completeBtnText: { color: '#FFF', fontSize: 12, fontWeight: '800' },

  vehicleCard: { backgroundColor: '#FFF', borderRadius: 20, padding: 16, borderWidth: 1, borderColor: '#F0F0F0' },
  vehicleRow: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 8 },
  vIcon: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  vLabel: { fontSize: 11, color: '#999', fontWeight: '600' },
  vVal: { fontSize: 15, fontWeight: '700', color: theme.colors.dark, marginTop: 1 },
  vDivider: { height: 1, backgroundColor: '#F5F5F5', marginLeft: 50 },

  docRow: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    padding: 14, borderRadius: 14, marginBottom: 8, borderWidth: 1, borderColor: '#F5F5F5',
  },
  docIcon: { width: 36, height: 36, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginRight: 14 },
  docInfo: { flex: 1 },
  docLabel: { fontSize: 14, fontWeight: '700', color: theme.colors.dark },
  docStatusRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 3 },
  docStatus: { fontSize: 11, fontWeight: '600' },

  badgesRow: { flexDirection: 'row', gap: 10 },
  badgeItem: {
    flex: 1, alignItems: 'center', backgroundColor: '#FFF',
    borderRadius: 16, padding: 14, borderWidth: 1, borderColor: '#F0F0F0', gap: 8,
  },
  badgeLocked: { opacity: 0.45 },
  badgeIconWrap: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  badgeLabel: { fontSize: 10, fontWeight: '700', color: theme.colors.dark, textAlign: 'center' },
  badgeLabelLocked: { color: '#CCC' },

  menuItem: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: '#FFF', padding: 14, borderRadius: 16, marginBottom: 8,
    borderWidth: 1, borderColor: '#F5F5F5',
  },
  menuLeft: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  menuIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  menuLabel: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  menuSub: { fontSize: 11, color: '#BBB', fontWeight: '500', marginTop: 1 },

  logoutBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    marginHorizontal: 20, marginTop: 32, paddingVertical: 16, borderRadius: 16,
    backgroundColor: '#FEF2F2', borderWidth: 1, borderColor: '#FECACA',
  },
  logoutText: { fontSize: 15, fontWeight: '700', color: '#EF4444' },
  version: { textAlign: 'center', fontSize: 11, color: '#DDD', marginTop: 16, fontWeight: '600', marginBottom: 8 },

  onlineToggle: {
    padding: 20, borderRadius: 24, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, position: 'relative', overflow: 'hidden',
  },
  onlineBg: { backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' },
  offlineBg: { backgroundColor: '#F9FAFB', borderColor: '#E5E7EB' },
  onlineDot: { width: 8, height: 8, borderRadius: 4, position: 'absolute', top: 12, right: 12 },
  dotGreen: { backgroundColor: '#10B981' },
  dotGray: { backgroundColor: '#9CA3AF' },
  onlineText: { fontSize: 16, fontWeight: '900', color: theme.colors.dark },
  toggleHint: { fontSize: 11, fontWeight: '700', color: '#999', marginTop: 4, textTransform: 'uppercase' },
});
