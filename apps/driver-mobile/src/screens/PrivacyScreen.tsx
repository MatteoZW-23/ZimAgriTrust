import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, Switch, TouchableOpacity,
  ScrollView, SafeAreaView, ActivityIndicator, Alert, Platform, Share,
} from 'react-native';
import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';
import { 
  Shield as IconShield, Eye as IconEye, MapPin as IconMapPin, 
  Phone as IconPhone, Trash2 as IconTrash2, Download as IconDownload, 
  Info as IconInfo, ChevronRight as IconChevronRight
} from 'lucide-react-native';
import { theme } from '../styles';
import { getDriverSettings, updatePrivacySettings, deleteDriverData, exportDriverData } from '../api';

export default function PrivacyScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState({
    share_location_delivery: true,
    phone_visibility: true,
    data_sharing_consent: true,
  });

  useEffect(() => {
    fetchPrivacy();
  }, []);

  const fetchPrivacy = async () => {
    try {
      const data = await getDriverSettings(token);
      setSettings({
        share_location_delivery: data.share_location_delivery,
        phone_visibility: data.phone_visibility,
        data_sharing_consent: data.data_sharing_consent,
      });
    } catch (err) {
      console.warn('Failed to fetch privacy settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSetting = async (key) => {
    const newVal = !settings[key];
    setSettings({ ...settings, [key]: newVal });
    
    try {
      await updatePrivacySettings(token, { [key]: newVal });
    } catch (err) {
      Alert.alert('Error', 'Failed to update privacy settings');
      setSettings({ ...settings, [key]: !newVal }); // Revert
    }
  };

  const handleDeleteData = () => {
    Alert.alert(
      'Delete My Data',
      'Are you sure you want to delete your personal data? This action will disable your account and cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteDriverData(token);
              Alert.alert('Request Received', 'Your data deletion request is being processed. You will be logged out.');
              // In real app, trigger logout
            } catch (err) {
              Alert.alert('Error', 'Failed to submit deletion request');
            }
          }
        }
      ]
    );
  };

  const handleRequestDataArchive = async () => {
    try {
      const data = await exportDriverData(token);
      const text = JSON.stringify(data, null, 2);
      if (Platform.OS === 'web') {
        const blob = new Blob([text], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'zimagritrust-driver-data.json';
        a.click();
        URL.revokeObjectURL(url);
        return;
      }
      await Share.share({ title: 'ZimAgriTrust driver data export', message: text });
    } catch (err) {
      Alert.alert('Export failed', 'Could not prepare your data archive. Please try again.');
    }
  };

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={theme.colors.sky} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <Animated.View entering={FadeInDown.duration(600).springify()} style={styles.header}>
          <View style={styles.headerIconWrap}>
            <IconShield size={32} color={theme.colors.sky} />
          </View>
          <Text style={styles.title}>Privacy & Data</Text>
          <Text style={styles.subtitle}>Control your digital footprint</Text>
        </Animated.View>

        <Animated.View entering={FadeInUp.duration(600).delay(100).springify()} style={styles.section}>
          <Text style={styles.sectionTitle}>Preferences</Text>
          <View style={styles.card}>
            <PrivacyRow
              icon={<IconMapPin size={22} color="#0EA5E9" />}
              iconBg="#E0F2FE"
              label="Real-time Location"
              description="Share location during deliveries"
              value={settings.share_location_delivery}
              onToggle={() => toggleSetting('share_location_delivery')}
            />
            <View style={styles.divider} />
            <PrivacyRow
              icon={<IconPhone size={22} color="#F59E0B" />}
              iconBg="#FEF3C7"
              label="Phone Visibility"
              description="Allow customers to call you"
              value={settings.phone_visibility}
              onToggle={() => toggleSetting('phone_visibility')}
            />
            <View style={styles.divider} />
            <PrivacyRow
              icon={<IconEye size={22} color="#10B981" />}
              iconBg="#D1FAE5"
              label="Analytics & Data"
              description="Share data to improve the app"
              value={settings.data_sharing_consent}
              onToggle={() => toggleSetting('data_sharing_consent')}
            />
          </View>
        </Animated.View>

        <Animated.View entering={FadeInUp.duration(600).delay(200).springify()} style={styles.infoBox}>
          <View style={styles.infoIcon}>
            <IconInfo size={20} color="#0EA5E9" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.infoTitle}>Secure by Design</Text>
            <Text style={styles.infoText}>
              Your documents are encrypted and only accessible by verified administrators.
            </Text>
          </View>
        </Animated.View>

        <Animated.View entering={FadeInUp.duration(600).delay(300).springify()} style={styles.section}>
          <Text style={styles.sectionTitle}>Account Data</Text>
          <View style={styles.card}>
            <TouchableOpacity style={styles.menuItem} onPress={handleRequestDataArchive} activeOpacity={0.7}>
              <View style={styles.menuLeft}>
                <View style={[styles.menuIconWrap, { backgroundColor: '#F3F4F6' }]}>
                  <IconDownload size={20} color="#4B5563" />
                </View>
                <Text style={styles.menuLabel}>Request Data Archive</Text>
              </View>
              <IconChevronRight size={18} color="#D1D5DB" />
            </TouchableOpacity>
            <View style={styles.divider} />
            <TouchableOpacity style={styles.menuItem} onPress={handleDeleteData} activeOpacity={0.7}>
              <View style={styles.menuLeft}>
                <View style={[styles.menuIconWrap, { backgroundColor: '#FEE2E2' }]}>
                  <IconTrash2 size={20} color="#EF4444" />
                </View>
                <Text style={[styles.menuLabel, { color: '#EF4444' }]}>Delete Account & Data</Text>
              </View>
              <IconChevronRight size={18} color="#D1D5DB" />
            </TouchableOpacity>
          </View>
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}

function PrivacyRow({ icon, iconBg, label, description, value, onToggle }) {
  return (
    <View style={styles.row}>
      <View style={styles.rowLeft}>
        <View style={[styles.iconBox, { backgroundColor: iconBg }]}>{icon}</View>
        <View style={{ flex: 1, paddingRight: 16 }}>
          <Text style={styles.rowLabel}>{label}</Text>
          <Text style={styles.rowDesc}>{description}</Text>
        </View>
      </View>
      <Switch
        value={value}
        onValueChange={onToggle}
        trackColor={{ false: '#E5E7EB', true: theme.colors.sky }}
        thumbColor="#FFFFFF"
        ios_backgroundColor="#E5E7EB"
        style={{ transform: [{ scale: 0.9 }] }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.gray50 },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: 24, paddingBottom: 60 },
  
  header: { marginBottom: 40, alignItems: 'center', paddingTop: 10 },
  headerIconWrap: { 
    width: 72, height: 72, borderRadius: 36, backgroundColor: '#E0F2FE', 
    justifyContent: 'center', alignItems: 'center', marginBottom: 16,
    shadowColor: '#0EA5E9', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.15, shadowRadius: 12, elevation: 8
  },
  title: { fontSize: 30, fontWeight: '900', color: '#111827', letterSpacing: -0.7 },
  subtitle: { fontSize: 15, color: '#6B7280', marginTop: 6, fontWeight: '600' },

  section: { marginBottom: 32 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 12, marginLeft: 8 },
  
  card: { 
    backgroundColor: '#FFFFFF', borderRadius: 26, paddingHorizontal: 20,
    shadowColor: '#0F172A', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.06, shadowRadius: 18, elevation: 4,
    borderWidth: 1, borderColor: '#E2E8F0'
  },
  
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 20 },
  rowLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  iconBox: { width: 44, height: 44, borderRadius: 14, justifyContent: 'center', alignItems: 'center', marginRight: 16 },
  rowLabel: { fontSize: 16, fontWeight: '800', color: '#111827', marginBottom: 3 },
  rowDesc: { fontSize: 13, color: '#6B7280', lineHeight: 18 },
  
  divider: { height: 1, backgroundColor: '#EEF2F7', marginLeft: 60 },

  infoBox: {
    flexDirection: 'row', backgroundColor: '#F0F9FF', padding: 20, borderRadius: 20, 
    marginBottom: 32, gap: 16, alignItems: 'center', borderWidth: 1, borderColor: '#BAE6FD'
  },
  infoIcon: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#FFFFFF', justifyContent: 'center', alignItems: 'center', shadowColor: '#0EA5E9', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 1 },
  infoTitle: { fontSize: 15, fontWeight: '700', color: '#0369A1', marginBottom: 4 },
  infoText: { fontSize: 13, color: '#0284C7', lineHeight: 20, fontWeight: '500' },

  menuItem: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 20 },
  menuLeft: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  menuIconWrap: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  menuLabel: { fontSize: 16, fontWeight: '700', color: '#111827' },
});
