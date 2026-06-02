import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Image, ScrollView, StyleSheet, Text, TouchableOpacity, View, Modal, TextInput, Dimensions } from 'react-native';
import { Bookmark, Flag, MapPin, ShieldCheck, Star, Tag, Wheat, X, ChevronLeft, ChevronRight, DollarSign } from 'lucide-react-native';
import { getListingDetails, reportListing, saveListing, makeOffer } from '../api';
import { theme } from '../styles';
import { formatCropName, formatGrade, formatLocation, formatMoney } from '../utils/formatters';

const { width } = Dimensions.get('window');

export default function ListingDetailScreen({ navigation, route }) {
  const { listing: initialListing = null, listingId, role = 'buyer', token } = route.params || {};
  const [listing, setListing] = useState(initialListing);
  const [loading, setLoading] = useState(!initialListing);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showOfferModal, setShowOfferModal] = useState(false);
  const [offerAmount, setOfferAmount] = useState('');
  const [submittingOffer, setSubmittingOffer] = useState(false);

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

  const handleMakeOffer = async () => {
    const amount = parseFloat(offerAmount);
    if (!amount || amount <= 0) {
      Alert.alert('Invalid Amount', 'Please enter a valid offer amount.');
      return;
    }

    setSubmittingOffer(true);
    try {
      await makeOffer(token, listing.id, amount);
      Alert.alert('Offer Sent', 'Your offer has been submitted successfully.');
      setShowOfferModal(false);
      setOfferAmount('');
    } catch (err) {
      Alert.alert('Offer Failed', err.message || 'Could not submit offer.');
    } finally {
      setSubmittingOffer(false);
    }
  };

  const images = listing.photo_urls || listing.image_urls || (listing.image_url ? [listing.image_url] : []);
  const currentImage = images[currentImageIndex] || null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
        <Text style={styles.backText}>Back</Text>
      </TouchableOpacity>

      <View style={styles.hero}>
        {images.length > 0 ? (
          <>
            <TouchableOpacity 
              style={styles.imageNavBtnLeft} 
              onPress={() => setCurrentImageIndex((prev) => (prev > 0 ? prev - 1 : images.length - 1))}
              disabled={images.length <= 1}
            >
              <ChevronLeft size={24} color="#fff" />
            </TouchableOpacity>
            <Image source={{ uri: currentImage }} style={styles.heroImage} />
            <TouchableOpacity 
              style={styles.imageNavBtnRight} 
              onPress={() => setCurrentImageIndex((prev) => (prev < images.length - 1 ? prev + 1 : 0))}
              disabled={images.length <= 1}
            >
              <ChevronRight size={24} color="#fff" />
            </TouchableOpacity>
            {images.length > 1 && (
              <View style={styles.imageDots}>
                {images.map((_, index) => (
                  <View 
                    key={index} 
                    style={[styles.dot, index === currentImageIndex && styles.dotActive]} 
                  />
                ))}
              </View>
            )}
          </>
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
          <TouchableOpacity style={styles.primaryBtn} onPress={() => setShowOfferModal(true)}>
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

      {/* Make Offer Modal */}
      <Modal
        visible={showOfferModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowOfferModal(false)}
      >
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowOfferModal(false)}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Make an Offer</Text>
              <TouchableOpacity onPress={() => setShowOfferModal(false)}>
                <X size={24} color="#64748b" />
              </TouchableOpacity>
            </View>

            <View style={styles.offerInfo}>
              <Text style={styles.offerInfoLabel}>Listing</Text>
              <Text style={styles.offerInfoValue}>{formatCropName(listing)}</Text>
            </View>

            <View style={styles.offerInfo}>
              <Text style={styles.offerInfoLabel}>Current Price</Text>
              <Text style={styles.offerInfoValue}>{formatMoney(listing.price_per_unit, listing.currency)}/{listing.quantity_unit || 'kg'}</Text>
            </View>

            <Text style={styles.inputLabel}>Your Offer (USD)</Text>
            <View style={styles.inputWrapper}>
              <DollarSign size={20} color="#64748b" style={{ marginRight: 12 }} />
              <TextInput
                style={styles.offerInput}
                placeholder="0.00"
                placeholderTextColor="#94a3b8"
                value={offerAmount}
                onChangeText={setOfferAmount}
                keyboardType="decimal-pad"
              />
            </View>

            <TouchableOpacity 
              style={[styles.modalConfirmBtn, submittingOffer && styles.modalConfirmBtnDisabled]} 
              onPress={handleMakeOffer}
              disabled={submittingOffer}
            >
              {submittingOffer ? <ActivityIndicator color="#fff" /> : <Text style={styles.modalConfirmText}>Submit Offer</Text>}
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
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
  hero: { borderRadius: 28, overflow: 'hidden', backgroundColor: '#fff', minHeight: 210, marginBottom: 16, position: 'relative' },
  heroImage: { width: '100%', height: 240 },
  heroPlaceholder: { height: 220, alignItems: 'center', justifyContent: 'center', backgroundColor: '#ecfdf5' },
  imageNavBtnLeft: { position: 'absolute', left: 12, top: '50%', marginTop: -20, width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(0,0,0,0.3)', justifyContent: 'center', alignItems: 'center' },
  imageNavBtnRight: { position: 'absolute', right: 12, top: '50%', marginTop: -20, width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(0,0,0,0.3)', justifyContent: 'center', alignItems: 'center' },
  imageDots: { position: 'absolute', bottom: 16, flexDirection: 'row', gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.5)' },
  dotActive: { backgroundColor: '#fff' },
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
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  modalTitle: { fontSize: 20, fontWeight: '900', color: '#111827' },
  offerInfo: { backgroundColor: '#F8FAFC', borderRadius: 12, padding: 16, marginBottom: 16 },
  offerInfoLabel: { fontSize: 12, fontWeight: '700', color: '#64748b', textTransform: 'uppercase' },
  offerInfoValue: { fontSize: 16, fontWeight: '900', color: '#111827', marginTop: 4 },
  inputLabel: { color: '#64748b', fontSize: 12, fontWeight: '900', textTransform: 'uppercase', marginBottom: 8 },
  inputWrapper: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 14, paddingHorizontal: 16, paddingVertical: 14, marginBottom: 16 },
  offerInput: { flex: 1, fontSize: 17, fontWeight: '900', color: '#111827' },
  modalConfirmBtn: { backgroundColor: theme.colors.green, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  modalConfirmBtnDisabled: { backgroundColor: '#CBD5E1' },
  modalConfirmText: { color: '#fff', fontWeight: '900', fontSize: 16 },
});
