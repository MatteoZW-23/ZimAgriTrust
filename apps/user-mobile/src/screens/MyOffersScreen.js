import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View, Modal, TextInput } from 'react-native';
import { HandCoins, ShoppingBag, X, Plus, Trash2, Clock, CheckCircle, XCircle, ArrowUpRight } from 'lucide-react-native';
import { getOffersMade, cancelOffer, increaseOffer } from '../api';
import { theme } from '../styles';
import { formatMoney } from '../utils/formatters';

export default function MyOffersScreen({ route, navigation }) {
  const { token } = route.params || {};
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [showIncreaseModal, setShowIncreaseModal] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState(null);
  const [increaseAmount, setIncreaseAmount] = useState('');
  const [increasing, setIncreasing] = useState(false);

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

  const filteredOffers = offers.filter(offer => {
    if (activeTab === 'all') return true;
    return offer.status?.toLowerCase() === activeTab;
  });

  const handleCancelOffer = async (offerId) => {
    Alert.alert(
      'Cancel Offer',
      'Are you sure you want to cancel this offer?',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Yes',
          style: 'destructive',
          onPress: async () => {
            try {
              await cancelOffer(token, offerId);
              Alert.alert('Cancelled', 'Your offer has been cancelled.');
              load();
            } catch (err) {
              Alert.alert('Cancel Failed', err.message || 'Could not cancel offer.');
            }
          },
        },
      ]
    );
  };

  const handleIncreaseOffer = () => {
    const amount = parseFloat(increaseAmount);
    if (!amount || amount <= 0) {
      Alert.alert('Invalid Amount', 'Please enter a valid increase amount.');
      return;
    }
    setIncreasing(true);
    increaseOffer(token, selectedOffer.id, amount)
      .then(() => {
        Alert.alert('Offer Increased', 'Your offer has been increased successfully.');
        setShowIncreaseModal(false);
        setIncreaseAmount('');
        setSelectedOffer(null);
        load();
      })
      .catch((err) => {
        Alert.alert('Increase Failed', err.message || 'Could not increase offer.');
      })
      .finally(() => {
        setIncreasing(false);
      });
  };

  const openIncreaseModal = (offer) => {
    setSelectedOffer(offer);
    setIncreaseAmount('');
    setShowIncreaseModal(true);
  };

  const getStatusIcon = (status) => {
    const s = status?.toLowerCase() || '';
    if (s === 'pending') return <Clock size={16} color="#f59e0b" />;
    if (s === 'accepted') return <CheckCircle size={16} color="#10b981" />;
    if (s === 'rejected') return <XCircle size={16} color="#ef4444" />;
    return <Clock size={16} color="#64748b" />;
  };

  const getStatusColor = (status) => {
    const s = status?.toLowerCase() || '';
    if (s === 'pending') return '#f59e0b';
    if (s === 'accepted') return '#10b981';
    if (s === 'rejected') return '#ef4444';
    return '#64748b';
  };

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

      <View style={styles.tabs}>
        {['all', 'pending', 'accepted', 'rejected'].map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.stateCard}><ActivityIndicator color={theme.colors.sky} /><Text style={styles.stateText}>Loading offers...</Text></View>
      ) : filteredOffers.length === 0 ? (
        <View style={styles.stateCard}>
          <ShoppingBag size={46} color="#cbd5e1" />
          <Text style={styles.emptyTitle}>No offers found</Text>
          <Text style={styles.stateText}>{activeTab === 'all' ? 'Browse the marketplace and make your first offer.' : `No ${activeTab} offers found.`}</Text>
          {activeTab === 'all' && (
            <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate('Marketplace', { token, role: 'buyer' })}>
              <Text style={styles.primaryText}>Open Marketplace</Text>
            </TouchableOpacity>
          )}
        </View>
      ) : (
        filteredOffers.map((offer) => (
          <View key={offer.id} style={styles.card}>
            <TouchableOpacity onPress={() => navigation.navigate('ListingDetail', { listingId: offer.listing_id, token, role: 'buyer' })}>
              <View style={styles.cardHeader}>
                <Text style={styles.crop}>{offer.product_type || offer.listing?.product_type || 'Listing offer'}</Text>
                <View style={styles.statusBadge}>
                  {getStatusIcon(offer.status)}
                  <Text style={[styles.statusText, { color: getStatusColor(offer.status) }]}>{offer.status || 'Pending'}</Text>
                </View>
              </View>
              <Text style={styles.meta}>{Number(offer.quantity || 0).toLocaleString()} kg at {formatMoney(offer.offered_price, offer.currency || 'USD')}/kg</Text>
              {offer.counter_price && (
                <Text style={styles.counterText}>Counter offer: {formatMoney(offer.counter_price, offer.currency || 'USD')}/kg</Text>
              )}
            </TouchableOpacity>
            {offer.status?.toLowerCase() === 'pending' && (
              <View style={styles.cardActions}>
                <TouchableOpacity style={styles.actionBtn} onPress={() => handleCancelOffer(offer.id)}>
                  <Trash2 size={16} color="#ef4444" />
                  <Text style={styles.actionText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.actionBtn, styles.actionBtnPrimary]} onPress={() => openIncreaseModal(offer)}>
                  <ArrowUpRight size={16} color="#fff" />
                  <Text style={styles.actionTextPrimary}>Increase</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        ))
      )}

      {/* Increase Offer Modal */}
      <Modal
        visible={showIncreaseModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowIncreaseModal(false)}
      >
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowIncreaseModal(false)}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Increase Offer</Text>
              <TouchableOpacity onPress={() => setShowIncreaseModal(false)}>
                <X size={24} color="#64748b" />
              </TouchableOpacity>
            </View>

            {selectedOffer && (
              <>
                <View style={styles.offerInfo}>
                  <Text style={styles.offerInfoLabel}>Current Offer</Text>
                  <Text style={styles.offerInfoValue}>{formatMoney(selectedOffer.offered_price, selectedOffer.currency || 'USD')}/kg</Text>
                </View>

                <Text style={styles.inputLabel}>Increase Amount (USD)</Text>
                <TextInput
                  style={styles.offerInput}
                  placeholder="0.00"
                  placeholderTextColor="#94a3b8"
                  value={increaseAmount}
                  onChangeText={setIncreaseAmount}
                  keyboardType="decimal-pad"
                />

                <TouchableOpacity
                  style={[styles.modalConfirmBtn, increasing && styles.modalConfirmBtnDisabled]}
                  onPress={handleIncreaseOffer}
                  disabled={increasing}
                >
                  {increasing ? <ActivityIndicator color="#fff" /> : <Text style={styles.modalConfirmText}>Increase Offer</Text>}
                </TouchableOpacity>
              </>
            )}
          </View>
        </TouchableOpacity>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#eff6ff' },
  content: { padding: 20, paddingTop: 28, paddingBottom: 120 },
  hero: { backgroundColor: '#0f2f45', borderRadius: 28, padding: 24, marginBottom: 18 },
  title: { color: '#fff', fontSize: 28, fontWeight: '900', marginTop: 12 },
  subtitle: { color: '#d7efff', fontSize: 14, lineHeight: 21, marginTop: 8 },
  tabs: { flexDirection: 'row', gap: 8, marginBottom: 18 },
  tab: { flex: 1, backgroundColor: '#fff', borderRadius: 12, paddingVertical: 12, alignItems: 'center', borderWidth: 1, borderColor: '#dbeafe' },
  tabActive: { backgroundColor: theme.colors.sky, borderColor: theme.colors.sky },
  tabText: { fontSize: 13, fontWeight: '700', color: '#64748b' },
  tabTextActive: { color: '#fff' },
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#dbeafe', marginBottom: 14 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 },
  crop: { color: '#111827', fontSize: 17, fontWeight: '900', flex: 1 },
  statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#F8FAFC', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999 },
  statusText: { fontSize: 11, fontWeight: '900', textTransform: 'uppercase' },
  meta: { color: '#64748b', fontSize: 13, fontWeight: '700', marginTop: 4 },
  counterText: { color: '#f59e0b', fontSize: 12, fontWeight: '700', marginTop: 4 },
  cardActions: { flexDirection: 'row', gap: 8, marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#e2e8f0' },
  actionBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingVertical: 10, borderRadius: 12, backgroundColor: '#FEE2E2' },
  actionBtnPrimary: { backgroundColor: theme.colors.sky },
  actionText: { fontSize: 13, fontWeight: '700', color: '#ef4444' },
  actionTextPrimary: { fontSize: 13, fontWeight: '700', color: '#fff' },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center' },
  emptyTitle: { color: '#111827', fontSize: 20, fontWeight: '900', marginTop: 12 },
  stateText: { color: '#64748b', fontWeight: '700', textAlign: 'center', marginTop: 8 },
  primaryBtn: { backgroundColor: theme.colors.sky, borderRadius: 14, paddingHorizontal: 20, paddingVertical: 12, marginTop: 16 },
  primaryText: { color: '#fff', fontWeight: '900' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  modalTitle: { fontSize: 20, fontWeight: '900', color: '#111827' },
  offerInfo: { backgroundColor: '#F8FAFC', borderRadius: 12, padding: 16, marginBottom: 16 },
  offerInfoLabel: { fontSize: 12, fontWeight: '700', color: '#64748b', textTransform: 'uppercase' },
  offerInfoValue: { fontSize: 16, fontWeight: '900', color: '#111827', marginTop: 4 },
  inputLabel: { color: '#64748b', fontSize: 12, fontWeight: '900', textTransform: 'uppercase', marginBottom: 8 },
  offerInput: { backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 14, paddingHorizontal: 16, paddingVertical: 14, marginBottom: 16, fontSize: 17, fontWeight: '900', color: '#111827' },
  modalConfirmBtn: { backgroundColor: theme.colors.sky, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  modalConfirmBtnDisabled: { backgroundColor: '#CBD5E1' },
  modalConfirmText: { color: '#fff', fontWeight: '900', fontSize: 16 },
});
