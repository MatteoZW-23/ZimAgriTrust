import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, SafeAreaView, ScrollView, StyleSheet, Switch, Text, TouchableOpacity, View } from 'react-native';
import { Bell, Globe2, Shield } from 'lucide-react-native';
import { getUserSettings, updateUserSettings } from '../api';
import { theme } from '../styles';

export default function SettingsScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [settings, setSettings] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setSettings(await getUserSettings(token));
    } catch (err) {
      Alert.alert('Settings failed', err.message || 'Could not load settings.');
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const patch = async (changes) => {
    try {
      setSaving(true);
      const next = { ...(settings || {}), ...changes };
      setSettings(next);
      setSettings(await updateUserSettings(token, changes));
    } catch (err) {
      Alert.alert('Update failed', err.message || 'Could not update settings.');
      load();
    } finally {
      setSaving(false);
    }
  };

  if (!settings) {
    return <View style={styles.center}><ActivityIndicator color={theme.colors.green} /></View>;
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Settings</Text>
        <Text style={styles.subtitle}>Notification, language, privacy, and support controls.</Text>

        <Section icon={Bell} title="Notifications">
          <Toggle label="Push notifications" value={settings.push_notifications} onValueChange={(v) => patch({ push_notifications: v })} />
          <Toggle label="SMS notifications" value={settings.sms_notifications} onValueChange={(v) => patch({ sms_notifications: v })} />
          <Toggle label="Email notifications" value={settings.email_notifications} onValueChange={(v) => patch({ email_notifications: v })} />
        </Section>

        <Section icon={Globe2} title="Language">
          {[
            ['en', 'English'],
            ['sn', 'Shona'],
            ['nd', 'Ndebele'],
          ].map(([code, label]) => (
            <TouchableOpacity key={code} style={[styles.lang, settings.language === code && styles.langActive]} onPress={() => patch({ language: code })}>
              <Text style={[styles.langText, settings.language === code && styles.langTextActive]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </Section>

        <Section icon={Shield} title="Privacy and support">
          <TouchableOpacity style={styles.rowButton} onPress={() => navigation.navigate('Privacy', { token })}><Text style={styles.rowText}>Privacy controls</Text></TouchableOpacity>
          <TouchableOpacity style={styles.rowButton} onPress={() => navigation.navigate('Support')}><Text style={styles.rowText}>Support center</Text></TouchableOpacity>
        </Section>

        {saving && <Text style={styles.saving}>Saving...</Text>}
      </ScrollView>
    </SafeAreaView>
  );
}

function Section({ icon: Icon, title, children }) {
  return (
    <View style={styles.section}>
      <View style={styles.sectionHeader}><Icon size={20} color={theme.colors.green} /><Text style={styles.sectionTitle}>{title}</Text></View>
      {children}
    </View>
  );
}

function Toggle({ label, value, onValueChange }) {
  return (
    <View style={styles.toggleRow}>
      <Text style={styles.toggleText}>{label}</Text>
      <Switch value={!!value} onValueChange={onValueChange} trackColor={{ false: '#cbd5e1', true: '#bbf7d0' }} thumbColor={value ? theme.colors.green : '#f8fafc'} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F0DE' },
  content: { padding: 20, paddingTop: 56, paddingBottom: 120 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F6F0DE' },
  title: { color: '#111827', fontSize: 32, fontWeight: '900' },
  subtitle: { color: '#64748b', fontSize: 14, lineHeight: 21, marginTop: 8, marginBottom: 20 },
  section: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#e5e7eb', marginBottom: 14 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  sectionTitle: { color: '#111827', fontSize: 16, fontWeight: '900' },
  toggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10 },
  toggleText: { color: '#334155', fontSize: 15, fontWeight: '800' },
  lang: { padding: 14, borderRadius: 14, backgroundColor: '#f8fafc', marginTop: 8, borderWidth: 1, borderColor: '#e2e8f0' },
  langActive: { backgroundColor: theme.colors.green, borderColor: theme.colors.green },
  langText: { color: '#334155', fontWeight: '900' },
  langTextActive: { color: '#fff' },
  rowButton: { padding: 14, borderRadius: 14, backgroundColor: '#f8fafc', marginTop: 8, borderWidth: 1, borderColor: '#e2e8f0' },
  rowText: { color: '#334155', fontWeight: '900' },
  saving: { color: '#64748b', textAlign: 'center', fontWeight: '800' },
});
