import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  SafeAreaView, RefreshControl, Alert, ActivityIndicator
} from 'react-native';
import { getMyListings } from '../api';
import { theme } from '../styles';

const CROP_EMOJI = {
  maize: '🌽', corn: '🌽', wheat: '🌾', beans: '🫘', soybeans: '🫘',
  tobacco: '🍃', cotton: '🌿', groundnuts: '🥜', sorghum: '🌾',
  sunflower: '🌻', default: '🌱',
};

function cropEmoji(name = '') {
  return CROP_EMOJI[name.toLowerCase()] || CROP_EMOJI.default;
}

function statusColor(status = '') {
  const s = status.toUpperCase();
  if (s === 'ACTIVE') return '#22c55e';
  if (s === 'PENDING') return '#f59e0b';
  if (s === 'SOLD' || s === 'COMPLETED') return '#3b82f6';
  if (s === 'EXPIRED' || s === 'PAUSED') return '#94a3b8';
  return '#64748b';
}

export default function MyListingsScreen({ navigation, route }) {
  const { token } = route.params || {};
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      setError('');
      const data = await getMyListings(token);
      setListings(Array.isArray(data) ? data : data?.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load listings.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  const handleDelete = (id) => {
    Alert.alert('Delete Listing', 'Are you sure you want to delete this listing?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => {
        setListings(prev => prev.filter(l => l.id !== id));
      }},
    ]);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>My Listings</Text>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => navigation.navigate('CreateListing', { token })}
        >
          <Text style={styles.addBtnText}>+ NEW</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.colors.green} />
          <Text style={styles.loadingText}>Loading your listings...</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={load}>
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.green} />}
          contentContainerStyle={{ paddingBottom: 120 }}
        >
          {listings.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>🌱</Text>
              <Text style={styles.emptyTitle}>No listings yet</Text>
              <Text style={styles.emptyText}>Create your first listing to start selling.</Text>
              <TouchableOpacity
                style={styles.createBtn}
                onPress={() => navigation.navigate('CreateListing', { token })}
              >
                <Text style={styles.createBtnText}>Create Listing</Text>
              </TouchableOpacity>
            </View>
          ) : (
            listings.map((listing) => (
              <ListingCard
                key={listing.id}
                listing={listing}
                onDelete={() => handleDelete(listing.id)}
                onEdit={() => navigation.navigate('CreateListing', { token, listing })}
                onViewOffers={() => navigation.navigate('OrderDetails', { orderId: listing.id, role: 'farmer', token })}
              />
            ))
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function ListingCard({ listing, onDelete, onEdit, onViewOffers }) {
  const crop = listing.product_type || listing.crop || 'Listing';
  const qty = listing.quantity ? `${Number(listing.quantity).toLocaleString()} ${listing.quantity_unit || 'kg'}` : '—';
  const price = listing.price_per_unit ? `$${Number(listing.price_per_unit).toFixed(2)}/${listing.quantity_unit || 'kg'}` : '—';
  const total = listing.quantity && listing.price_per_unit
    ? `$${(Number(listing.quantity) * Number(listing.price_per_unit)).toFixed(2)}`
    : '—';
  const location = [listing.location_district, listing.location_province].filter(Boolean).join(', ') || listing.location || '—';
  const status = listing.status || 'ACTIVE';
  const offerCount = listing.offer_count || listing.offers_count || 0;

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardEmoji}>{cropEmoji(crop)}</Text>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardCrop}>{crop.toUpperCase()} — {listing.grade || 'Ungraded'}</Text>
          <Text style={styles.cardMeta}>{qty} | {price} | {total} total</Text>
          <Text style={styles.cardLocation}>📍 {location}</Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: statusColor(status) + '20' }]}>
          <Text style={[styles.statusText, { color: statusColor(status) }]}>{status}</Text>
        </View>
      </View>

      {offerCount > 0 && (
        <TouchableOpacity style={styles.offerBanner} onPress={onViewOffers}>
          <Text style={styles.offerBannerText}>🔴 {offerCount} new offer{offerCount > 1 ? 's' : ''}! Tap to review</Text>
        </TouchableOpacity>
      )}

      <View style={styles.cardActions}>
        <TouchableOpacity style={styles.actionBtn} onPress={onEdit}>
          <Text style={styles.actionBtnText}>✏️ EDIT</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionBtn, { borderColor: '#f59e0b' }]} onPress={onViewOffers}>
          <Text style={[styles.actionBtnText, { color: '#f59e0b' }]}>📋 OFFERS</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionBtn, { borderColor: '#ef4444' }]} onPress={onDelete}>
          <Text style={[styles.actionBtnText, { color: '#ef4444' }]}>🗑️ DELETE</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 24, paddingTop: 60 },
  back: { fontSize: 16, fontWeight: '700', color: theme.colors.sky },
  title: { fontSize: 18, fontWeight: '900', color: theme.colors.black },
  addBtn: { backgroundColor: theme.colors.green, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 12 },
  addBtnText: { color: '#fff', fontWeight: '900', fontSize: 12 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  loadingText: { marginTop: 12, color: '#64748b', fontWeight: '600' },
  errorText: { color: '#ef4444', fontWeight: '700', textAlign: 'center', marginBottom: 16 },
  retryBtn: { backgroundColor: theme.colors.green, paddingHorizontal: 24, paddingVertical: 12, borderRadius: 12 },
  retryText: { color: '#fff', fontWeight: '800' },
  empty: { alignItems: 'center', paddingTop: 80, paddingHorizontal: 40 },
  emptyIcon: { fontSize: 64, marginBottom: 16 },
  emptyTitle: { fontSize: 22, fontWeight: '900', color: theme.colors.black, marginBottom: 8 },
  emptyText: { fontSize: 14, color: '#64748b', textAlign: 'center', lineHeight: 22, marginBottom: 32 },
  createBtn: { backgroundColor: theme.colors.green, paddingHorizontal: 32, paddingVertical: 16, borderRadius: 16 },
  createBtnText: { color: '#fff', fontWeight: '900', fontSize: 16 },
  card: { marginHorizontal: 20, marginBottom: 16, backgroundColor: '#fff', borderRadius: 20, borderWidth: 1, borderColor: '#e5e7eb', padding: 20, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.06, shadowRadius: 12, elevation: 3 },
  cardHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, marginBottom: 12 },
  cardEmoji: { fontSize: 32 },
  cardCrop: { fontSize: 15, fontWeight: '900', color: theme.colors.black },
  cardMeta: { fontSize: 13, color: '#475569', marginTop: 2, fontWeight: '600' },
  cardLocation: { fontSize: 12, color: '#94a3b8', marginTop: 4, fontWeight: '600' },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  statusText: { fontSize: 11, fontWeight: '900' },
  offerBanner: { backgroundColor: '#fef2f2', borderRadius: 12, padding: 10, marginBottom: 12, borderWidth: 1, borderColor: '#fecaca' },
  offerBannerText: { color: '#dc2626', fontWeight: '800', fontSize: 13, textAlign: 'center' },
  cardActions: { flexDirection: 'row', gap: 8 },
  actionBtn: { flex: 1, paddingVertical: 10, borderRadius: 12, borderWidth: 1.5, borderColor: theme.colors.green, alignItems: 'center' },
  actionBtnText: { fontSize: 11, fontWeight: '900', color: theme.colors.green },
});
