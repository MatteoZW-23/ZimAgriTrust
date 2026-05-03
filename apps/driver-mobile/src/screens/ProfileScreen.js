import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView, Alert, Platform } from 'react-native';
import { Phone, MapPin, Truck, Shield, Star, LogOut, ChevronRight, Bell, HelpCircle, Settings, Award, FileText, Camera, CheckCircle, Clock as ClockIcon } from 'lucide-react-native';
import { theme } from '../styles';
import { getDriverProfile } from '../api';
import { clearSession } from '../utils/auth';

function CompletionRing({ percent }) {
  const size = 80;
  return (
    <View style={{ width: size, height: size, justifyContent: 'center', alignItems: 'center' }}>
      <View style={{ width: size, height: size, borderRadius: size / 2, borderWidth: 6, borderColor: '#F0F0F0', justifyContent: 'center', alignItems: 'center', position: 'absolute' }} />
      <View style={{ width: size, height: size, borderRadius: size / 2, borderWidth: 6, borderColor: percent >= 100 ? '#4CAF50' : theme.colors.sky, borderTopColor: percent < 25 ? '#F0F0F0' : undefined, borderRightColor: percent < 50 ? '#F0F0F0' : undefined, borderBottomColor: percent < 75 ? '#F0F0F0' : undefined, justifyContent: 'center', alignItems: 'center', position: 'absolute' }} />
      <Text style={{ fontSize: 18, fontWeight: '900', color: theme.colors.dark }}>{percent}%</Text>
    </View>
  );
}

const DOCUMENTS = [
  { key: 'license', label: "Driver's License", status: 'verified', icon: FileText },
  { key: 'vehicle', label: 'Vehicle Registration', status: 'verified', icon: Truck },
  { key: 'insurance', label: 'Insurance Certificate', status: 'pending', icon: Shield },
  { key: 'photo', label: 'Profile Photo', status: 'missing', icon: Camera },
];

const ACHIEVEMENTS = [
  { label: '100 Deliveries', emoji: '🏆', earned: true },
  { label: 'On-Time Pro', emoji: '⚡', earned: true },
  { label: '5-Star Rating', emoji: '⭐', earned: false },
  { label: 'Night Owl', emoji: '🦉', earned: false },
];

export default function ProfileScreen({ route }) {
  const { token, profile: initialProfile = {}, onLogout } = route.params || {};
  const [profile, setProfile] = useState(initialProfile);

  useEffect(() => {
    if (token) {
      getDriverProfile(token)
        .then(data => setProfile(prev => ({ ...prev, ...data })))
        .catch(() => {});
    }
  }, [token]);

  const handleLogout = () => {
    if (Platform.OS === 'web') {
      clearSession().then(() => { if (onLogout) onLogout(); });
      return;
    }
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign Out', style: 'destructive', onPress: async () => { await clearSession(); if (onLogout) onLogout(); }},
    ]);
  };

  const rating = profile.rating || 4.8;
  const completionPercent = 75;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Profile</Text>
        </View>

        {/* Profile Hero */}
        <View style={styles.heroCard}>
          <View style={styles.heroTop}>
            <View style={styles.avatarSection}>
              <View style={styles.avatar}>
                <Text style={{ fontSize: 36 }}>🚚</Text>
              </View>
              <View style={{ flex: 1, marginLeft: 16 }}>
                <Text style={styles.name}>{profile.full_name || 'Driver'}</Text>
                <View style={styles.roleBadge}><Text style={styles.roleText}>VERIFIED DRIVER</Text></View>
                <View style={styles.phoneRow}>
                  <Phone size={12} color="#999" />
                  <Text style={styles.phoneText}>{profile.phone_number || '+263 77 •••'}</Text>
                </View>
              </View>
            </View>
          </View>

          <View style={styles.statsGrid}>
            <View style={styles.statBox}>
              <Star size={16} color="#FFC107" />
              <Text style={styles.statVal}>{rating}</Text>
              <Text style={styles.statLabel}>Rating</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <CheckCircle size={16} color="#4CAF50" />
              <Text style={styles.statVal}>142</Text>
              <Text style={styles.statLabel}>Trips</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <Award size={16} color={theme.colors.sky} />
              <Text style={styles.statVal}>98%</Text>
              <Text style={styles.statLabel}>On-Time</Text>
            </View>
          </View>
        </View>

        {/* Profile Completion */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Profile Completion</Text>
          <View style={styles.completionCard}>
            <CompletionRing percent={completionPercent} />
            <View style={{ flex: 1, marginLeft: 20 }}>
              <Text style={styles.completionTitle}>{completionPercent < 100 ? 'Almost there!' : 'Complete!'}</Text>
              <Text style={styles.completionSub}>{completionPercent < 100 ? 'Upload your profile photo to complete your profile' : 'Your profile is fully verified'}</Text>
              {completionPercent < 100 && (
                <TouchableOpacity style={styles.completeBtn}>
                  <Text style={styles.completeBtnText}>Complete Now</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </View>

        {/* Vehicle Details */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Vehicle</Text>
          <View style={styles.vehicleCard}>
            <View style={styles.vehicleRow}>
              <View style={[styles.vIcon, { backgroundColor: '#E1F5FE' }]}><Truck size={18} color={theme.colors.sky} /></View>
              <View style={{ flex: 1 }}><Text style={styles.vLabel}>Type</Text><Text style={styles.vVal}>{profile.vehicle_type || '10-Ton Truck'}</Text></View>
            </View>
            <View style={styles.vDivider} />
            <View style={styles.vehicleRow}>
              <View style={[styles.vIcon, { backgroundColor: '#FFF3E0' }]}><Text style={{ fontSize: 15 }}>📦</Text></View>
              <View style={{ flex: 1 }}><Text style={styles.vLabel}>Capacity</Text><Text style={styles.vVal}>{profile.carrying_capacity_kg || 5000} kg</Text></View>
            </View>
            <View style={styles.vDivider} />
            <View style={styles.vehicleRow}>
              <View style={[styles.vIcon, { backgroundColor: '#E8F5E9' }]}><MapPin size={18} color="#4CAF50" /></View>
              <View style={{ flex: 1 }}><Text style={styles.vLabel}>Operating Area</Text><Text style={styles.vVal}>{profile.operating_district || 'Harare Metropolitan'}</Text></View>
            </View>
          </View>
        </View>

        {/* Documents */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Documents</Text>
          {DOCUMENTS.map(doc => {
            const Icon = doc.icon;
            const isVerified = doc.status === 'verified';
            const isPending = doc.status === 'pending';
            return (
              <TouchableOpacity key={doc.key} style={styles.docRow}>
                <View style={[styles.docIcon, { backgroundColor: isVerified ? '#E8F5E9' : isPending ? '#FFF8E1' : '#F5F5F5' }]}>
                  <Icon size={16} color={isVerified ? '#4CAF50' : isPending ? '#FF9800' : '#999'} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.docLabel}>{doc.label}</Text>
                  <Text style={[styles.docStatus, { color: isVerified ? '#4CAF50' : isPending ? '#FF9800' : '#999' }]}>
                    {isVerified ? '✓ Verified' : isPending ? '⏳ Under Review' : 'Not uploaded'}
                  </Text>
                </View>
                <ChevronRight size={16} color="#DDD" />
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Achievements */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Achievements</Text>
          <View style={styles.badgesRow}>
            {ACHIEVEMENTS.map((a, i) => (
              <View key={i} style={[styles.badgeItem, !a.earned && styles.badgeLocked]}>
                <Text style={{ fontSize: 24 }}>{a.emoji}</Text>
                <Text style={[styles.badgeLabel, !a.earned && { color: '#CCC' }]}>{a.label}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Settings Menu */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Settings</Text>
          <MenuItem icon={<Settings size={20} color={theme.colors.sky} />} label="Account Settings" sub="Name, phone, password" />
          <MenuItem icon={<Bell size={20} color="#FF9800" />} label="Notifications" sub="Push, SMS, email" />
          <MenuItem icon={<Shield size={20} color="#4CAF50" />} label="Privacy & Security" sub="Data, permissions" />
          <MenuItem icon={<HelpCircle size={20} color="#9C27B0" />} label="Help & Support" sub="FAQ, contact us" />
        </View>

        {/* Sign Out */}
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <LogOut size={18} color="#D32F2F" />
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>
        <Text style={styles.version}>ZimAgriTrust Driver v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function MenuItem({ icon, label, sub, onPress }) {
  return (
    <TouchableOpacity style={styles.menuItem} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.menuLeft}>
        <View style={styles.menuIcon}>{icon}</View>
        <View>
          <Text style={styles.menuLabel}>{label}</Text>
          {sub && <Text style={styles.menuSub}>{sub}</Text>}
        </View>
      </View>
      <ChevronRight size={18} color="#DDD" />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  header: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 },
  headerTitle: { fontSize: 28, fontWeight: '900', color: theme.colors.dark },

  heroCard: { marginHorizontal: 20, backgroundColor: '#FFF', borderRadius: 24, padding: 20, ...theme.shadows.sm, borderWidth: 1, borderColor: '#F0F0F0' },
  heroTop: { marginBottom: 16 },
  avatarSection: { flexDirection: 'row', alignItems: 'center' },
  avatar: { width: 72, height: 72, borderRadius: 36, backgroundColor: 'rgba(41,182,246,0.1)', justifyContent: 'center', alignItems: 'center', borderWidth: 3, borderColor: 'rgba(41,182,246,0.2)' },
  name: { fontSize: 20, fontWeight: '900', color: theme.colors.dark },
  roleBadge: { backgroundColor: '#E8F5E9', alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8, marginTop: 4 },
  roleText: { fontSize: 10, fontWeight: '800', color: '#4CAF50', letterSpacing: 1 },
  phoneRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  phoneText: { fontSize: 13, color: '#999', fontWeight: '500' },
  statsGrid: { flexDirection: 'row', backgroundColor: '#F8F9FA', borderRadius: 16, padding: 14 },
  statBox: { flex: 1, alignItems: 'center', gap: 4 },
  statVal: { fontSize: 18, fontWeight: '900', color: theme.colors.dark },
  statLabel: { fontSize: 11, fontWeight: '600', color: '#999' },
  statDivider: { width: 1, backgroundColor: '#E8E8E8' },

  section: { marginHorizontal: 20, marginTop: 24 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: '#BBB', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 },

  completionCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF', borderRadius: 20, padding: 20, borderWidth: 1, borderColor: '#F0F0F0' },
  completionTitle: { fontSize: 16, fontWeight: '800', color: theme.colors.dark },
  completionSub: { fontSize: 12, color: '#999', marginTop: 4, lineHeight: 18 },
  completeBtn: { backgroundColor: theme.colors.sky, alignSelf: 'flex-start', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 10, marginTop: 10 },
  completeBtnText: { color: '#FFF', fontSize: 12, fontWeight: '800' },

  vehicleCard: { backgroundColor: '#FFF', borderRadius: 20, padding: 16, borderWidth: 1, borderColor: '#F0F0F0' },
  vehicleRow: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 8 },
  vIcon: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  vLabel: { fontSize: 11, color: '#999', fontWeight: '600' },
  vVal: { fontSize: 15, fontWeight: '700', color: theme.colors.dark, marginTop: 1 },
  vDivider: { height: 1, backgroundColor: '#F5F5F5', marginLeft: 50 },

  docRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF', padding: 14, borderRadius: 14, marginBottom: 8, borderWidth: 1, borderColor: '#F5F5F5' },
  docIcon: { width: 36, height: 36, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginRight: 14 },
  docLabel: { fontSize: 14, fontWeight: '700', color: theme.colors.dark },
  docStatus: { fontSize: 11, fontWeight: '600', marginTop: 2 },

  badgesRow: { flexDirection: 'row', gap: 10 },
  badgeItem: { flex: 1, alignItems: 'center', backgroundColor: '#FFF', borderRadius: 16, padding: 14, borderWidth: 1, borderColor: '#F0F0F0', gap: 6 },
  badgeLocked: { opacity: 0.4 },
  badgeLabel: { fontSize: 10, fontWeight: '700', color: theme.colors.dark, textAlign: 'center' },

  menuItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#FFF', padding: 14, borderRadius: 16, marginBottom: 8, borderWidth: 1, borderColor: '#F5F5F5' },
  menuLeft: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  menuIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: '#F8F9FA', justifyContent: 'center', alignItems: 'center' },
  menuLabel: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  menuSub: { fontSize: 11, color: '#BBB', fontWeight: '500', marginTop: 1 },

  logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, marginHorizontal: 20, marginTop: 32, paddingVertical: 16, borderRadius: 16, backgroundColor: '#FFF5F5', borderWidth: 1, borderColor: '#FFCDD2' },
  logoutText: { fontSize: 15, fontWeight: '700', color: '#D32F2F' },
  version: { textAlign: 'center', fontSize: 11, color: '#DDD', marginTop: 16, fontWeight: '600' },
});
