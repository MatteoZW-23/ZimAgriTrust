import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View, Image, FlatList, Dimensions } from 'react-native';
import { Bookmark, MapPin, Trash2, X } from 'lucide-react-native';
import { getSavedListings, unsaveListing } from '../api';
import { theme } from '../styles';
import { formatCropName, formatLocation, formatMoney } from '../utils/formatters';

const { width } = Dimensions.get('window');
const CARD_WIDTH = (width - 60) / 2;

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

  const handleRemove = async (listingId) => {
    Alert.alert(
      'Remove Listing',
      'Are you sure you want to remove this listing from your saved items?',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await unsaveListing(token, listingId);
              setListings(prev => prev.filter(l => l.id !== listingId));
              Alert.alert('Removed', 'Listing removed from saved items.');
            } catch (err) {
              Alert.alert('Remove Failed', err.message || 'Could not remove listing.');
            }
          },
        },
      ]
    );
  };

  const renderListing = ({ item }) => {
    const photo = item.photo_urls?.[0] || item.image_urls?.[0] || item.image_url;
    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('ListingDetail', { listing: item, token, role: 'buyer' })}
      >
        <View style={styles.cardImageContainer}>
          {photo ? (
            <Image source={{ uri: photo }} style={styles.cardImage} />
          ) : (
            <View style={styles.cardImagePlaceholder}>
              <Bookmark size={32} color={theme.colors.sky} />
            </View>
          )}
          <TouchableOpacity
            style={styles.removeBtn}
            onPress={(e) => {
              e.stopPropagation();
              handleRemove(item.id);
            }}
          >
            <Trash2 size={16} color="#fff" />
          </TouchableOpacity>
        </View>
        <View style={styles.cardContent}>
          <Text style={styles.crop} numberOfLines={2}>{formatCropName(item)}</Text>
          <View style={styles.row}>
            <MapPin size={12} color="#64748b" />
            <Text style={styles.meta} numberOfLines={1}>{formatLocation(item)}</Text>
          </View>
          <Text style={styles.price}>{formatMoney(item.price_per_unit, item.currency)}/{item.quantity_unit || 'kg'}</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView
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
          <View style={styles.stateCard}>
            <Bookmark size={46} color="#cbd5e1" />
            <Text style={styles.emptyTitle}>No saved listings</Text>
            <Text style={styles.stateText}>Save listings from the marketplace to compare later.</Text>
            <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate('Marketplace', { token, role: 'buyer' })}>
              <Text style={styles.primaryText}>Browse Marketplace</Text>
            </TouchableOpacity>
          </View>
        ) : null}
      </ScrollView>

      {!loading && listings.length > 0 && (
        <FlatList
          data={listings}
          renderItem={renderListing}
          keyExtractor={(item) => item.id}
          numColumns={2}
          contentContainerStyle={styles.gridContent}
          columnWrapperStyle={styles.row}
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#eff6ff' },
  content: { padding: 20, paddingTop: 28 },
  gridContent: { padding: 20, paddingBottom: 120, paddingTop: 0 },
  hero: { backgroundColor: '#0f2f45', borderRadius: 28, padding: 24, marginBottom: 18 },
  title: { color: '#fff', fontSize: 28, fontWeight: '900', marginTop: 12 },
  subtitle: { color: '#d7efff', fontSize: 14, lineHeight: 21, marginTop: 8 },
  card: { backgroundColor: '#fff', borderRadius: 22, borderWidth: 1, borderColor: '#dbeafe', marginBottom: 14, width: CARD_WIDTH, overflow: 'hidden' },
  cardImageContainer: { position: 'relative', height: 140 },
  cardImage: { width: '100%', height: '100%' },
  cardImagePlaceholder: { width: '100%', height: '100%', backgroundColor: '#ecfdf5', justifyContent: 'center', alignItems: 'center' },
  removeBtn: { position: 'absolute', top: 8, right: 8, width: 32, height: 32, borderRadius: 16, backgroundColor: 'rgba(239, 68, 68, 0.9)', justifyContent: 'center', alignItems: 'center' },
  cardContent: { padding: 12 },
  crop: { color: '#111827', fontSize: 15, fontWeight: '900', marginBottom: 6 },
  row: { flexDirection: 'row', gap: 4, alignItems: 'center', marginBottom: 6 },
  meta: { color: '#64748b', fontSize: 11, fontWeight: '700', flex: 1 },
  price: { color: theme.colors.sky, fontSize: 14, fontWeight: '900' },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center' },
  emptyTitle: { color: '#111827', fontSize: 20, fontWeight: '900', marginTop: 12 },
  stateText: { color: '#64748b', fontWeight: '700', textAlign: 'center', marginTop: 8 },
  primaryBtn: { backgroundColor: theme.colors.sky, borderRadius: 14, paddingHorizontal: 20, paddingVertical: 12, marginTop: 16 },
  primaryText: { color: '#fff', fontWeight: '900' },
});
