import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Bookmark, MapPin } from 'lucide-react-native';
import { getSavedListings } from '../api';
import { theme } from '../styles';
import { formatCropName, formatLocation, formatMoney } from '../utils/formatters';

export default function SavedListingsScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await getSavedListings(token);
      setListings(Array.isArray(data) ? data : data?.data || []);
    } catch (err) {
      Alert.alert('Saved listings failed', err.message || 'Could not load saved listings.');
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
        <Bookmark size={30} color={theme.colors.gold} />
        <Text style={styles.title}>Saved Listings</Text>
        <Text style={styles.subtitle}>Your bookmarked crops and inputs from the marketplace.</Text>
      </View>

      {loading ? (
        <View style={styles.stateCard}><ActivityIndicator color={theme.colors.sky} /><Text style={styles.stateText}>Loading saved listings...</Text></View>
      ) : listings.length === 0 ? (
        <View style={styles.stateCard}><Text style={styles.emptyTitle}>No saved listings</Text><Text style={styles.stateText}>Save listings from the marketplace to compare later.</Text></View>
      ) : (
        listings.map((listing) => (
          <TouchableOpacity key={listing.id} style={styles.card} onPress={() => navigation.navigate('ListingDetail', { listing, token, role: 'buyer' })}>
            <Text style={styles.crop}>{formatCropName(listing)}</Text>
            <View style={styles.row}>
              <MapPin size={14} color="#64748b" />
              <Text style={styles.meta}>{formatLocation(listing)}</Text>
            </View>
            <Text style={styles.price}>{formatMoney(listing.price_per_unit, listing.currency)}/{listing.quantity_unit || 'kg'}</Text>
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
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#dbeafe', marginBottom: 14 },
  crop: { color: '#111827', fontSize: 18, fontWeight: '900' },
  row: { flexDirection: 'row', gap: 6, alignItems: 'center', marginTop: 8 },
  meta: { color: '#64748b', fontSize: 13, fontWeight: '700' },
  price: { color: theme.colors.sky, fontSize: 16, fontWeight: '900', marginTop: 12 },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center' },
  emptyTitle: { color: '#111827', fontSize: 20, fontWeight: '900' },
  stateText: { color: '#64748b', fontWeight: '700', textAlign: 'center', marginTop: 8 },
});
