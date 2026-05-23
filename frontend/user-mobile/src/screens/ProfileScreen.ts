import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, SafeAreaView, Alert, Platform, Share, Image } from 'react-native';
import {
  User as IconUser, MapPin as IconMapPin, Phone as IconPhone,
  Shield as IconShield, Star as IconStar, LogOut as IconLogOut,
  ChevronRight as IconChevronRight, Bell as IconBell,
  HelpCircle as IconHelpCircle, FileText as IconFileText,
  Settings as IconSettings, Briefcase as IconBriefcase,
  Download as IconDownload, Trash2 as IconTrash2,
  PowerOff as IconPowerOff, ShoppingCart as IconShopping,
  Sprout as IconSprout, CheckCircle, Clock, TrendingUp, Award
} from 'lucide-react-native';
import { theme } from '../styles';
import { deactivateAccount, deleteAccount, exportPersonalData, getProfile } from '../api';
import { clearSession } from '../utils/auth';

export default function ProfileScreen({ route, navigation }) {
  const { role = 'farmer', token, profile: initialProfile = {}, onLogout } = route.params || {};
  const [profile, setProfile] = useState(initialProfile);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      setLoading(true);
      getProfile(token)
        .then(data => setProfile(data))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [token]);

  const handleLogout = () => {
    if (Platform.OS === 'web') {
      clearSession().then(() => {
        if (onLogout) onLogout();
      });
      return;
    }
    Alert.alert('Logout', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await clearSession();
          if (onLogout) onLogout();
        },
      },
    ]);
  };

  const handleExportData = async () => {
    try {
      const data = await exportPersonalData(token);
      const text = JSON.stringify(data, null, 2);
      if (Platform.OS === 'web') {
        const blob = new Blob([text], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'zimagritrust-personal-data.json';
        a.click();
        URL.revokeObjectURL(url);
        return;
      }
      await Share.share({ title: 'ZimAgriTrust Personal Data', message: text });
    } catch (err) {
      Alert.alert('Export failed', err.message || 'Could not export your data.');
    }
  };

  const handleDeactivateAccount = () => {
    Alert.alert('Deactivate account', 'Your account will be disabled and you will be signed out. You can contact support to reactivate it.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Deactivate',
        style: 'destructive',
        onPress: async () => {
          try {
            await deactivateAccount(token);
            await clearSession();
            if (onLogout) onLogout();
          } catch (err) {
            Alert.alert('Deactivate failed', err.message || 'Could not deactivate your account.');
          }
        },
      },
    ]);
  };

  const handleDeleteAccount = () => {
    Alert.alert('Delete account permanently?', 'This will anonymize your personal details and close your account. This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteAccount(token);
            await clearSession();
            if (onLogout) onLogout();
          } catch (err) {
            Alert.alert('Delete failed', err.message || 'Could not delete your account.');
          }
        },
      },
    ]);
  };

  const handleEditProfile = () => {
    navigation.navigate('EditProfile', {
      token,
      profile,
      onProfileUpdated: setProfile,
    });
  };

  const trustScore = profile.trust_score || 50;
  const trustColor = trustScore >= 80 ? '#4CAF50' : trustScore >= 50 ? '#FFC107' : '#D32F2F';
  const trustLabel = trustScore >= 80 ? 'Excellent' : trustScore >= 50 ? 'Good' : 'Needs Improvement';
  const accent = role === 'farmer' ? theme.colors.green : theme.colors.sky;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Profile</Text>
        </View>

        {/* Profile Card */}
        <View style={styles.profileCard}>
          <View style={[styles.avatar, { backgroundColor: `${accent}15`, borderColor: `${accent}30` }]}>
            <Image source={require('../../assets/logo.png')} style={{ width: 40, height: 40, resizeMode: 'contain' }} />
          </View>
          <Text style={styles.name}>{profile.full_name || profile.name || 'User'}</Text>
          <Text style={styles.roleLabel}>{(role || 'user').charAt(0).toUpperCase() + (role || 'user').slice(1)}</Text>

          <View style={styles.infoRow}>
            <IconPhone size={14} color="#999" />
            <Text style={styles.infoText}>{profile.phone_number || '+263...'}</Text>
          </View>
          {profile.location && (
            <View style={styles.infoRow}>
              <IconMapPin size={14} color="#999" />
              <Text style={styles.infoText}>{profile.location}</Text>
            </View>
          )}

          {/* Verification Badges */}
          <View style={styles.verificationBadges}>
            <VerificationBadge icon={<CheckCircle size={14} color="#4CAF50" />} label="ID Verified" verified={profile.id_verified} />
            <VerificationBadge icon={<IconPhone size={14} color="#4CAF50" />} label="Phone Verified" verified={profile.phone_verified} />
            <VerificationBadge icon={<IconShield size={14} color="#4CAF50" />} label="Email Verified" verified={profile.email_verified} />
          </View>
        </View>

        {/* Trust Score */}
        <View style={styles.trustCard}>
          <View style={styles.trustHeader}>
            <View>
              <Text style={styles.trustLabel}>Trust Score</Text>
              <Text style={[styles.trustValue, { color: trustColor }]}>{trustScore}/100</Text>
            </View>
            <View style={[styles.trustBadge, { backgroundColor: `${trustColor}15` }]}>
              <IconStar size={18} color={trustColor} />
              <Text style={[styles.trustBadgeText, { color: trustColor }]}>{trustLabel}</Text>
            </View>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${trustScore}%`, backgroundColor: trustColor }]} />
          </View>
        </View>

        {/* Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{profile.listing_count || 0}</Text>
            <Text style={styles.statLabel}>Listings</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{profile.completed_orders || 0}</Text>
            <Text style={styles.statLabel}>Completed</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>${profile.total_sales || 0}</Text>
            <Text style={styles.statLabel}>Sales</Text>
          </View>
        </View>

        {/* Additional Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <TrendingUp size={20} color={accent} style={{ marginBottom: 8 }} />
            <Text style={styles.statValue}>{profile.offers_made || 0}</Text>
            <Text style={styles.statLabel}>Offers Made</Text>
          </View>
          <View style={styles.statCard}>
            <Clock size={20} color={accent} style={{ marginBottom: 8 }} />
            <Text style={styles.statValue}>{profile.offers_received || 0}</Text>
            <Text style={styles.statLabel}>Offers Received</Text>
          </View>
          <View style={styles.statCard}>
            <Award size={20} color={accent} style={{ marginBottom: 8 }} />
            <Text style={styles.statValue}>{profile.response_rate || 0}%</Text>
            <Text style={styles.statLabel}>Response Rate</Text>
          </View>
        </View>

        {/* Menu Items */}
        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Account</Text>
          <MenuItem icon={<IconSettings size={20} color={accent} />} label="Account Settings" onPress={handleEditProfile} />
          <MenuItem icon={<IconShield size={20} color={accent} />} label="Change PIN" onPress={() => navigation.navigate('ChangePin', { token })} />
          <MenuItem icon={<IconBell size={20} color={accent} />} label="Notifications & Language" onPress={() => navigation.navigate('Settings', { token })} />
          <MenuItem icon={<IconShield size={20} color={accent} />} label="Verification" onPress={() => navigation.navigate('Verification', { token })} />
          <MenuItem icon={<IconDownload size={20} color={accent} />} label="Export My Data" onPress={handleExportData} />
          <MenuItem icon={<IconFileText size={20} color={accent} />} label="My Disputes" onPress={() => navigation.navigate('Disputes', { token })} />
          {role !== 'agent' && (
            <MenuItem
              icon={<IconBriefcase size={20} color={accent} />}
              label="Become an Agent"
              onPress={() => navigation.navigate('AgentApplication', { profile })}
            />
          )}
        </View>

        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Support</Text>
          <MenuItem icon={<IconHelpCircle size={20} color={accent} />} label="Help Center" onPress={() => navigation.navigate('Support')} />
          <MenuItem icon={<IconFileText size={20} color={accent} />} label="Terms & Privacy" onPress={() => navigation.navigate('Privacy', { token, onLogout })} />
        </View>

        <View style={styles.menuSection}>
          <Text style={styles.sectionTitle}>Data & Account Control</Text>
          <MenuItem icon={<IconPowerOff size={20} color="#D97706" />} label="Deactivate Account" onPress={handleDeactivateAccount} />
          <MenuItem icon={<IconTrash2 size={20} color="#D32F2F" />} label="Delete My Account" onPress={handleDeleteAccount} />
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <IconLogOut size={20} color="#D32F2F" />
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>

        <Text style={styles.version}>ZimAgriTrust v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function MenuItem({ icon, label, onPress }) {
  return (
    <TouchableOpacity style={styles.menuItem} onPress={onPress}>
      <View style={styles.menuItemLeft}>
        {icon}
        <Text style={styles.menuItemLabel}>{label}</Text>
      </View>
      <IconChevronRight size={18} color="#CCC" />
    </TouchableOpacity>
  );
}

function VerificationBadge({ icon, label, verified }) {
  return (
    <View style={[styles.verificationBadge, { backgroundColor: verified ? '#E8F5E9' : '#F5F5F5' }]}>
      {icon}
      <Text style={[styles.verificationBadgeText, { color: verified ? '#4CAF50' : '#999' }]}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: { padding: 24, paddingTop: 16 },
  headerTitle: { fontSize: 28, fontWeight: '800', color: theme.colors.black },
  profileCard: {
    marginHorizontal: 20,
    backgroundColor: '#FFF',
    borderRadius: 24,
    padding: 28,
    alignItems: 'center',
    ...theme.shadows.sm,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    marginBottom: 16,
  },
  name: { fontSize: 22, fontWeight: '800', color: theme.colors.black },
  roleLabel: { fontSize: 14, color: '#999', fontWeight: '600', marginTop: 4, textTransform: 'uppercase', letterSpacing: 1 },
  infoRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 12 },
  infoText: { fontSize: 14, color: '#666', fontWeight: '500' },
  verificationBadges: { flexDirection: 'row', gap: 8, marginTop: 16, flexWrap: 'wrap', justifyContent: 'center' },
  verificationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  verificationBadgeText: { fontSize: 11, fontWeight: '700' },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    marginTop: 16,
  },
  badgeText: { fontSize: 13, fontWeight: '700' },
  trustCard: {
    marginHorizontal: 20,
    marginTop: 16,
    backgroundColor: '#FFF',
    borderRadius: 20,
    padding: 20,
    ...theme.shadows.xs,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  trustHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  trustLabel: { fontSize: 13, color: '#999', fontWeight: '700', textTransform: 'uppercase' },
  trustValue: { fontSize: 28, fontWeight: '900', marginTop: 4 },
  trustBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  trustBadgeText: { fontSize: 13, fontWeight: '700' },
  progressBar: { height: 8, backgroundColor: '#F0F0F0', borderRadius: 4, marginTop: 16, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 4 },
  statsRow: { flexDirection: 'row', marginHorizontal: 20, marginTop: 16, gap: 12 },
  statCard: {
    flex: 1,
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    ...theme.shadows.xs,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  statValue: { fontSize: 20, fontWeight: '900', color: theme.colors.black },
  statLabel: { fontSize: 12, color: '#999', fontWeight: '600', marginTop: 4 },
  menuSection: { marginHorizontal: 20, marginTop: 24 },
  sectionTitle: { fontSize: 14, fontWeight: '800', color: '#999', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 },
  menuItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#F5F5F5',
  },
  menuItemLeft: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  menuItemLabel: { fontSize: 15, fontWeight: '600', color: theme.colors.black },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginHorizontal: 20,
    marginTop: 32,
    paddingVertical: 16,
    borderRadius: 14,
    backgroundColor: '#FFF5F5',
    borderWidth: 1,
    borderColor: '#FFCDD2',
  },
  logoutText: { fontSize: 16, fontWeight: '700', color: '#D32F2F' },
  version: { textAlign: 'center', fontSize: 12, color: '#CCC', marginTop: 20, fontWeight: '600' },
});
