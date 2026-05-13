import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Image, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Bookmark, Flag, MapPin, ShieldCheck, Star, Tag, Wheat } from 'lucide-react-native';
import { getListingDetails, reportListing, saveListing } from '../api';
import { theme } from '../styles';
import { formatCropName, formatGrade, formatLocation, formatMoney } from '../utils/formatters';

export default function ListingDetailScreen({ navigation, route }) {
  const { listing: initialListing = null, listingId, role = 'buyer', token } = route.params || {};
  const [listing, setListing] = useState(initialListing);
  const [loading, setLoading] = useState(!initialListing);

  useEffect(() => {
    const id = listingId || initialListing?.id;
    if (!id || initialListing) return;
    setLoading(true);
    getListingDetails(token, id)
      .then(setListing)
      .catch((err) => Alert.alert('Listing failed', err.message || 'Could not load listing.'))
      .finally(() => setLoading(false));
  }, [initialListing, listingId, token]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={theme.colors.green} />
        <Text style={styles.centerText}>Loading listing...</Text>
      </View>
    );
  }

  if (!listing) {
    return (
      <View style={styles.center}>
        <Text style={styles.centerText}>Listing not found.</Text>
      </View>
    );
  }

  const photo = listing.photo_urls?.[0] || listing.image_urls?.[0] || listing.image_url;
  const sellerTrust = listing.seller_trust_score || listing.seller?.trust_score || 0;
  const isFarmerOwner = role === 'farmer' && String(listing.seller_id || '') === String(route.params?.profile?.id || '');

  const handleSave = async () => {
    try {
      await saveListing(token, listing.id);
      Alert.alert('Saved', 'Listing saved to your buyer list.');
    } catch (err) {
      Alert.alert('Save failed', err.message || 'Could not save listing.');
    }
  };

  const handleReport = async () => {
    try {
      await reportListing(token, listing.id, 'mobile_user_report');
      Alert.alert('Reported', 'Thank you. Our team will review this listing.');
    } catch (err) {
      Alert.alert('Report failed', err.message || 'Could not report listing.');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
        <Text style={styles.backText}>Back</Text>
      </TouchableOpacity>

      <View style={styles.hero}>
        {photo ? (
          <Image source={{ uri: photo }} style={styles.heroImage} />
        ) : (
          <View style={styles.heroPlaceholder}>
            <Wheat size={48} color={theme.colors.green} />
          </View>
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.title}>{formatCropName(listing)}</Text>
        <View style={styles.locationRow}>
          <MapPin size={16} color="#64748b" />
          <Text style={styles.location}>{formatLocation(listing)}</Text>
        </View>

        <View style={styles.metrics}>
          <Metric icon={Tag} label="Price" value={`${formatMoney(listing.price_per_unit, listing.currency)}/${listing.quantity_unit || 'kg'}`} />
          <Metric icon={Wheat} label="Quantity" value={`${Number(listing.quantity || 0).toLocaleString()} ${listing.quantity_unit || 'kg'}`} />
          <Metric icon={ShieldCheck} label="Grade" value={formatGrade(listing.grade || listing.ai_grade_estimate)} />
        </View>

        <View style={styles.sellerCard}>
          <View>
            <Text style={styles.sellerLabel}>Seller</Text>
            <Text style={styles.sellerName}>{listing.seller_name || listing.seller?.full_name || 'Verified seller'}</Text>
          </View>
          <View style={styles.trustBadge}>
            <Star size={14} color={theme.colors.gold} />
            <Text style={styles.trustText}>{sellerTrust}/100</Text>
          </View>
        </View>

        <View style={styles.badges}>
          <Text style={styles.badge}>ID {listing.seller_id_verified ? 'verified' : 'pending'}</Text>
          <Text style={styles.badge}>Crop {listing.verification_status || 'pending'}</Text>
          <Text style={styles.badge}>Escrow ready</Text>
        </View>

        {listing.notes ? <Text style={styles.notes}>{listing.notes}</Text> : null}
      </View>

      {role === 'buyer' ? (
        <View style={styles.actions}>
          <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate('MakeOffer', { token, product: { listing, title: formatCropName(listing) } })}>
            <Text style={styles.primaryText}>Make Offer</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryBtn} onPress={handleSave}>
            <Bookmark size={18} color={theme.colors.sky} />
            <Text style={styles.secondaryText}>Save</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.actions}>
          <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate('OffersReceived', { token, listingId: listing.id })}>
            <Text style={styles.primaryText}>{isFarmerOwner ? 'View Offers' : 'Open Offers'}</Text>
          </TouchableOpacity>
        </View>
      )}

      <TouchableOpacity style={styles.reportBtn} onPress={handleReport}>
        <Flag size={16} color={theme.colors.red} />
        <Text style={styles.reportText}>Report listing</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <View style={styles.metric}>
      <Icon size={16} color={theme.colors.green} />
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6F0DE' },
  content: { padding: 20, paddingBottom: 120, paddingTop: 28 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24, backgroundColor: '#F6F0DE' },
  centerText: { color: '#64748b', fontWeight: '800', marginTop: 12 },
  backBtn: { alignSelf: 'flex-start', backgroundColor: '#fff', borderRadius: 999, paddingHorizontal: 18, paddingVertical: 10, marginBottom: 14 },
  backText: { color: '#111827', fontWeight: '900' },
  hero: { borderRadius: 28, overflow: 'hidden', backgroundColor: '#fff', minHeight: 210, marginBottom: 16 },
  heroImage: { width: '100%', height: 240 },
  heroPlaceholder: { height: 220, alignItems: 'center', justifyContent: 'center', backgroundColor: '#ecfdf5' },
  card: { backgroundColor: '#fff', borderRadius: 28, padding: 20, borderWidth: 1, borderColor: '#e5e7eb' },
  title: { color: '#111827', fontSize: 28, fontWeight: '900' },
  locationRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8 },
  location: { color: '#64748b', fontSize: 14, fontWeight: '700' },
  metrics: { flexDirection: 'row', gap: 10, marginTop: 18 },
  metric: { flex: 1, backgroundColor: '#f8fafc', borderRadius: 18, padding: 12, borderWidth: 1, borderColor: '#e2e8f0' },
  metricValue: { color: '#111827', fontSize: 13, fontWeight: '900', marginTop: 8 },
  metricLabel: { color: '#64748b', fontSize: 10, fontWeight: '900', textTransform: 'uppercase', marginTop: 4 },
  sellerCard: { marginTop: 18, backgroundColor: '#111827', borderRadius: 20, padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  sellerLabel: { color: '#94a3b8', fontSize: 11, fontWeight: '900', textTransform: 'uppercase' },
  sellerName: { color: '#fff', fontSize: 16, fontWeight: '900', marginTop: 4 },
  trustBadge: { flexDirection: 'row', gap: 5, alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.1)', paddingHorizontal: 10, paddingVertical: 8, borderRadius: 999 },
  trustText: { color: '#fff', fontWeight: '900' },
  badges: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 16 },
  badge: { backgroundColor: '#dcfce7', color: '#166534', borderRadius: 999, paddingHorizontal: 12, paddingVertical: 7, fontSize: 12, fontWeight: '900', overflow: 'hidden' },
  notes: { color: '#475569', lineHeight: 22, marginTop: 16, fontWeight: '600' },
  actions: { flexDirection: 'row', gap: 10, marginTop: 18 },
  primaryBtn: { flex: 1, backgroundColor: theme.colors.green, borderRadius: 18, paddingVertical: 16, alignItems: 'center' },
  primaryText: { color: '#fff', fontSize: 16, fontWeight: '900' },
  secondaryBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#fff', borderRadius: 18, paddingHorizontal: 18, borderWidth: 1, borderColor: '#dbeafe' },
  secondaryText: { color: theme.colors.sky, fontWeight: '900' },
  reportBtn: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8, marginTop: 16, paddingVertical: 14 },
  reportText: { color: theme.colors.red, fontWeight: '900' },
});
