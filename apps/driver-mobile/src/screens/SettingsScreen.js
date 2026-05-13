import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, Switch, TouchableOpacity,
  ScrollView, SafeAreaView, ActivityIndicator, Alert,
} from 'react-native';
import {
  Bell as IconBell, Smartphone as IconSmartphone, Mail as IconMail, 
  Shield as IconShield, HelpCircle as IconHelpCircle,
  ChevronRight as IconChevronRight, Lock as IconLock, 
  Eye as IconEye, Trash2 as IconTrash2, Download as IconDownload,
} from 'lucide-react-native';
import { theme } from '../styles';
import { getDriverSettings, updateDriverSettings } from '../api';

export default function SettingsScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    push_notifications: true,
    sms_notifications: true,
    email_notifications: false,
    job_alerts: true,
    earnings_alerts: true,
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await getDriverSettings(token);
      setSettings(data);
    } catch (err) {
      console.warn('Failed to fetch settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSetting = async (key) => {
    const newVal = !settings[key];
    setSettings({ ...settings, [key]: newVal });
    
    try {
      await updateDriverSettings(token, { [key]: newVal });
    } catch (err) {
      Alert.alert('Error', 'Failed to save setting');
      setSettings({ ...settings, [key]: !newVal }); // Revert
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
        <View style={styles.header}>
          <Text style={styles.title}>Settings</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          <View style={styles.card}>
            <SettingRow
              icon={<IconBell size={20} color={theme.colors.sky} />}
              label="Push Notifications"
              value={settings.push_notifications}
              onToggle={() => toggleSetting('push_notifications')}
            />
            <View style={styles.divider} />
            <SettingRow
              icon={<IconSmartphone size={20} color="#F59E0B" />}
              label="SMS Alerts"
              value={settings.sms_notifications}
              onToggle={() => toggleSetting('sms_notifications')}
            />
            <View style={styles.divider} />
            <SettingRow
              icon={<IconMail size={20} color="#10B981" />}
              label="Email Reports"
              value={settings.email_notifications}
              onToggle={() => toggleSetting('email_notifications')}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Job Alerts</Text>
          <View style={styles.card}>
            <SettingRow
              label="New Available Jobs"
              value={settings.job_alerts}
              onToggle={() => toggleSetting('job_alerts')}
            />
            <View style={styles.divider} />
            <SettingRow
              label="Earnings Notifications"
              value={settings.earnings_alerts}
              onToggle={() => toggleSetting('earnings_alerts')}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account & Security</Text>
          <View style={styles.card}>
            <MenuRow
              icon={<IconLock size={20} color="#6366F1" />}
              label="Change PIN"
              onPress={() => navigation.navigate('ChangePin', { token })}
            />
            <View style={styles.divider} />
            <MenuRow
              icon={<IconEye size={20} color="#EC4899" />}
              label="Privacy Settings"
              onPress={() => navigation.navigate('Privacy', { token })}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Support</Text>
          <View style={styles.card}>
            <MenuRow
              icon={<IconHelpCircle size={20} color="#8B5CF6" />}
              label="Help Center"
              onPress={() => navigation.navigate('Support')}
            />
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.version}>ZimAgriTrust Driver v1.0.0</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function SettingRow({ icon, label, value, onToggle }) {
  return (
    <View style={styles.row}>
      <View style={styles.rowLeft}>
        {icon && <View style={styles.iconBox}>{icon}</View>}
        <Text style={styles.rowLabel}>{label}</Text>
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

function MenuRow({ icon, label, onPress }) {
  return (
    <TouchableOpacity style={styles.row} onPress={onPress}>
      <View style={styles.rowLeft}>
        {icon && <View style={styles.iconBox}>{icon}</View>}
        <Text style={styles.rowLabel}>{label}</Text>
      </View>
      <IconChevronRight size={18} color="#CCC" />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: 20, paddingBottom: 100 },
  header: { marginBottom: 24 },
  title: { fontSize: 24, fontWeight: '900', color: theme.colors.dark },

  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 13, fontWeight: '800', color: '#BBB', textTransform: 'uppercase', marginBottom: 12, marginLeft: 4 },
  card: { backgroundColor: '#FFF', borderRadius: 20, paddingHorizontal: 16, borderWidth: 1, borderColor: '#F0F0F0' },
  
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 16 },
  rowLeft: { flexDirection: 'row', alignItems: 'center' },
  iconBox: { width: 36, height: 36, borderRadius: 10, backgroundColor: '#F8F9FA', justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  rowLabel: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  
  divider: { height: 1, backgroundColor: '#F8F9FA' },
  
  footer: { marginTop: 20, alignItems: 'center' },
  version: { fontSize: 12, color: '#DDD', fontWeight: '600' },
});
