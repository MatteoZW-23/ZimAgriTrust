import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
 StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Dimensions,
} from 'react-native';

import Animated, {
  FadeInDown,
  FadeInRight,
  FadeInUp,
} from 'react-native-reanimated';

import {
  Bookmark,
  HandCoins,
  PackageCheck,
  Search,
  ShieldCheck,
  Wallet,
  ChevronRight,
  TrendingUp,
  Star,
  Eye,
} from 'lucide-react-native';

import {
  getOffersMade,
  getProfile,
  getSavedListings,
  getTransactions,
  getWalletBalance,
  getListings,
} from '../api';

import { theme } from '../styles';

const { width } = Dimensions.get('window');

export default function BuyerDashboardScreen({
  navigation,
  route,
}) {
  const { token, profile: initialProfile = {} } =
    route.params || {};

  const [profile, setProfile] = useState(initialProfile);
  const [offers, setOffers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [saved, setSaved] = useState([]);
  const [wallet, setWallet] = useState(null);
  const [recommendations, setRecommendations] =
    useState([]);
  const [recentlyViewed, setRecentlyViewed] =
    useState([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!token) return;

    try {
      setError('');

      const [
        profileData,
        offerData,
        orderData,
        savedData,
        walletData,
        listingsData,
      ] = await Promise.all([
        getProfile(token),
        getOffersMade(token),
        getTransactions(token),
        getSavedListings(token).catch(() => []),
        getWalletBalance(token),
        getListings(token).catch(() => []),
      ]);

      setProfile(profileData || {});

      setOffers(
        Array.isArray(offerData)
          ? offerData
          : offerData?.data || []
      );

      setOrders(
        Array.isArray(orderData)
          ? orderData
          : orderData?.data || []
      );

      setSaved(
        Array.isArray(savedData)
          ? savedData
          : savedData?.data || []
      );

      setWallet(walletData || null);

      const allListings = Array.isArray(listingsData)
        ? listingsData
        : listingsData?.data || [];

      setRecommendations(allListings.slice(0, 6));
      setRecentlyViewed(allListings.slice(0, 4));
    } catch (err) {
      setError(
        err?.message ||
          'Could not load your buyer dashboard.'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const pendingOffers = offers.filter(
    (item) =>
      String(item.status || '').toUpperCase() ===
      'PENDING'
  ).length;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            load();
          }}
          tintColor={theme.colors.sky}
        />
      }
    >
      {/* HERO */}
      <Animated.View
        entering={FadeInDown.duration(600).springify()}
        style={styles.hero}
      >
        <View style={styles.heroGlow} />

        <View style={styles.heroContent}>
          <Text style={styles.kicker}>
            BUYER PORTAL
          </Text>

          <Text style={styles.title}>
            Welcome back,{'\n'}
            {profile.full_name ||
              profile.name ||
              'Buyer'}
            !
          </Text>

          <Text style={styles.subtitle}>
            Discover verified crops and manage
            your agricultural pipeline.
          </Text>
        </View>
      </Animated.View>

      {/* LOADING */}
      {loading ? (
        <View style={styles.stateCard}>
          <ActivityIndicator
            size="large"
            color={theme.colors.sky}
          />
        </View>
      ) : error ? (
        <View style={styles.stateCard}>
          <Text style={styles.errorText}>
            {error}
          </Text>

          <TouchableOpacity
            style={styles.primaryBtn}
            onPress={load}
            activeOpacity={0.85}
          >
            <Text style={styles.primaryText}>
              Try Again
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          {/* METRICS */}
          <Animated.View
            entering={FadeInUp.duration(600)
              .delay(100)
              .springify()}
            style={styles.grid}
          >
            <Metric
              icon={HandCoins}
              color="#F59E0B"
              label="Pending Offers"
              value={pendingOffers}
            />

            <Metric
              icon={PackageCheck}
              color="#10B981"
              label="Active Orders"
              value={orders.length}
            />

            <Metric
              icon={Bookmark}
              color="#8B5CF6"
              label="Saved Items"
              value={saved.length}
            />

            <Metric
              icon={Wallet}
              color="#0EA5E9"
              label="Wallet Balance"
              value={`$${Number(
                wallet?.available_usd ??
                  wallet?.available ??
                  0
              ).toFixed(2)}`}
            />
          </Animated.View>

          {/* QUICK ACTIONS */}
          <Animated.View
            entering={FadeInRight.duration(600)
              .delay(200)
              .springify()}
            style={styles.actionSection}
          >
            <Text style={styles.sectionTitle}>
              Quick Actions
            </Text>

            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={
                styles.actionRow
              }
            >
              <ActionCard
                icon={Search}
                color="#0EA5E9"
                label="Browse Market"
                onPress={() =>
                  navigation.navigate(
                    'Marketplace',
                    {
                      token,
                      role: 'buyer',
                    }
                  )
                }
              />

              <ActionCard
                icon={HandCoins}
                color="#F59E0B"
                label="My Offers"
                onPress={() =>
                  navigation.navigate(
                    'MyOffers',
                    {
                      token,
                    }
                  )
                }
              />

              <ActionCard
                icon={ShieldCheck}
                color="#10B981"
                label="Saved Listings"
                onPress={() =>
                  navigation.navigate(
                    'SavedListings',
                    {
                      token,
                    }
                  )
                }
              />
            </ScrollView>
          </Animated.View>

          {/* RECENT ORDERS */}
          <Animated.View
            entering={FadeInUp.duration(600)
              .delay(300)
              .springify()}
            style={styles.section}
          >
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Recent Orders
              </Text>

              <TouchableOpacity
                onPress={() =>
                  navigation.navigate(
                    'MyOrders',
                    {
                      token,
                      role: 'buyer',
                    }
                  )
                }
                activeOpacity={0.85}
              >
                <Text style={styles.seeAll}>
                  See All
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.orderList}>
              {orders.slice(0, 3).map((order, i) => (
                <View key={order.id}>
                  <TouchableOpacity
                    style={styles.rowCard}
                    activeOpacity={0.85}
                    onPress={() =>
                      navigation.navigate(
                        'OrderDetails',
                        {
                          orderId: order.id,
                          role: 'buyer',
                          token,
                        }
                      )
                    }
                  >
                    <View style={styles.rowIconWrap}>
                      <PackageCheck
                        size={20}
                        color="#10B981"
                      />
                    </View>

                    <View style={styles.rowInfo}>
                      <Text
                        style={styles.rowTitle}
                        numberOfLines={1}
                      >
                        {order.product ||
                          order.product_type ||
                          'Crop order'}
                      </Text>

                      <Text style={styles.rowSub}>
                        {order.status ||
                          'PENDING'}
                      </Text>
                    </View>

                    <View
                      style={
                        styles.rowAmountWrap
                      }
                    >
                      <Text
                        style={
                          styles.rowAmount
                        }
                      >
                        $
                        {Number(
                          order.total_amount ||
                            order.amount ||
                            0
                        ).toFixed(2)}
                      </Text>

                      <ChevronRight
                        size={16}
                        color="#CBD5E1"
                      />
                    </View>
                  </TouchableOpacity>

                  {i <
                    Math.min(
                      orders.length,
                      3
                    ) -
                      1 && (
                    <View
                      style={styles.divider}
                    />
                  )}
                </View>
              ))}

              {orders.length === 0 && (
                <View style={styles.emptyCard}>
                  <Text style={styles.emptyText}>
                    Your agricultural pipeline
                    is clear. Browse the market
                    to find verified produce.
                  </Text>
                </View>
              )}
            </View>
          </Animated.View>

          {/* RECOMMENDATIONS */}
          <Animated.View
            entering={FadeInUp.duration(600)
              .delay(400)
              .springify()}
            style={styles.section}
          >
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Recommended for You
              </Text>

              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() =>
                  navigation.navigate(
                    'Marketplace',
                    {
                      token,
                      role: 'buyer',
                    }
                  )
                }
              >
                <Text style={styles.seeAll}>
                  See All
                </Text>
              </TouchableOpacity>
            </View>

            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={
                false
              }
              contentContainerStyle={
                styles.horizontalList
              }
            >
              {recommendations
                .slice(0, 4)
                .map((listing) => (
                  <TouchableOpacity
                    key={listing.id}
                    activeOpacity={0.85}
                    style={styles.listingCard}
                    onPress={() =>
                      navigation.navigate(
                        'ListingDetail',
                        {
                          listingId:
                            listing.id,
                          token,
                          role: 'buyer',
                        }
                      )
                    }
                  >
                    <View
                      style={
                        styles.listingImagePlaceholder
                      }
                    >
                      <TrendingUp
                        size={24}
                        color="#38BDF8"
                      />
                    </View>

                    <View
                      style={
                        styles.listingContent
                      }
                    >
                      <Text
                        style={
                          styles.listingTitle
                        }
                        numberOfLines={1}
                      >
                        {listing.product_type ||
                          listing.crop ||
                          'Crop'}
                      </Text>

                      <Text
                        style={
                          styles.listingLocation
                        }
                        numberOfLines={1}
                      >
                        {listing.location ||
                          'Location'}
                      </Text>

                      <View
                        style={
                          styles.listingPriceRow
                        }
                      >
                        <Text
                          style={
                            styles.listingPrice
                          }
                        >
                          $
                          {Number(
                            listing.price_per_unit ||
                              0
                          ).toFixed(2)}
                          /
                          {listing.quantity_unit ||
                            'kg'}
                        </Text>

                        <View
                          style={
                            styles.ratingBadge
                          }
                        >
                          <Star
                            size={10}
                            color="#F59E0B"
                            fill="#F59E0B"
                          />

                          <Text
                            style={
                              styles.ratingText
                            }
                          >
                            4.5
                          </Text>
                        </View>
                      </View>
                    </View>
                  </TouchableOpacity>
                ))}

              {recommendations.length ===
                0 && (
                <View style={styles.emptyCard}>
                  <Text style={styles.emptyText}>
                    No recommendations
                    available at the moment.
                  </Text>
                </View>
              )}
            </ScrollView>
          </Animated.View>

          {/* RECENTLY VIEWED */}
          <Animated.View
            entering={FadeInUp.duration(600)
              .delay(500)
              .springify()}
            style={styles.section}
          >
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Recently Viewed
              </Text>

              <TouchableOpacity
                activeOpacity={0.85}
                onPress={() =>
                  navigation.navigate(
                    'Marketplace',
                    {
                      token,
                      role: 'buyer',
                    }
                  )
                }
              >
                <Text style={styles.seeAll}>
                  See All
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.orderList}>
              {recentlyViewed
                .slice(0, 3)
                .map((listing, i) => (
                  <View key={listing.id}>
                    <TouchableOpacity
                      activeOpacity={0.85}
                      style={styles.rowCard}
                      onPress={() =>
                        navigation.navigate(
                          'ListingDetail',
                          {
                            listingId:
                              listing.id,
                            token,
                            role: 'buyer',
                          }
                        )
                      }
                    >
                      <View
                        style={
                          styles.rowIconWrap
                        }
                      >
                        <Eye
                          size={20}
                          color="#8B5CF6"
                        />
                      </View>

                      <View
                        style={styles.rowInfo}
                      >
                        <Text
                          style={
                            styles.rowTitle
                          }
                          numberOfLines={1}
                        >
                          {listing.product_type ||
                            listing.crop ||
                            'Crop'}
                        </Text>

                        <Text
                          style={styles.rowSub}
                        >
                          {listing.location ||
                            'Location'}
                        </Text>
                      </View>

                      <View
                        style={
                          styles.rowAmountWrap
                        }
                      >
                        <Text
                          style={
                            styles.rowAmount
                          }
                        >
                          $
                          {Number(
                            listing.price_per_unit ||
                              0
                          ).toFixed(2)}
                        </Text>

                        <ChevronRight
                          size={16}
                          color="#CBD5E1"
                        />
                      </View>
                    </TouchableOpacity>

                    {i <
                      Math.min(
                        recentlyViewed.length,
                        3
                      ) -
                        1 && (
                      <View
                        style={styles.divider}
                      />
                    )}
                  </View>
                ))}

              {recentlyViewed.length ===
                0 && (
                <View style={styles.emptyCard}>
                  <Text style={styles.emptyText}>
                    Your recently viewed items
                    will appear here.
                  </Text>
                </View>
              )}
            </View>
          </Animated.View>
        </>
      )}
    </ScrollView>
  );
}

function Metric({
  icon: Icon,
  color,
  label,
  value,
}) {
  return (
    <View style={styles.metricCard}>
      <View
        style={[
          styles.metricIconWrap,
          {
            backgroundColor: `${color}15`,
          },
        ]}
      >
        <Icon size={22} color={color} />
      </View>

      <Text style={styles.metricValue}>
        {value}
      </Text>

      <Text style={styles.metricLabel}>
        {label}
      </Text>
    </View>
  );
}

function ActionCard({
  icon: Icon,
  color,
  label,
  onPress,
}) {
  return (
    <TouchableOpacity
      style={[
        styles.actionCard,
        { backgroundColor: color },
      ]}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <View style={styles.actionIconFloat}>
        <Icon
          size={32}
          color="rgba(255,255,255,0.2)"
        />
      </View>

      <View style={styles.actionIconContainer}>
        <Icon size={24} color="#FFF" />
      </View>

      <Text style={styles.actionText}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.gray50,
  },

  content: {
    paddingBottom: 120,
  },

  hero: {
    backgroundColor: '#0F172A',
    borderBottomLeftRadius: 48,
    borderBottomRightRadius: 48,
    padding: 32,
    paddingTop: 60,
    paddingBottom: 46,
    shadowColor: '#0F172A',
    shadowOffset: {
      width: 0,
      height: 14,
    },
    shadowOpacity: 0.12,
    shadowRadius: 20,
    elevation: 8,
    position: 'relative',
    overflow: 'hidden',
  },

  heroGlow: {
    position: 'absolute',
    top: -50,
    right: -50,
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: '#38BDF8',
    opacity: 0.15,
    transform: [{ scale: 1.5 }],
  },

  heroContent: {
    position: 'relative',
    zIndex: 2,
  },

  kicker: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 1.5,
    marginBottom: 8,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 34,
    lineHeight: 40,
    fontWeight: '900',
    marginBottom: 12,
    letterSpacing: -0.8,
  },

  subtitle: {
    color: '#94A3B8',
    fontSize: 15,
    lineHeight: 24,
    fontWeight: '600',
    maxWidth: '85%',
  },

  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginTop: -24,
  },

  metricCard: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 28,
    padding: 22,
    marginBottom: 14,
    shadowColor: '#0F172A',
    shadowOffset: {
      width: 0,
      height: 12,
    },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 5,
    borderWidth: 1,
    borderColor: '#EAF0F6',
  },

  metricIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },

  metricValue: {
    color: '#0F172A',
    fontSize: 28,
    fontWeight: '900',
    marginBottom: 4,
    letterSpacing: -0.6,
  },

  metricLabel: {
    color: '#64748B',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
  },

  actionSection: {
    marginTop: 36,
  },

  sectionTitle: {
    color: '#0F172A',
    fontSize: 18,
    fontWeight: '900',
    marginBottom: 16,
  },

  actionRow: {
    paddingHorizontal: 24,
  },

  actionCard: {
    width: 138,
    height: 138,
    borderRadius: 30,
    padding: 18,
    justifyContent: 'space-between',
    marginRight: 12,
    shadowColor: '#0F172A',
    shadowOffset: {
      width: 0,
      height: 12,
    },
    shadowOpacity: 0.16,
    shadowRadius: 18,
    elevation: 8,
    position: 'relative',
    overflow: 'hidden',
  },

  actionIconFloat: {
    position: 'absolute',
    top: -10,
    right: -10,
  },

  actionIconContainer: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor:
      'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },

  actionText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '800',
    lineHeight: 20,
  },

  section: {
    marginTop: 40,
    paddingHorizontal: 24,
  },

  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },

  seeAll: {
    color: '#0EA5E9',
    fontSize: 14,
    fontWeight: '800',
  },

  orderList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 32,
    shadowColor: '#0F172A',
    shadowOffset: {
      width: 0,
      height: 12,
    },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 5,
    borderWidth: 1,
    borderColor: '#EAF0F6',
  },

  rowCard: {
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },

  rowIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 18,
    backgroundColor: '#ECFDF5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },

  rowInfo: {
    flex: 1,
  },

  rowTitle: {
    color: '#0F172A',
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 4,
  },

  rowSub: {
    color: '#64748B',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },

  rowAmountWrap: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  rowAmount: {
    color: '#0F172A',
    fontSize: 18,
    fontWeight: '900',
    marginRight: 8,
  },

  divider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginHorizontal: 20,
  },

  emptyCard: {
    padding: 32,
    alignItems: 'center',
  },

  emptyText: {
    color: '#94A3B8',
    fontWeight: '500',
    lineHeight: 22,
    textAlign: 'center',
  },

  horizontalList: {
    paddingHorizontal: 24,
  },

  listingCard: {
    width: 160,
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    overflow: 'hidden',
    marginRight: 12,
    shadowColor: '#0F172A',
    shadowOffset: {
      width: 0,
      height: 10,
    },
    shadowOpacity: 0.08,
    shadowRadius: 18,
    elevation: 5,
    borderWidth: 1,
    borderColor: '#EAF0F6',
  },

  listingImagePlaceholder: {
    height: 100,
    backgroundColor: '#F0F9FF',
    justifyContent: 'center',
    alignItems: 'center',
  },

  listingContent: {
    padding: 12,
  },

  listingTitle: {
    color: '#0F172A',
    fontSize: 14,
    fontWeight: '800',
    marginBottom: 4,
  },

  listingLocation: {
    color: '#64748B',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 8,
  },

  listingPriceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  listingPrice: {
    color: '#0F172A',
    fontSize: 14,
    fontWeight: '900',
  },

  ratingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },

  ratingText: {
    color: '#92400E',
    fontSize: 10,
    fontWeight: '800',
    marginLeft: 4,
  },

  stateCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 32,
    padding: 40,
    marginHorizontal: 24,
    marginTop: 24,
    alignItems: 'center',
    shadowColor: '#0F172A',
    shadowOffset: {
      width: 0,
      height: 12,
    },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 5,
    borderWidth: 1,
    borderColor: '#EAF0F6',
  },

  errorText: {
    color: '#EF4444',
    textAlign: 'center',
    fontWeight: '800',
    marginBottom: 20,
    fontSize: 16,
  },

  primaryBtn: {
    backgroundColor: '#0EA5E9',
    borderRadius: 18,
    paddingHorizontal: 24,
    paddingVertical: 15,
    shadowColor: '#0EA5E9',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
    elevation: 6,
  },

  primaryText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 15,
  },
});
