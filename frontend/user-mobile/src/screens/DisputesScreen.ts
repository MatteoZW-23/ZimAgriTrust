import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { AlertTriangle, Plus } from 'lucide-react-native';
import { getDisputes } from '../api';
import { theme } from '../styles';

export default function DisputesScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await getDisputes(token);
      setDisputes(Array.isArray(data) ? data : data?.data || []);
    } catch (err) {
      Alert.alert('Disputes failed', err.message || 'Could not load disputes.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Disputes</Text>
          <Text style={styles.subtitle}>Open cases, evidence, and resolutions.</Text>
        </View>
        <TouchableOpacity style={styles.addBtn} onPress={() => navigation.navigate('RaiseDispute', { token })}>
          <Plus size={20} color="#fff" />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.stateCard}><ActivityIndicator color={theme.colors.red} /></View>
      ) : disputes.length === 0 ? (
        <View style={styles.stateCard}>
          <AlertTriangle size={42} color="#cbd5e1" />
          <Text style={styles.emptyTitle}>No disputes</Text>
          <Text style={styles.stateText}>If something goes wrong with an order, you can raise a case here.</Text>
        </View>
      ) : (
        disputes.map((dispute) => (
          <View key={dispute.id} style={styles.card}>
            <View style={styles.cardTop}>
              <Text style={styles.type}>{dispute.type}</Text>
              <Text style={styles.status}>{dispute.status}</Text>
            </View>
            <Text style={styles.description}>{dispute.description}</Text>
            {dispute.resolution ? <Text style={styles.resolution}>Resolution: {dispute.resolution}</Text> : null}
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff7ed' },
  content: { padding: 20, paddingTop: 56, paddingBottom: 120 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 },
  title: { color: '#111827', fontSize: 32, fontWeight: '900' },
  subtitle: { color: '#64748b', fontSize: 14, fontWeight: '700', marginTop: 4 },
  addBtn: { backgroundColor: theme.colors.red, borderRadius: 18, width: 48, height: 48, alignItems: 'center', justifyContent: 'center' },
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#fed7aa', marginBottom: 14 },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  type: { color: '#111827', fontSize: 17, fontWeight: '900', textTransform: 'capitalize' },
  status: { color: theme.colors.red, fontSize: 12, fontWeight: '900', textTransform: 'uppercase' },
  description: { color: '#475569', fontSize: 14, lineHeight: 21, marginTop: 10, fontWeight: '600' },
  resolution: { color: theme.colors.green, fontWeight: '800', marginTop: 12 },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center', borderWidth: 1, borderColor: '#fed7aa' },
  emptyTitle: { color: '#111827', fontSize: 20, fontWeight: '900', marginTop: 12 },
  stateText: { color: '#64748b', fontWeight: '700', textAlign: 'center', marginTop: 8 },
});
