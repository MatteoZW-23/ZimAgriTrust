import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Check, RefreshCcw, X } from 'lucide-react-native';
import { acceptOfferById, counterOfferById, getOffersReceived, rejectOfferById } from '../api';
import { theme } from '../styles';

export default function OffersReceivedScreen({ route, navigation }) {
  const { token, listingId } = route.params || {};
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [counterValues, setCounterValues] = useState({});
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    try {
      const data = await getOffersReceived(token);
      const items = Array.isArray(data) ? data : data?.data || [];
      setOffers(listingId ? items.filter((offer) => String(offer.listing_id) === String(listingId)) : items);
    } catch (err) {
      Alert.alert('Offers failed', err.message || 'Could not load received offers.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [listingId, token]);

  useEffect(() => { load(); }, [load]);

  const run = async (offer, action) => {
    try {
      setBusyId(offer.id);
      if (action === 'accept') await acceptOfferById(token, offer.id);
      if (action === 'reject') await rejectOfferById(token, offer.id);
      if (action === 'counter') await counterOfferById(token, offer.id, counterValues[offer.id]);
      await load();
      Alert.alert('Updated', `Offer ${action}ed successfully.`);
    } catch (err) {
      Alert.alert('Offer update failed', err.message || 'Could not update this offer.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}><Text style={styles.back}>Back</Text></TouchableOpacity>
        <Text style={styles.title}>Offers Received</Text>
      </View>

      {loading ? (
        <View style={styles.stateCard}><ActivityIndicator color={theme.colors.green} /><Text style={styles.stateText}>Loading offers...</Text></View>
      ) : offers.length === 0 ? (
        <View style={styles.stateCard}><Text style={styles.emptyTitle}>No offers yet</Text><Text style={styles.stateText}>Buyer offers for your listings will appear here.</Text></View>
      ) : (
        offers.map((offer) => (
          <View key={offer.id} style={styles.card}>
            <View style={styles.cardTop}>
              <View>
                <Text style={styles.crop}>{offer.product_type || offer.listing?.product_type || 'Listing offer'}</Text>
                <Text style={styles.meta}>{Number(offer.quantity || 0).toLocaleString()} kg at ${Number(offer.offered_price || 0).toFixed(2)}/kg</Text>
              </View>
              <Text style={styles.status}>{offer.status}</Text>
            </View>

            <TextInput
              style={styles.input}
              placeholder="Counter price per kg"
              keyboardType="decimal-pad"
              value={counterValues[offer.id] || ''}
              onChangeText={(text) => setCounterValues((current) => ({ ...current, [offer.id]: text }))}
            />

            <View style={styles.actions}>
              <Action disabled={busyId === offer.id} color={theme.colors.green} icon={Check} label="Accept" onPress={() => run(offer, 'accept')} />
              <Action disabled={busyId === offer.id} color={theme.colors.gold} icon={RefreshCcw} label="Counter" onPress={() => run(offer, 'counter')} />
              <Action disabled={busyId === offer.id} color={theme.colors.red} icon={X} label="Reject" onPress={() => run(offer, 'reject')} />
            </View>
          </View>
        ))
      )}
    </ScrollView>
  );
}

function Action({ icon: Icon, color, label, onPress, disabled }) {
  return (
    <TouchableOpacity style={[styles.action, { backgroundColor: color }, disabled && { opacity: 0.5 }]} onPress={onPress} disabled={disabled}>
      <Icon size={14} color="#fff" />
      <Text style={styles.actionText}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F0DE' },
  content: { padding: 20, paddingTop: 56, paddingBottom: 120 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 },
  back: { color: theme.colors.sky, fontWeight: '900' },
  title: { color: '#111827', fontSize: 22, fontWeight: '900' },
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#e5e7eb', marginBottom: 14 },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  crop: { color: '#111827', fontSize: 17, fontWeight: '900' },
  meta: { color: '#64748b', fontSize: 13, fontWeight: '700', marginTop: 4 },
  status: { color: theme.colors.green, fontSize: 12, fontWeight: '900', textTransform: 'uppercase' },
  input: { marginTop: 14, backgroundColor: '#f8fafc', borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 14, padding: 12, fontWeight: '800' },
  actions: { flexDirection: 'row', gap: 8, marginTop: 14 },
  action: { flex: 1, borderRadius: 12, paddingVertical: 11, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 5 },
  actionText: { color: '#fff', fontWeight: '900', fontSize: 12 },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center' },
  emptyTitle: { color: '#111827', fontSize: 20, fontWeight: '900' },
  stateText: { color: '#64748b', fontWeight: '700', textAlign: 'center', marginTop: 8 },
});
