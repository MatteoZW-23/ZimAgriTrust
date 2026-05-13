import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { HandCoins, ShoppingBag } from 'lucide-react-native';
import { getOffersMade } from '../api';
import { theme } from '../styles';

export default function MyOffersScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await getOffersMade(token);
      setOffers(Array.isArray(data) ? data : data?.data || []);
    } catch (err) {
      Alert.alert('Offers failed', err.message || 'Could not load offers you made.');
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
      <View style={styles.hero}>
        <HandCoins size={30} color={theme.colors.gold} />
        <Text style={styles.title}>My Offers</Text>
        <Text style={styles.subtitle}>Track submitted offers and accepted counter-offers.</Text>
      </View>

      {loading ? (
        <View style={styles.stateCard}><ActivityIndicator color={theme.colors.sky} /><Text style={styles.stateText}>Loading offers...</Text></View>
      ) : offers.length === 0 ? (
        <View style={styles.stateCard}>
          <ShoppingBag size={46} color="#cbd5e1" />
          <Text style={styles.emptyTitle}>No offers made</Text>
          <Text style={styles.stateText}>Browse the marketplace and make your first offer.</Text>
          <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate('Marketplace', { token, role: 'buyer' })}>
            <Text style={styles.primaryText}>Open Marketplace</Text>
          </TouchableOpacity>
        </View>
      ) : (
        offers.map((offer) => (
          <TouchableOpacity key={offer.id} style={styles.card} onPress={() => navigation.navigate('ListingDetail', { listingId: offer.listing_id, token, role: 'buyer' })}>
            <View>
              <Text style={styles.crop}>{offer.product_type || offer.listing?.product_type || 'Listing offer'}</Text>
              <Text style={styles.meta}>{Number(offer.quantity || 0).toLocaleString()} kg at ${Number(offer.offered_price || 0).toFixed(2)}/kg</Text>
            </View>
            <Text style={styles.status}>{offer.status}</Text>
          </TouchableOpacity>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#eff6ff' },
  content: { padding: 20, paddingTop: 28, paddingBottom: 120 },
  hero: { backgroundColor: '#0f2f45', borderRadius: 28, padding: 24, marginBottom: 18 },
  title: { color: '#fff', fontSize: 28, fontWeight: '900', marginTop: 12 },
  subtitle: { color: '#d7efff', fontSize: 14, lineHeight: 21, marginTop: 8 },
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#dbeafe', marginBottom: 14, flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  crop: { color: '#111827', fontSize: 17, fontWeight: '900' },
  meta: { color: '#64748b', fontSize: 13, fontWeight: '700', marginTop: 4 },
  status: { color: theme.colors.sky, fontSize: 12, fontWeight: '900', textTransform: 'uppercase' },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center' },
  emptyTitle: { color: '#111827', fontSize: 20, fontWeight: '900', marginTop: 12 },
  stateText: { color: '#64748b', fontWeight: '700', textAlign: 'center', marginTop: 8 },
  primaryBtn: { backgroundColor: theme.colors.sky, borderRadius: 14, paddingHorizontal: 20, paddingVertical: 12, marginTop: 16 },
  primaryText: { color: '#fff', fontWeight: '900' },
});
