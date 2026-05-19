import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View, Modal } from 'react-native';
import { Check, RefreshCcw, X, Filter, ArrowUpDown, Clock, DollarSign, TrendingUp, TrendingDown } from 'lucide-react-native';
import { acceptOfferById, counterOfferById, getOffersReceived, rejectOfferById } from '../api';
import { theme } from '../styles';
import { TabView, SceneMap, TabBar } from 'react-native-tab-view';

export default function OffersReceivedScreen({ route, navigation }) {
  const { token, listingId } = route.params || {};
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [counterValues, setCounterValues] = useState({});
  const [busyId, setBusyId] = useState(null);
  const [index, setIndex] = useState(0);
  const [routes] = useState([
    { key: 'pending', title: 'Pending' },
    { key: 'accepted', title: 'Accepted' },
    { key: 'rejected', title: 'Rejected' },
  ]);
  const [sortBy, setSortBy] = useState('newest');
  const [showSortModal, setShowSortModal] = useState(false);

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

  const filterOffers = (status) => {
    const s = status.toUpperCase();
    return offers.filter(o => {
      const oStatus = (o.status || 'PENDING').toUpperCase();
      if (s === 'PENDING') return oStatus === 'PENDING';
      if (s === 'ACCEPTED') return oStatus === 'ACCEPTED' || oStatus === 'COMPLETED';
      if (s === 'REJECTED') return oStatus === 'REJECTED';
      return true;
    });
  };

  const sortOffers = (offersToSort) => {
    const sorted = [...offersToSort];
    if (sortBy === 'newest') {
      return sorted.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    } else if (sortBy === 'highest') {
      return sorted.sort((a, b) => Number(b.offered_price || 0) - Number(a.offered_price || 0));
    } else if (sortBy === 'lowest') {
      return sorted.sort((a, b) => Number(a.offered_price || 0) - Number(b.offered_price || 0));
    }
    return sorted;
  };

  const renderScene = ({ route }) => {
    const filteredOffers = filterOffers(route.key);
    const sortedOffers = sortOffers(filteredOffers);
    
    if (loading) {
      return (
        <View style={styles.stateCard}>
          <ActivityIndicator color={theme.colors.green} />
          <Text style={styles.stateText}>Loading offers...</Text>
        </View>
      );
    }

    if (sortedOffers.length === 0) {
      return (
        <View style={styles.stateCard}>
          <Clock size={48} color="#CBD5E1" style={{ marginBottom: 16 }} />
          <Text style={styles.emptyTitle}>No {route.key.toLowerCase()} offers</Text>
          <Text style={styles.stateText}>
            {route.key === 'pending' ? 'Offers awaiting your response will appear here.' : 
             route.key === 'accepted' ? 'Your accepted offers will appear here.' :
             'Rejected offers will appear here.'}
          </Text>
        </View>
      );
    }

    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
      >
        {sortedOffers.map((offer) => (
          <View key={offer.id} style={styles.card}>
            <View style={styles.cardTop}>
              <View>
                <Text style={styles.crop}>{offer.product_type || offer.listing?.product_type || 'Listing offer'}</Text>
                <Text style={styles.meta}>{Number(offer.quantity || 0).toLocaleString()} kg at ${Number(offer.offered_price || 0).toFixed(2)}/kg</Text>
                <Text style={styles.buyer}>Buyer: {offer.buyer_name || 'Unknown'}</Text>
              </View>
              <View style={styles.priceBadge}>
                <DollarSign size={14} color={theme.colors.green} />
                <Text style={styles.totalPrice}>${(Number(offer.quantity || 0) * Number(offer.offered_price || 0)).toFixed(2)}</Text>
              </View>
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
        ))}
      </ScrollView>
    );
  };

  const renderTabBar = (props) => (
    <TabBar
      {...props}
      style={styles.tabBar}
      labelStyle={styles.tabLabel}
      indicatorStyle={styles.tabIndicator}
      activeColor={theme.colors.green}
      inactiveColor="#94a3b8"
    />
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}><Text style={styles.back}>Back</Text></TouchableOpacity>
        <Text style={styles.title}>Offers Received</Text>
        <TouchableOpacity onPress={() => setShowSortModal(true)} style={styles.sortBtn}>
          <ArrowUpDown size={18} color={theme.colors.green} />
        </TouchableOpacity>
      </View>

      <TabView
        navigationState={{ index, routes }}
        renderScene={renderScene}
        onIndexChange={setIndex}
        renderTabBar={renderTabBar}
        swipeEnabled
      />

      <Modal
        visible={showSortModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowSortModal(false)}
      >
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowSortModal(false)}>
          <View style={styles.sortModal}>
            <Text style={styles.modalTitle}>Sort By</Text>
            <TouchableOpacity 
              style={[styles.sortOption, sortBy === 'newest' && styles.sortOptionActive]} 
              onPress={() => { setSortBy('newest'); setShowSortModal(false); }}
            >
              <Clock size={18} color={sortBy === 'newest' ? '#fff' : '#64748b'} />
              <Text style={[styles.sortOptionText, sortBy === 'newest' && styles.sortOptionTextActive]}>Newest First</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.sortOption, sortBy === 'highest' && styles.sortOptionActive]} 
              onPress={() => { setSortBy('highest'); setShowSortModal(false); }}
            >
              <TrendingUp size={18} color={sortBy === 'highest' ? '#fff' : '#64748b'} />
              <Text style={[styles.sortOptionText, sortBy === 'highest' && styles.sortOptionTextActive]}>Highest Price</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.sortOption, sortBy === 'lowest' && styles.sortOptionActive]} 
              onPress={() => { setSortBy('lowest'); setShowSortModal(false); }}
            >
              <TrendingDown size={18} color={sortBy === 'lowest' ? '#fff' : '#64748b'} />
              <Text style={[styles.sortOptionText, sortBy === 'lowest' && styles.sortOptionTextActive]}>Lowest Price</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
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
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 24, paddingTop: 60 },
  back: { color: theme.colors.sky, fontWeight: '900', fontSize: 16 },
  title: { color: '#111827', fontSize: 22, fontWeight: '900' },
  sortBtn: { padding: 8, borderRadius: 12, backgroundColor: '#F0FDF4' },
  tabBar: { backgroundColor: '#fff', elevation: 0, shadowOpacity: 0, borderBottomWidth: 1, borderBottomColor: '#e5e7eb' },
  tabLabel: { fontSize: 14, fontWeight: '700' },
  tabIndicator: { backgroundColor: theme.colors.green, height: 3 },
  card: { backgroundColor: '#fff', borderRadius: 22, padding: 18, borderWidth: 1, borderColor: '#e5e7eb', marginBottom: 14 },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  crop: { color: '#111827', fontSize: 17, fontWeight: '900' },
  meta: { color: '#64748b', fontSize: 13, fontWeight: '700', marginTop: 4 },
  buyer: { color: '#94a3b8', fontSize: 12, fontWeight: '600', marginTop: 2 },
  priceBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F0FDF4', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 12 },
  totalPrice: { color: theme.colors.green, fontSize: 16, fontWeight: '900', marginLeft: 4 },
  input: { marginTop: 14, backgroundColor: '#f8fafc', borderWidth: 1, borderColor: '#e2e8f0', borderRadius: 14, padding: 12, fontWeight: '800' },
  actions: { flexDirection: 'row', gap: 8, marginTop: 14 },
  action: { flex: 1, borderRadius: 12, paddingVertical: 11, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 5 },
  actionText: { color: '#fff', fontWeight: '900', fontSize: 12 },
  stateCard: { backgroundColor: '#fff', borderRadius: 22, padding: 24, alignItems: 'center', margin: 20 },
  emptyTitle: { color: '#111827', fontSize: 20, fontWeight: '900' },
  stateText: { color: '#64748b', fontWeight: '700', textAlign: 'center', marginTop: 8 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'flex-end' },
  sortModal: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24 },
  modalTitle: { fontSize: 20, fontWeight: '900', color: '#111827', marginBottom: 16 },
  sortOption: { flexDirection: 'row', alignItems: 'center', padding: 16, borderRadius: 12, marginBottom: 8, backgroundColor: '#F8FAFC' },
  sortOptionActive: { backgroundColor: theme.colors.green },
  sortOptionText: { fontSize: 16, fontWeight: '700', color: '#64748b', marginLeft: 12 },
  sortOptionTextActive: { color: '#fff' },
});
