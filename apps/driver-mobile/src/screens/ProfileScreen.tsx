import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, Alert, Platform, Modal, ActivityIndicator, Image,
} from 'react-native';
import {
  Phone as IconPhone, MapPin as IconMapPin, Truck as IconTruck,
  Shield as IconShield, Star as IconStar, LogOut as IconLogOut,
  ChevronRight as IconChevronRight, Bell as IconBell,
  HelpCircle as IconHelpCircle, Settings as IconSettings,
  Award as IconAward, FileText as IconFileText, Camera as IconCamera,
  CheckCircle as IconCheckCircle, Clock as IconClock,
  XCircle as IconXCircle, User as IconUser, Package as IconPackage,
  Upload as IconUpload, X as IconX, Calendar as IconCalendar,
} from 'lucide-react-native';
import { theme } from '../styles';
import { getDriverProfile, updateAvailability, uploadDocument } from '../api';
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
  { key: 'license',  label: "Driver's License",    status: 'verified', icon: IconFileText, uploadDate: '2024-01-15' },
  { key: 'vehicle',  label: 'Vehicle Registration', status: 'verified', icon: IconTruck, uploadDate: '2024-01-15' },
  { key: 'insurance',label: 'Insurance Certificate',status: 'pending',  icon: IconShield, uploadDate: '2024-04-20' },
  { key: 'photo',    label: 'Profile Photo',        status: 'missing',  icon: IconCamera, uploadDate: null },
  { key: 'id_proof', label: 'National ID',         status: 'verified', icon: IconUser, uploadDate: '2024-01-10' },
];

const VERIFICATION_TIMELINE = [
  { date: '2024-01-10', event: 'Account Created', status: 'completed' },
  { date: '2024-01-10', event: 'National ID Uploaded', status: 'completed' },
  { date: '2024-01-12', event: 'ID Verified', status: 'completed' },
  { date: '2024-01-15', event: 'Driver\'s License Uploaded', status: 'completed' },
  { date: '2024-01-17', event: 'License Verified', status: 'completed' },
  { date: '2024-01-15', event: 'Vehicle Registration Uploaded', status: 'completed' },
  { date: '2024-01-18', event: 'Vehicle Verified', status: 'completed' },
  { date: '2024-04-20', event: 'Insurance Certificate Uploaded', status: 'completed' },
  { date: '2024-04-22', event: 'Insurance Under Review', status: 'pending' },
];

const ACHIEVEMENTS = [
  { label: '100 Deliveries', icon: IconAward,       earned: true },
  { label: 'On-Time Pro',    icon: IconCheckCircle, earned: true },
  { label: '5-Star Rating',  icon: IconStar,        earned: false },
  { label: 'Night Shift',    icon: IconTruck,       earned: false },
];

export default function ProfileScreen({ route, navigation, onLogout: onLogoutProp }) {
  const { token, profile: initialProfile = {}, onLogout: onLogoutParam } = route.params || {};
  const onLogout = onLogoutProp || onLogoutParam;
  const [profile, setProfile] = useState(initialProfile);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [uploading, setUploading] = useState(false);

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

  const handleUploadDocument = (doc) => {
    setSelectedDoc(doc);
    setShowUploadModal(true);
  };

  const handleConfirmUpload = async () => {
    if (!selectedDoc) return;
    setUploading(true);
    try {
      // Simulate document upload
      await new Promise(resolve => setTimeout(resolve, 1500));
      Alert.alert('Success', `${selectedDoc.label} uploaded successfully. It will be reviewed shortly.`);
      setShowUploadModal(false);
      setSelectedDoc(null);
    } catch (err) {
      Alert.alert('Upload Failed', err.message || 'Could not upload document. Please try again.');
    } finally {
      setUploading(false);
    }
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
              <Image source={require('../../assets/logo.png')} style={{ width: 32, height: 32, resizeMode: 'contain' }} />
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
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle}>Documents</Text>
            <TouchableOpacity onPress={() => {}}>
              <Text style={styles.seeAllText}>View All</Text>
            </TouchableOpacity>
          </View>
          {DOCUMENTS.map((doc, idx) => {
            const Icon = doc.icon;
            const st = DOC_STATUS[doc.status];
            const StatusIcon = st.icon;
            return (
              <TouchableOpacity
                key={doc.key + idx}
                style={styles.docRow}
                activeOpacity={0.75}
                onPress={() => doc.status === 'missing' && handleUploadDocument(doc)}
              >
                <View style={[styles.docIcon, { backgroundColor: st.bg }]}>
                  <Icon size={16} color={st.color} />
                </View>
                <View style={styles.docInfo}>
                  <Text style={styles.docLabel}>{doc.label}</Text>
                  <View style={styles.docStatusRow}>
                    <StatusIcon size={11} color={st.color} />
                    <Text style={[styles.docStatus, { color: st.color }]}>{st.label}</Text>
                  </View>
                  {doc.uploadDate && (
                    <Text style={styles.uploadDate}>Uploaded: {doc.uploadDate}</Text>
                  )}
                </View>
                {doc.status === 'missing' ? (
                  <View style={styles.uploadBadge}>
                    <IconUpload size={14} color={theme.colors.sky} />
                  </View>
                ) : (
                  <IconChevronRight size={16} color="#DDD" />
                )}
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Verification Timeline */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Verification Timeline</Text>
          <View style={styles.timelineCard}>
            {VERIFICATION_TIMELINE.map((item, index) => (
              <View key={index} style={styles.timelineItem}>
                <View style={styles.timelineLeft}>
                  <View style={[
                    styles.timelineDot,
                    item.status === 'completed' ? styles.timelineDotComplete : styles.timelineDotPending,
                  ]}>
                    {item.status === 'completed' && <IconCheckCircle size={10} color="#FFF" />}
                    {item.status === 'pending' && <IconClock size={10} color="#F59E0B" />}
                  </View>
                  {index < VERIFICATION_TIMELINE.length - 1 && (
                    <View style={styles.timelineLine} />
                  )}
                </View>
                <View style={styles.timelineContent}>
                  <Text style={styles.timelineEvent}>{item.event}</Text>
                  <Text style={styles.timelineDate}>{item.date}</Text>
                </View>
              </View>
            ))}
          </View>
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

        {/* Settings Menu */}
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

      {/* Document Upload Modal */}
      <Modal visible={showUploadModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Upload Document</Text>
            <TouchableOpacity onPress={() => setShowUploadModal(false)} style={styles.modalCloseBtn}>
              <IconX size={20} color="#666" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.docPreview}>
              <View style={styles.docPreviewIcon}>
                {selectedDoc && <selectedDoc.icon size={32} color={theme.colors.sky} />}
              </View>
              <Text style={styles.docPreviewLabel}>{selectedDoc?.label}</Text>
              <Text style={styles.docPreviewSub}>Upload a clear photo or scan of your document</Text>
            </View>

            <TouchableOpacity style={styles.uploadArea} activeOpacity={0.8}>
              <IconCamera size={40} color="#CCC" />
              <Text style={styles.uploadAreaText}>Tap to take a photo</Text>
              <Text style={styles.uploadAreaSub}>or drag and drop a file</Text>
            </TouchableOpacity>

            <View style={styles.uploadTips}>
              <Text style={styles.tipsTitle}>Upload Tips</Text>
              <Text style={styles.tipsText}>• Ensure all text is clearly visible</Text>
              <Text style={styles.tipsText}>• Use good lighting</Text>
              <Text style={styles.tipsText}>• Avoid glare and shadows</Text>
              <Text style={styles.tipsText}>• File size should be under 5MB</Text>
            </View>
          </ScrollView>

          <View style={styles.modalFooter}>
            <TouchableOpacity
              style={[styles.uploadBtn, uploading && styles.uploadBtnDisabled]}
              onPress={handleConfirmUpload}
              disabled={uploading}
            >
              {uploading ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <>
                  <IconUpload size={18} color="#FFF" />
                  <Text style={styles.uploadBtnText}>Upload Document</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
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
  container: { flex: 1, backgroundColor: theme.colors.gray50 },
  scrollContent: { paddingBottom: 120 },

  header: { paddingHorizontal: 20, paddingTop: 20, paddingBottom: 10 },
  headerTitle: { fontSize: 30, fontWeight: '900', color: theme.colors.ink, letterSpacing: -0.8 },

  heroCard: {
    marginHorizontal: 20, backgroundColor: '#FFF', borderRadius: 28,
    padding: 22, shadowColor: '#0F172A', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.08, shadowRadius: 18, elevation: 4,
    borderWidth: 1, borderColor: '#E2E8F0',
  },
  avatarRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  avatar: {
    width: 72, height: 72, borderRadius: 36,
    backgroundColor: '#E1F5FE', justifyContent: 'center', alignItems: 'center',
    borderWidth: 3, borderColor: 'rgba(41,182,246,0.2)',
  },
  avatarInfo: { flex: 1, marginLeft: 16 },
  name: { fontSize: 22, fontWeight: '900', color: theme.colors.ink, letterSpacing: -0.4 },
  roleBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#F0FDF4', alignSelf: 'flex-start',
    paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8, marginTop: 4,
  },
  roleText: { fontSize: 10, fontWeight: '800', color: '#4CAF50', letterSpacing: 0.5 },
  phoneRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  phoneText: { fontSize: 13, color: '#64748B', fontWeight: '600' },

  statsGrid: { flexDirection: 'row', backgroundColor: '#F8FAFC', borderRadius: 20, padding: 16, borderWidth: 1, borderColor: '#E2E8F0' },
  statBox: { flex: 1, alignItems: 'center', gap: 4 },
  statVal: { fontSize: 18, fontWeight: '900', color: theme.colors.ink },
  statLabel: { fontSize: 11, fontWeight: '700', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: 0.4 },
  statDivider: { width: 1, backgroundColor: '#E2E8F0' },

  section: { marginHorizontal: 20, marginTop: 24 },
  sectionHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  sectionTitle: { fontSize: 12, fontWeight: '900', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: 1 },
  seeAllText: { fontSize: 13, fontWeight: '700', color: theme.colors.sky },

  completionCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    borderRadius: 24, padding: 22, borderWidth: 1, borderColor: '#E2E8F0', ...theme.shadows.sm,
  },
  completionText: { flex: 1, marginLeft: 20 },
  completionHeading: { fontSize: 16, fontWeight: '900', color: theme.colors.ink },
  completionSub: { fontSize: 12, color: '#64748B', marginTop: 4, lineHeight: 18 },
  completeBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: theme.colors.sky, alignSelf: 'flex-start',
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 10, marginTop: 10,
  },
  completeBtnText: { color: '#FFF', fontSize: 12, fontWeight: '800' },

  vehicleCard: { backgroundColor: '#FFF', borderRadius: 24, padding: 18, borderWidth: 1, borderColor: '#E2E8F0', ...theme.shadows.sm },
  vehicleRow: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 8 },
  vIcon: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  vLabel: { fontSize: 11, color: '#94A3B8', fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.4 },
  vVal: { fontSize: 15, fontWeight: '800', color: theme.colors.ink, marginTop: 1 },
  vDivider: { height: 1, backgroundColor: '#EEF2F7', marginLeft: 50 },

  docRow: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF',
    padding: 15, borderRadius: 18, marginBottom: 10, borderWidth: 1, borderColor: '#E2E8F0', ...theme.shadows.xs,
  },
  docIcon: { width: 36, height: 36, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginRight: 14 },
  docInfo: { flex: 1 },
  docLabel: { fontSize: 14, fontWeight: '800', color: theme.colors.ink },
  docStatusRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 3 },
  docStatus: { fontSize: 11, fontWeight: '600' },
  uploadDate: { fontSize: 10, color: '#94A3B8', marginTop: 2 },
  uploadBadge: {
    width: 32, height: 32, borderRadius: 16, backgroundColor: '#F0F9FF',
    justifyContent: 'center', alignItems: 'center',
  },

  timelineCard: {
    backgroundColor: '#FFF', borderRadius: 24, padding: 22,
    borderWidth: 1, borderColor: '#E2E8F0', ...theme.shadows.sm,
  },
  timelineItem: { flexDirection: 'row', marginBottom: 16 },
  timelineLeft: { alignItems: 'center', width: 24, marginRight: 12 },
  timelineDot: {
    width: 20, height: 20, borderRadius: 10, justifyContent: 'center', alignItems: 'center',
  },
  timelineDotComplete: { backgroundColor: '#4CAF50' },
  timelineDotPending: { backgroundColor: '#FFFBEB', borderWidth: 2, borderColor: '#F59E0B' },
  timelineLine: { width: 2, flex: 1, backgroundColor: '#DCE6F2', marginTop: 4 },
  timelineContent: { flex: 1, paddingBottom: 16 },
  timelineEvent: { fontSize: 14, fontWeight: '800', color: theme.colors.ink },
  timelineDate: { fontSize: 11, color: '#94A3B8', marginTop: 2 },

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

  // Modal styles
  modalContainer: { flex: 1, backgroundColor: '#FFF' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20, borderBottomWidth: 1, borderBottomColor: '#F0F0F0' },
  modalTitle: { fontSize: 18, fontWeight: '700', color: theme.colors.dark },
  modalCloseBtn: { padding: 8 },
  modalContent: { flex: 1, padding: 20 },
  modalFooter: { padding: 20, borderTopWidth: 1, borderTopColor: '#F0F0F0' },
  docPreview: { alignItems: 'center', marginBottom: 24 },
  docPreviewIcon: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#F0F9FF', justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  docPreviewLabel: { fontSize: 18, fontWeight: '700', color: theme.colors.dark },
  docPreviewSub: { fontSize: 13, color: '#999', marginTop: 4 },
  uploadArea: {
    borderWidth: 2, borderColor: '#E0E0E0', borderStyle: 'dashed', borderRadius: 16,
    padding: 32, alignItems: 'center', backgroundColor: '#F9FAFB', marginBottom: 24,
  },
  uploadAreaText: { fontSize: 14, fontWeight: '600', color: theme.colors.dark, marginTop: 12 },
  uploadAreaSub: { fontSize: 12, color: '#999', marginTop: 4 },
  uploadTips: { backgroundColor: '#F8F9FA', borderRadius: 16, padding: 16 },
  tipsTitle: { fontSize: 14, fontWeight: '700', color: theme.colors.dark, marginBottom: 12 },
  tipsText: { fontSize: 12, color: '#666', marginBottom: 6 },
  uploadBtn: { backgroundColor: theme.colors.sky, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14, borderRadius: 12 },
  uploadBtnDisabled: { backgroundColor: '#CCC' },
  uploadBtnText: { color: '#FFF', fontSize: 15, fontWeight: '600' },
});
