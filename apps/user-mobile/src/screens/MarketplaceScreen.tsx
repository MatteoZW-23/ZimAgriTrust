import React, { useEffect, useState, useCallback } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View, Modal, FlatList } from 'react-native';
import { searchListings } from '../api';
import { theme } from '../styles';
import { formatMoney, parseNumber, formatCropName, formatLocation, formatGrade } from '../utils/formatters';
import { Search as IconSearch, Filter as IconFilter, SlidersHorizontal as IconSliders, X, ArrowUpDown, TrendingUp, TrendingDown, ChevronDown } from 'lucide-react-native';

const INITIAL_FILTERS = {
  crop: '',
  location: '',
  minPrice: '',
  maxPrice: '',
  grade: '',
};

const QUICK_CROPS = [];
const GRADE_OPTIONS = [{ label: 'Any grade', value: '' }];

function toOfferPayload(listing) {
  return {
    id: listing.id,
    title: formatCropName(listing),
    qty: `${Number(listing.quantity || 0).toLocaleString()} ${listing.quantity_unit || 'kg'}`,
    price: `${formatMoney(listing.price_per_unit, listing.currency)}/${listing.quantity_unit || 'kg'}`,
    loc: formatLocation(listing),
    rating: String(listing.seller_trust_score || 0),
    sector: listing.sector,
    sellerName: listing.seller_name,
    listing,
  };
}

function FilterPill({ label, selected, onPress }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[styles.pill, selected && styles.pillActive]}
      activeOpacity={0.85}
    >
      <Text style={[styles.pillText, selected && styles.pillTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

function StatCard({ label, value }) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export default function MarketplaceScreen({ navigation, route }) {
  const { role = 'buyer', token, profile } = route.params || {};
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [listings, setListings] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [showSortModal, setShowSortModal] = useState(false);
  const [sortBy, setSortBy] = useState('newest');
  const [searchQuery, setSearchQuery] = useState('');

  async function loadListings(nextFilters = filters, offset = 0, append = false) {
    const minPrice = parseNumber(nextFilters.minPrice);
    const maxPrice = parseNumber(nextFilters.maxPrice);

    if (minPrice !== undefined && maxPrice !== undefined && minPrice > maxPrice) {
      setError('Minimum price cannot be greater than maximum price.');
      setListings([]);
      setPagination(null);
      setLoading(false);
      return;
    }

    if (!append) setLoading(true);
    setError('');

    try {
      const response = await searchListings({
        crop: nextFilters.crop.trim() || undefined,
        location: nextFilters.location.trim() || undefined,
        min_price: minPrice,
        max_price: maxPrice,
        grade: nextFilters.grade || undefined,
        limit: 20,
        offset: offset,
      });

      const newData = response?.data || [];
      if (append) {
        setListings(prev => [...prev, ...newData]);
      } else {
        setListings(newData);
      }
      setPagination(response?.pagination || null);
    } catch (err) {
      setError(err.message || 'Unable to load live listings.');
      if (!append) {
        setListings([]);
        setPagination(null);
      }
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }

  const loadMore = useCallback(() => {
    if (loadingMore || !pagination || listings.length >= pagination.total) return;
    setLoadingMore(true);
    loadListings(filters, listings.length, true);
  }, [loadingMore, pagination, listings.length, filters]);

  const sortListings = useCallback((data) => {
    const sorted = [...data];
    if (sortBy === 'newest') {
      return sorted.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    } else if (sortBy === 'oldest') {
      return sorted.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
    } else if (sortBy === 'highest') {
      return sorted.sort((a, b) => (b.price_per_unit || 0) - (a.price_per_unit || 0));
    } else if (sortBy === 'lowest') {
      return sorted.sort((a, b) => (a.price_per_unit || 0) - (b.price_per_unit || 0));
    }
    return sorted;
  }, [sortBy]);

  useEffect(() => {
    loadListings(INITIAL_FILTERS);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateFilter(field, value) {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  function applySearch() {
    loadListings(filters);
  }

  function clearFilters() {
    setFilters(INITIAL_FILTERS);
    loadListings(INITIAL_FILTERS);
  }

  function applyQuickCrop(value) {
    const next = { ...filters, crop: value };
    setFilters(next);
    loadListings(next);
  }

  function applyGrade(value) {
    const next = { ...filters, grade: value };
    setFilters(next);
    loadListings(next);
  }

  function handleSearch() {
    setFilters(prev => ({ ...prev, crop: searchQuery }));
    loadListings({ ...filters, crop: searchQuery });
  }

  const sortedListings = sortListings(listings);

  const renderListing = ({ item }) => (
    <TouchableOpacity
      style={styles.listingCard}
      activeOpacity={0.9}
      onPress={() => navigation.navigate('ListingDetail', { listing: item, role, token, profile })}
    >
      <View style={styles.cardTop}>
        <View style={{ flex: 1, paddingRight: 12 }}>
          <Text style={styles.listingTitle}>{formatCropName(item)}</Text>
          <Text style={styles.listingLocation}>{formatLocation(item)}</Text>
        </View>

        <View style={styles.gradeBadge}>
          <Text style={styles.gradeBadgeText}>{formatGrade(item.grade || item.ai_grade_estimate)}</Text>
        </View>
      </View>

      <View style={styles.metricRow}>
        <StatCard
          label="Price per unit"
          value={formatMoney(item.price_per_unit, item.currency) + `/${item.quantity_unit || 'kg'}`}
        />
        <StatCard
          label="Quantity"
          value={`${Number(item.quantity || 0).toLocaleString()} ${item.quantity_unit || 'kg'}`}
        />
      </View>

      <View style={styles.footerRow}>
        <View>
          <Text style={styles.footerLabel}>Seller</Text>
          <Text style={styles.footerValue}>{item.seller_name || 'Anonymous'}</Text>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text style={styles.footerLabel}>Trust score</Text>
          <Text style={styles.footerValue}>{item.seller_trust_score || 0}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderFooter = () => {
    if (loadingMore) {
      return (
        <View style={styles.loadingMore}>
          <ActivityIndicator size="small" color={theme.colors.green} />
          <Text style={styles.loadingMoreText}>Loading more...</Text>
        </View>
      );
    }
    if (pagination && listings.length >= pagination.total) {
      return (
        <View style={styles.endOfList}>
          <Text style={styles.endOfListText}>No more listings</Text>
        </View>
      );
    }
    return null;
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.searchBar}>
          <IconSearch size={20} color="#64748b" style={{ marginRight: 12 }} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search crops, locations..."
            placeholderTextColor="#94a3b8"
            value={searchQuery}
            onChangeText={setSearchQuery}
            returnKeyType="search"
            onSubmitEditing={handleSearch}
            autoCapitalize="none"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => { setSearchQuery(''); setFilters(INITIAL_FILTERS); loadListings(INITIAL_FILTERS); }}>
              <X size={20} color="#64748b" />
            </TouchableOpacity>
          )}
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.headerBtn} onPress={() => setShowFilterModal(true)}>
            <IconFilter size={20} color={theme.colors.green} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerBtn} onPress={() => setShowSortModal(true)}>
            <ArrowUpDown size={20} color={theme.colors.green} />
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.sectionHeader}>
        <View>
          <Text style={styles.sectionTitle}>ACTIVE LISTINGS</Text>
          <Text style={styles.sectionSubtitle}>
            {pagination ? `${pagination.total} match${pagination.total === 1 ? '' : 'es'} found` : 'Search results from the API'}
          </Text>
        </View>
        <View style={styles.countBadge}>
          <Text style={styles.countBadgeText}>{loading ? '...' : String(sortedListings.length)}</Text>
        </View>
      </View>

      {loading ? (
        <View style={styles.stateCard}>
          <ActivityIndicator size="large" color={theme.colors.green} />
          <Text style={styles.stateTitle}>Loading live listings</Text>
          <Text style={styles.stateText}>Fetching the latest marketplace results.</Text>
        </View>
      ) : error ? (
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>Search failed</Text>
          <Text style={styles.stateText}>{error}</Text>
          <TouchableOpacity style={[styles.primaryButton, { marginTop: 16 }]} onPress={applySearch} activeOpacity={0.9}>
            <Text style={styles.primaryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : sortedListings.length === 0 ? (
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>No listings matched</Text>
          <Text style={styles.stateText}>Try a broader crop name, another district, or a different grade.</Text>
        </View>
      ) : (
        <FlatList
          data={sortedListings}
          renderItem={renderListing}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.results}
          showsVerticalScrollIndicator={false}
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListFooterComponent={renderFooter}
        />
      )}

      {/* Filter Modal */}
      <Modal
        visible={showFilterModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowFilterModal(false)}
      >
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowFilterModal(false)}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Filters</Text>
              <TouchableOpacity onPress={() => setShowFilterModal(false)}>
                <X size={24} color="#64748b" />
              </TouchableOpacity>
            </View>

            <Text style={styles.cardLabel}>Crop or keyword</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. maize"
              placeholderTextColor="#94a3b8"
              value={filters.crop}
              onChangeText={(text) => updateFilter('crop', text)}
              autoCapitalize="none"
            />

            <Text style={[styles.cardLabel, { marginTop: 14 }]}>Location</Text>
            <TextInput
              style={styles.input}
              placeholder="Province, district, or town"
              placeholderTextColor="#94a3b8"
              value={filters.location}
              onChangeText={(text) => updateFilter('location', text)}
            />

            <View style={styles.priceRow}>
              <View style={styles.priceField}>
                <Text style={styles.cardLabel}>Min price</Text>
                <TextInput
                  style={styles.input}
                  placeholder="0.00"
                  placeholderTextColor="#94a3b8"
                  value={filters.minPrice}
                  onChangeText={(text) => updateFilter('minPrice', text)}
                  keyboardType="decimal-pad"
                />
              </View>

              <View style={styles.priceField}>
                <Text style={styles.cardLabel}>Max price</Text>
                <TextInput
                  style={styles.input}
                  placeholder="0.00"
                  placeholderTextColor="#94a3b8"
                  value={filters.maxPrice}
                  onChangeText={(text) => updateFilter('maxPrice', text)}
                  keyboardType="decimal-pad"
                />
              </View>
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.secondaryButton} onPress={clearFilters} activeOpacity={0.9}>
                <Text style={styles.secondaryButtonText}>Clear</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.primaryButton} onPress={() => { setShowFilterModal(false); applySearch(); }} activeOpacity={0.9}>
                <Text style={styles.primaryButtonText}>Apply</Text>
              </TouchableOpacity>
            </View>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Sort Modal */}
      <Modal
        visible={showSortModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowSortModal(false)}
      >
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowSortModal(false)}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Sort By</Text>
              <TouchableOpacity onPress={() => setShowSortModal(false)}>
                <X size={24} color="#64748b" />
              </TouchableOpacity>
            </View>

            <TouchableOpacity style={[styles.sortOption, sortBy === 'newest' && styles.sortOptionActive]} onPress={() => { setSortBy('newest'); setShowSortModal(false); }}>
              <TrendingUp size={18} color={sortBy === 'newest' ? '#fff' : '#64748b'} />
              <Text style={[styles.sortOptionText, sortBy === 'newest' && styles.sortOptionTextActive]}>Newest First</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.sortOption, sortBy === 'oldest' && styles.sortOptionActive]} onPress={() => { setSortBy('oldest'); setShowSortModal(false); }}>
              <TrendingDown size={18} color={sortBy === 'oldest' ? '#fff' : '#64748b'} />
              <Text style={[styles.sortOptionText, sortBy === 'oldest' && styles.sortOptionTextActive]}>Oldest First</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.sortOption, sortBy === 'highest' && styles.sortOptionActive]} onPress={() => { setSortBy('highest'); setShowSortModal(false); }}>
              <TrendingUp size={18} color={sortBy === 'highest' ? '#fff' : '#64748b'} />
              <Text style={[styles.sortOptionText, sortBy === 'highest' && styles.sortOptionTextActive]}>Highest Price</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.sortOption, sortBy === 'lowest' && styles.sortOptionActive]} onPress={() => { setSortBy('lowest'); setShowSortModal(false); }}>
              <TrendingDown size={18} color={sortBy === 'lowest' ? '#fff' : '#64748b'} />
              <Text style={[styles.sortOptionText, sortBy === 'lowest' && styles.sortOptionTextActive]}>Lowest Price</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.gray50,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 18,
    backgroundColor: theme.colors.gray50,
    borderBottomWidth: 1,
    borderColor: '#e5e7eb',
    gap: 12,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginRight: 12,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.06,
    shadowRadius: 20,
    elevation: 4,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.black,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  headerBtn: {
    width: 48,
    height: 48,
    borderRadius: 18,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#DDE7D8',
    shadowColor: '#14532D',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.06,
    shadowRadius: 16,
    elevation: 3,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 32,
  },
  heroCard: {
    backgroundColor: '#1f2937',
    borderRadius: 28,
    padding: 22,
    marginBottom: 18,
  },
  heroKicker: {
    color: '#f9a825',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.6,
    marginBottom: 10,
  },
  heroTitle: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: '900',
    lineHeight: 34,
  },
  heroSub: {
    color: '#cbd5e1',
    fontSize: 14,
    lineHeight: 22,
    marginTop: 12,
  },
  searchCard: {
    backgroundColor: '#ffffff',
    borderRadius: 28,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginBottom: 22,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 5,
  },
  cardLabel: {
    color: '#475569',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.black,
  },
  priceRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 14,
  },
  priceField: {
    flex: 1,
  },
  pillRow: {
    paddingTop: 2,
    paddingBottom: 4,
    gap: 10,
  },
  pill: {
    backgroundColor: '#ffffff',
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  pillActive: {
    backgroundColor: theme.colors.green,
    borderColor: theme.colors.green,
  },
  pillText: {
    color: '#475569',
    fontSize: 13,
    fontWeight: '700',
  },
  pillTextActive: {
    color: '#ffffff',
  },
  actionRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 18,
  },
  primaryButton: {
    flex: 1,
    backgroundColor: theme.colors.green,
    borderRadius: 16,
    paddingVertical: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '900',
  },
  secondaryButton: {
    paddingHorizontal: 18,
    backgroundColor: '#f8fafc',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryButtonText: {
    color: '#334155',
    fontSize: 14,
    fontWeight: '800',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  sectionTitle: {
    color: '#111827',
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 0.4,
  },
  sectionSubtitle: {
    color: '#64748b',
    fontSize: 13,
    marginTop: 4,
  },
  countBadge: {
    backgroundColor: '#0F172A',
    borderRadius: 999,
    minWidth: 48,
    paddingHorizontal: 14,
    paddingVertical: 8,
    alignItems: 'center',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 4,
  },
  countBadgeText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '900',
  },
  stateCard: {
    backgroundColor: '#ffffff',
    borderRadius: 28,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginBottom: 20,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06,
    shadowRadius: 20,
    elevation: 4,
  },
  stateTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: '#111827',
    marginTop: 12,
  },
  stateText: {
    fontSize: 13,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 20,
    marginTop: 6,
  },
  results: {
    gap: 14,
  },
  listingCard: {
    backgroundColor: '#ffffff',
    borderRadius: 28,
    padding: 18,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.08,
    shadowRadius: 22,
    elevation: 5,
  },
  cardTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  listingTitle: {
    fontSize: 20,
    fontWeight: '900',
    color: '#111827',
  },
  listingLocation: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 4,
  },
  gradeBadge: {
    backgroundColor: '#fef3c7',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  gradeBadgeText: {
    color: '#92400e',
    fontSize: 12,
    fontWeight: '900',
  },
  metricRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#f8fafc',
    borderRadius: 18,
    padding: 14,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  statValue: {
    fontSize: 15,
    fontWeight: '900',
    color: '#111827',
  },
  statLabel: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    fontWeight: '800',
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  footerLabel: {
    fontSize: 11,
    color: '#94a3b8',
    textTransform: 'uppercase',
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  footerValue: {
    fontSize: 14,
    color: '#111827',
    fontWeight: '800',
    marginTop: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 14,
  },
  results: {
    paddingHorizontal: 20,
    paddingBottom: 100,
    gap: 14,
  },
  loadingMore: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  loadingMoreText: {
    color: '#64748b',
    fontSize: 14,
    fontWeight: '600',
  },
  endOfList: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  endOfListText: {
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    padding: 24,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '900',
    color: '#111827',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  sortOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    backgroundColor: '#F8FAFC',
  },
  sortOptionActive: {
    backgroundColor: theme.colors.green,
  },
  sortOptionText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#64748b',
    marginLeft: 12,
  },
  sortOptionTextActive: {
    color: '#fff',
  },
});
