import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, Switch, TouchableOpacity,
  ScrollView, SafeAreaView, ActivityIndicator, Alert,
} from 'react-native';
import { 
  Shield as IconShield, Eye as IconEye, MapPin as IconMapPin, 
  Phone as IconPhone, Trash2 as IconTrash2, Download as IconDownload, 
  Info as IconInfo 
} from 'lucide-react-native';
import { theme } from '../styles';
import { getDriverSettings, updatePrivacySettings, deleteDriverData } from '../api';

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
        <View style={styles.header}>
          <Text style={styles.title}>Privacy & Data</Text>
          <Text style={styles.subtitle}>Manage how your information is shared</Text>
        </View>

        <View style={styles.section}>
          <View style={styles.card}>
            <PrivacyRow
              icon={<IconMapPin size={20} color={theme.colors.sky} />}
              label="Real-time Location"
              description="Share location with buyers during active deliveries"
              value={settings.share_location_delivery}
              onToggle={() => toggleSetting('share_location_delivery')}
            />
            <View style={styles.divider} />
            <PrivacyRow
              icon={<IconPhone size={20} color="#F59E0B" />}
              label="Phone Visibility"
              description="Allow customers to see your phone number"
              value={settings.phone_visibility}
              onToggle={() => toggleSetting('phone_visibility')}
            />
            <View style={styles.divider} />
            <PrivacyRow
              icon={<IconEye size={20} color="#10B981" />}
              label="Analytics & Data"
              description="Share anonymized data to improve the app"
              value={settings.data_sharing_consent}
              onToggle={() => toggleSetting('data_sharing_consent')}
            />
          </View>
        </View>

        <View style={styles.infoBox}>
          <IconInfo size={16} color="#0EA5E9" />
          <Text style={styles.infoText}>
            We value your privacy. Your documents and sensitive information are only visible to authorized administrators.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Data</Text>
          <View style={styles.card}>
            <TouchableOpacity style={styles.menuItem}>
              <View style={styles.menuLeft}>
                <IconDownload size={20} color="#666" />
                <Text style={styles.menuLabel}>Download My Data</Text>
              </View>
            </TouchableOpacity>
            <View style={styles.divider} />
            <TouchableOpacity style={styles.menuItem} onPress={handleDeleteData}>
              <View style={styles.menuLeft}>
                <IconTrash2 size={20} color="#EF4444" />
                <Text style={[styles.menuLabel, { color: '#EF4444' }]}>Delete My Account & Data</Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function PrivacyRow({ icon, label, description, value, onToggle }) {
  return (
    <View style={styles.row}>
      <View style={styles.rowLeft}>
        <View style={styles.iconBox}>{icon}</View>
        <View style={{ flex: 1, paddingRight: 10 }}>
          <Text style={styles.rowLabel}>{label}</Text>
          <Text style={styles.rowDesc}>{description}</Text>
        </View>
      </View>
      <Switch
        value={value}
        onValueChange={onToggle}
        trackColor={{ false: '#E0E0E0', true: theme.colors.sky }}
        thumbColor="#FFF"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: 20 },
  
  header: { marginBottom: 32 },
  title: { fontSize: 24, fontWeight: '900', color: theme.colors.dark },
  subtitle: { fontSize: 14, color: '#666', marginTop: 4 },

  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: '#BBB', textTransform: 'uppercase', marginBottom: 12, marginLeft: 4 },
  card: { backgroundColor: '#FFF', borderRadius: 20, paddingHorizontal: 16, borderWidth: 1, borderColor: '#F0F0F0' },
  
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 16 },
  rowLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  iconBox: { width: 40, height: 40, borderRadius: 12, backgroundColor: '#F8F9FA', justifyContent: 'center', alignItems: 'center', marginRight: 16 },
  rowLabel: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  rowDesc: { fontSize: 12, color: '#999', marginTop: 2 },
  
  divider: { height: 1, backgroundColor: '#F8F9FA' },

  infoBox: {
    flexDirection: 'row', backgroundColor: '#E0F2FE', padding: 16, borderRadius: 16, marginBottom: 32, gap: 12,
  },
  infoText: { flex: 1, fontSize: 12, color: '#0369A1', lineHeight: 18, fontWeight: '500' },

  menuItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 18 },
  menuLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  menuLabel: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
});
