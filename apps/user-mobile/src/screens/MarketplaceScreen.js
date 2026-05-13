import React, { useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { searchListings } from '../api';
import { theme } from '../styles';
import { formatMoney, parseNumber, formatCropName, formatLocation, formatGrade } from '../utils/formatters';

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
  const [error, setError] = useState('');

  async function loadListings(nextFilters = filters) {
    const minPrice = parseNumber(nextFilters.minPrice);
    const maxPrice = parseNumber(nextFilters.maxPrice);

    if (minPrice !== undefined && maxPrice !== undefined && minPrice > maxPrice) {
      setError('Minimum price cannot be greater than maximum price.');
      setListings([]);
      setPagination(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await searchListings({
        crop: nextFilters.crop.trim() || undefined,
        location: nextFilters.location.trim() || undefined,
        min_price: minPrice,
        max_price: maxPrice,
        grade: nextFilters.grade || undefined,
        limit: 20,
        offset: 0,
      });

      setListings(response?.data || []);
      setPagination(response?.pagination || null);
    } catch (err) {
      setError(err.message || 'Unable to load live listings.');
      setListings([]);
      setPagination(null);
    } finally {
      setLoading(false);
    }
  }

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

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
      <View style={styles.heroCard}>
        <Text style={styles.heroKicker}>LIVE MARKET SEARCH</Text>
        <Text style={styles.heroTitle}>Search active crop listings from the backend.</Text>
        <Text style={styles.heroSub}>
          Filter by crop, location, price range, and grade. Results are pulled from the FastAPI marketplace API.
        </Text>
      </View>

      <View style={styles.searchCard}>
        <Text style={styles.cardLabel}>Crop or keyword</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. maize"
          placeholderTextColor="#94a3b8"
          value={filters.crop}
          onChangeText={(text) => updateFilter('crop', text)}
          returnKeyType="search"
          onSubmitEditing={applySearch}
          autoCapitalize="none"
        />

        <Text style={[styles.cardLabel, { marginTop: 14 }]}>Location</Text>
        <TextInput
          style={styles.input}
          placeholder="Province, district, or town"
          placeholderTextColor="#94a3b8"
          value={filters.location}
          onChangeText={(text) => updateFilter('location', text)}
          returnKeyType="search"
          onSubmitEditing={applySearch}
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

        {QUICK_CROPS.length > 0 && (
          <>
            <Text style={[styles.cardLabel, { marginTop: 14 }]}>Popular crops</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pillRow}>
              {QUICK_CROPS.map((item) => (
                <FilterPill
                  key={item.value}
                  label={item.label}
                  selected={filters.crop.toLowerCase() === item.value}
                  onPress={() => applyQuickCrop(item.value)}
                />
              ))}
            </ScrollView>
          </>
        )}

        {GRADE_OPTIONS.length > 1 && (
          <>
            <Text style={[styles.cardLabel, { marginTop: 14 }]}>Grade</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pillRow}>
              {GRADE_OPTIONS.map((item) => (
                <FilterPill
                  key={item.label}
                  label={item.label}
                  selected={filters.grade === item.value}
                  onPress={() => applyGrade(item.value)}
                />
              ))}
            </ScrollView>
          </>
        )}

        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.primaryButton} onPress={applySearch} activeOpacity={0.9}>
            <Text style={styles.primaryButtonText}>Search Listings</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.secondaryButton} onPress={clearFilters} activeOpacity={0.9}>
            <Text style={styles.secondaryButtonText}>Clear</Text>
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
          <Text style={styles.countBadgeText}>{loading ? '...' : String(listings.length)}</Text>
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
      ) : listings.length === 0 ? (
        <View style={styles.stateCard}>
          <Text style={styles.stateTitle}>No listings matched</Text>
          <Text style={styles.stateText}>Try a broader crop name, another district, or a different grade.</Text>
        </View>
      ) : (
        <View style={styles.results}>
          {listings.map((listing) => (
            <TouchableOpacity
              key={listing.id}
              style={styles.listingCard}
              activeOpacity={0.9}
              onPress={() => navigation.navigate('ListingDetail', { listing, role, token, profile })}
            >
              <View style={styles.cardTop}>
                <View style={{ flex: 1, paddingRight: 12 }}>
                  <Text style={styles.listingTitle}>{formatCropName(listing)}</Text>
                  <Text style={styles.listingLocation}>{formatLocation(listing)}</Text>
                </View>

                <View style={styles.gradeBadge}>
                  <Text style={styles.gradeBadgeText}>{formatGrade(listing.grade || listing.ai_grade_estimate)}</Text>
                </View>
              </View>

              <View style={styles.metricRow}>
                <StatCard
                  label="Price per unit"
                  value={formatMoney(listing.price_per_unit, listing.currency) + `/${listing.quantity_unit || 'kg'}`}
                />
                <StatCard
                  label="Quantity"
                  value={`${Number(listing.quantity || 0).toLocaleString()} ${listing.quantity_unit || 'kg'}`}
                />
              </View>

              <View style={styles.footerRow}>
                <View>
                  <Text style={styles.footerLabel}>Seller</Text>
                  <Text style={styles.footerValue}>{listing.seller_name || 'Anonymous'}</Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={styles.footerLabel}>Trust score</Text>
                  <Text style={styles.footerValue}>{listing.seller_trust_score || 0}</Text>
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F0DE',
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
    borderRadius: 24,
    padding: 18,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginBottom: 22,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 4,
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
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 16,
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
    backgroundColor: '#f1f5f9',
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
    backgroundColor: '#111827',
    borderRadius: 999,
    minWidth: 48,
    paddingHorizontal: 14,
    paddingVertical: 8,
    alignItems: 'center',
  },
  countBadgeText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '900',
  },
  stateCard: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    padding: 22,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginBottom: 20,
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
    borderRadius: 24,
    padding: 18,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 3,
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
});
