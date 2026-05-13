import React, { useCallback, useEffect, useState } from 'react';
import { Alert, Platform, SafeAreaView, ScrollView, Share, StyleSheet, Switch, Text, TouchableOpacity, View } from 'react-native';
import { Download, ShieldCheck, Trash2 } from 'lucide-react-native';
import { deleteAccount, exportPersonalData, getUserSettings, updateUserSettings } from '../api';
import { clearSession } from '../utils/auth';
import { theme } from '../styles';

export default function PrivacyScreen({ route, navigation }) {
  const { token, onLogout } = route.params || {};
  const [settings, setSettings] = useState({});

  const load = useCallback(() => {
    getUserSettings(token).then(setSettings).catch(() => {});
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const patch = async (changes) => {
    const next = { ...settings, ...changes };
    setSettings(next);
    try {
      setSettings(await updateUserSettings(token, changes));
    } catch {
      load();
    }
  };

  const downloadData = async () => {
    const data = await exportPersonalData(token);
    const text = JSON.stringify(data, null, 2);
    if (Platform.OS === 'web') {
      const blob = new Blob([text], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'zimagritrust-data.json';
      a.click();
      URL.revokeObjectURL(url);
      return;
    }
    await Share.share({ title: 'ZimAgriTrust data export', message: text });
  };

  const deleteData = () => {
    Alert.alert('Delete account data?', 'This closes your account and anonymizes your personal information.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          await deleteAccount(token);
          await clearSession();
          if (onLogout) onLogout();
          navigation.popToTop();
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <ShieldCheck size={34} color={theme.colors.green} />
        <Text style={styles.title}>Privacy</Text>
        <Text style={styles.subtitle}>Control how your data is used across marketplace, wallet, and dispute services.</Text>

        <View style={styles.card}>
          <Toggle label="Data sharing consent" value={settings.data_sharing_consent} onValueChange={(v) => patch({ data_sharing_consent: v })} />
          <Toggle label="Show phone after escrow" value={settings.phone_visibility} onValueChange={(v) => patch({ phone_visibility: v })} />
        </View>

        <TouchableOpacity style={styles.button} onPress={downloadData}>
          <Download size={18} color="#fff" />
          <Text style={styles.buttonText}>Download My Data</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.button, styles.deleteButton]} onPress={deleteData}>
          <Trash2 size={18} color="#fff" />
          <Text style={styles.buttonText}>Delete My Data</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function Toggle({ label, value, onValueChange }) {
  return (
    <View style={styles.toggleRow}>
      <Text style={styles.toggleText}>{label}</Text>
      <Switch value={!!value} onValueChange={onValueChange} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F0DE' },
  content: { padding: 20, paddingTop: 56, paddingBottom: 120 },
  title: { color: '#111827', fontSize: 32, fontWeight: '900', marginTop: 12 },
  subtitle: { color: '#64748b', fontSize: 14, lineHeight: 21, marginTop: 8, marginBottom: 20 },
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#e5e7eb', marginBottom: 16 },
  toggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10 },
  toggleText: { color: '#334155', fontSize: 15, fontWeight: '800', flex: 1, paddingRight: 12 },
  button: { backgroundColor: theme.colors.green, borderRadius: 16, paddingVertical: 15, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8, marginBottom: 12 },
  deleteButton: { backgroundColor: theme.colors.red },
  buttonText: { color: '#fff', fontWeight: '900', fontSize: 15 },
});
