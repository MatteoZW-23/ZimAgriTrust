import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, Switch, TouchableOpacity,
  ScrollView, SafeAreaView, ActivityIndicator, Alert,
} from 'react-native';
import {
  Bell, Smartphone, Mail, Shield, HelpCircle,
  ChevronRight, Lock, Eye, Trash2,
} from 'lucide-react-native';
import { theme } from '../styles';
import ScreenHeader from '../components/ScreenHeader';
import { getDriverSettings, updateDriverSettings } from '../api';

export default function SettingsScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState({
    push_notifications: true,
    sms_notifications: true,
    email_notifications: false,
    job_alerts: true,
    earnings_alerts: true,
    new_job_sound: true,
  });

  useEffect(() => { fetchSettings(); }, []);

  const fetchSettings = async () => {
    try {
      const data = await getDriverSettings(token);
      if (data) setSettings(s => ({ ...s, ...data }));
    } catch { /* use defaults */ }
    finally { setLoading(false); }
  };

  const toggle = async (key) => {
    const next = !settings[key];
    setSettings(s => ({ ...s, [key]: next }));
    try {
      await updateDriverSettings(token, { [key]: next });
    } catch {
      setSettings(s => ({ ...s, [key]: !next }));
      Alert.alert('Error', 'Could not save setting. Check your connection.');
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ScreenHeader title="Settings" navigation={navigation} />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.sky} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScreenHeader title="Settings" navigation={navigation} />
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>

        {/* Notifications */}
        <SectionLabel label="Notifications" />
        <Card>
          <ToggleRow
            icon={<Bell size={20} color={theme.colors.sky} />}
            iconBg="#E1F5FE"
            label="Push Notifications"
            desc="Receive alerts on your device"
            value={settings.push_notifications}
            onToggle={() => toggle('push_notifications')}
          />
          <Divider />
          <ToggleRow
            icon={<Smartphone size={20} color="#F59E0B" />}
            iconBg="#FFFBEB"
            label="SMS Alerts"
            desc="Text messages for key events"
            value={settings.sms_notifications}
            onToggle={() => toggle('sms_notifications')}
          />
          <Divider />
          <ToggleRow
            icon={<Mail size={20} color="#10B981" />}
            iconBg="#ECFDF5"
            label="Email Reports"
            desc="Weekly earnings summary"
            value={settings.email_notifications}
            onToggle={() => toggle('email_notifications')}
          />
        </Card>

        {/* Job Alerts */}
        <SectionLabel label="Job Alerts" />
        <Card>
          <ToggleRow
            label="New Available Jobs"
            desc="Alert when a job is posted near you"
            value={settings.job_alerts}
            onToggle={() => toggle('job_alerts')}
          />
          <Divider />
          <ToggleRow
            label="Earnings Notifications"
            desc="Alert when payment is received"
            value={settings.earnings_alerts}
            onToggle={() => toggle('earnings_alerts')}
          />
          <Divider />
          <ToggleRow
            label="Job Alert Sound"
            desc="Play sound for new job notifications"
            value={settings.new_job_sound}
            onToggle={() => toggle('new_job_sound')}
          />
        </Card>

        {/* Security */}
        <SectionLabel label="Security" />
        <Card>
          <NavRow
            icon={<Lock size={20} color="#6366F1" />}
            iconBg="#EEF2FF"
            label="Change PIN"
            desc="Update your 4–6 digit PIN"
            onPress={() => navigation.navigate('ChangePin', { token })}
          />
          <Divider />
          <NavRow
            icon={<Eye size={20} color="#EC4899" />}
            iconBg="#FDF2F8"
            label="Privacy Settings"
            desc="Location, data sharing"
            onPress={() => navigation.navigate('Privacy', { token })}
          />
        </Card>

        {/* Support */}
        <SectionLabel label="Support" />
        <Card>
          <NavRow
            icon={<HelpCircle size={20} color="#8B5CF6" />}
            iconBg="#F5F3FF"
            label="Help Center"
            desc="FAQ and contact options"
            onPress={() => navigation.navigate('Support')}
          />
        </Card>

        <Text style={styles.version}>ZimAgriTrust Driver v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Shared sub-components ─────────────────────────────────────────────────────

function SectionLabel({ label }) {
  return <Text style={styles.sectionLabel}>{label}</Text>;
}

function Card({ children }) {
  return <View style={styles.card}>{children}</View>;
}

function Divider() {
  return <View style={styles.divider} />;
}

function ToggleRow({ icon, iconBg, label, desc, value, onToggle }) {
  return (
    <View style={styles.row}>
      <View style={styles.rowLeft}>
        {icon ? (
          <View style={[styles.iconBox, { backgroundColor: iconBg || '#F5F5F5' }]}>{icon}</View>
        ) : (
          <View style={styles.iconBoxEmpty} />
        )}
        <View style={styles.rowText}>
          <Text style={styles.rowLabel}>{label}</Text>
          {desc ? <Text style={styles.rowDesc}>{desc}</Text> : null}
        </View>
      </View>
      <Switch
        value={value}
        onValueChange={onToggle}
        trackColor={{ false: '#E0E0E0', true: theme.colors.sky }}
        thumbColor="#FFF"
        ios_backgroundColor="#E0E0E0"
      />
    </View>
  );
}

function NavRow({ icon, iconBg, label, desc, onPress }) {
  return (
    <TouchableOpacity style={styles.row} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.rowLeft}>
        {icon ? (
          <View style={[styles.iconBox, { backgroundColor: iconBg || '#F5F5F5' }]}>{icon}</View>
        ) : null}
        <View style={styles.rowText}>
          <Text style={styles.rowLabel}>{label}</Text>
          {desc ? <Text style={styles.rowDesc}>{desc}</Text> : null}
        </View>
      </View>
      <ChevronRight size={18} color="#CCC" />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scroll: { padding: 20, paddingBottom: 60 },

  sectionLabel: {
    fontSize: 11, fontWeight: '800', color: '#BBB',
    textTransform: 'uppercase', letterSpacing: 1,
    marginBottom: 10, marginTop: 24, marginLeft: 4,
  },
  card: {
    backgroundColor: '#FFF', borderRadius: 20,
    paddingHorizontal: 16, borderWidth: 1, borderColor: '#F0F0F0',
    ...theme.shadows.xs,
  },
  divider: { height: 1, backgroundColor: '#F5F5F5', marginLeft: 64 },

  row: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', paddingVertical: 14,
  },
  rowLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  iconBox: {
    width: 40, height: 40, borderRadius: 12,
    justifyContent: 'center', alignItems: 'center', marginRight: 14,
  },
  iconBoxEmpty: { width: 40, marginRight: 14 },
  rowText: { flex: 1, paddingRight: 8 },
  rowLabel: { fontSize: 15, fontWeight: '700', color: theme.colors.dark },
  rowDesc: { fontSize: 12, color: '#999', marginTop: 2 },

  version: {
    textAlign: 'center', fontSize: 12, color: '#DDD',
    fontWeight: '600', marginTop: 32,
  },
});
