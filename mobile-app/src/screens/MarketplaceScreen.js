import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, TextInput, Image, StyleSheet } from 'react-native';
import { theme } from '../styles';

export default function MarketplaceScreen({ navigation }) {
  const [searchQuery, setSearchQuery] = useState('');

  const categories = [
    { id: 'crops', name: 'Crops', icon: '🌾', color: '#E8F5E9' },
    { id: 'livestock', name: 'Livestock', icon: '🐄', color: '#EFEBE9' },
    { id: 'poultry', name: 'Poultry', icon: '🐔', color: '#FFFDE7' },
    { id: 'dairy', name: 'Dairy', icon: '🥛', color: '#E1F5FE' },
    { id: 'fisheries', name: 'Fisheries', icon: '🐟', color: '#E1F5FE' },
    { id: 'value', name: 'Value-Added', icon: '🏭', color: '#F3E5F5' },
    { id: 'near', name: 'Near Me', icon: '📍', color: '#F5F5F5' },
  ];

  const recommendations = [
    { id: '1', title: 'Grade A Maize', qty: '5,000kg', price: '$0.45/kg', loc: 'Mash West', rating: '4.9', sales: '234', sector: 'crops' },
    { id: '2', title: 'Brahman Cattle', qty: '10 heads', price: '$450/head', loc: 'Midlands', rating: '4.7', sales: '89', sector: 'livestock' },
    { id: '3', title: 'Fresh Milk', qty: '500L/day', price: '$0.80/L', loc: 'Manicaland', rating: '4.8', sales: '156', sector: 'dairy' },
  ];

  const recentOrders = [
    { id: 'AG-067', product: 'Maize (500kg)', price: '$450', status: 'In Payment', date: 'Mar 28', color: '#F9A825' },
    { id: 'AG-054', product: 'Milk (200L)', price: '$160', status: 'Completed', date: 'Mar 25', color: '#2E7D32' },
  ];

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hello, Grain Millers!</Text>
          <Text style={styles.walletLabel}>Wallet: <Text style={styles.walletValue}>$12,450.00</Text></Text>
        </View>
        <TouchableOpacity style={styles.profileBtn}>
           <Text style={{ fontSize: 20 }}>👤</Text>
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.searchInput}
          placeholder="Search products, crops, livestock..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        <TouchableOpacity><Text style={styles.micIcon}>🎤</Text></TouchableOpacity>
      </View>

      {/* Categories */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>FIND BY CATEGORY</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.categoryScroll}>
          {categories.map(cat => (
            <TouchableOpacity key={cat.id} style={styles.categoryItem}>
              <View style={[styles.categoryIconBox, { backgroundColor: cat.color }]}>
                 <Text style={{ fontSize: 24 }}>{cat.icon}</Text>
              </View>
              <Text style={styles.categoryLabel}>{cat.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Recommended */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>🔥 BEST FOR YOU</Text>
            <TouchableOpacity><Text style={styles.seeAll}>See All</Text></TouchableOpacity>
        </View>
        <View style={styles.recGrid}>
            {recommendations.map(item => (
                <TouchableOpacity key={item.id} style={styles.recCard} onPress={() => navigation.navigate('MakeOffer', { product: item })}>
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardTitle}>{item.title}</Text>
                        <Text style={styles.cardRating}>⭐ {item.rating}</Text>
                    </View>
                    <Text style={styles.cardQty}>{item.qty} available</Text>
                    <Text style={styles.cardPrice}>{item.price} | <Text style={styles.cardLoc}>{item.loc}</Text></Text>
                    <TouchableOpacity style={styles.offerBtn} onPress={() => navigation.navigate('MakeOffer', { product: item })}>
                        <Text style={styles.offerBtnText}>Make Offer</Text>
                    </TouchableOpacity>
                </TouchableOpacity>
            ))}
        </View>
      </View>

      {/* Market Insights */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📊 MARKET PRICES</Text>
        <TouchableOpacity style={styles.insightCard}>
            <View style={{ flex: 1 }}>
                <Text style={styles.insightTitle}>Maize Price Trend</Text>
                <Text style={styles.insightSub}>Prices are rising (+15%)</Text>
                <View style={styles.miniChart}>
                    <View style={[styles.chartBar, { height: '30%' }]} />
                    <View style={[styles.chartBar, { height: '45%' }]} />
                    <View style={[styles.chartBar, { height: '40%' }]} />
                    <View style={[styles.chartBar, { height: '65%' }]} />
                    <View style={[styles.chartBar, { height: '80%', backgroundColor: theme.colors.sky }]} />
                </View>
            </View>
            <View style={styles.insightAction}>
                <Text style={styles.buyNowText}>Buy Now</Text>
                <Text style={{ fontSize: 12, color: '#666' }}>Prices rising soon</Text>
            </View>
        </TouchableOpacity>
      </View>

      {/* Recent Orders */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📋 MY RECENT ORDERS</Text>
        <View style={styles.orderList}>
            {recentOrders.map(order => (
                <TouchableOpacity key={order.id} style={styles.orderItem} onPress={() => navigation.navigate('OrderDetails', { orderId: order.id })}>
                    <View style={styles.orderLeft}>
                        <Text style={styles.orderRef}>{order.id}</Text>
                        <Text style={styles.orderProd}>{order.product}</Text>
                    </View>
                    <View style={styles.orderRight}>
                        <Text style={[styles.orderStatus, { color: order.color }]}>● {order.status}</Text>
                        <Text style={styles.orderDate}>{order.date}</Text>
                    </View>
                </TouchableOpacity>
            ))}
        </View>
        <TouchableOpacity style={styles.viewAllBtn}>
            <Text style={styles.viewAllText}>View All Orders →</Text>
        </TouchableOpacity>
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { padding: 24, paddingTop: 60, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  greeting: { fontSize: 24, fontWeight: '800', color: theme.colors.black },
  walletLabel: { fontSize: 14, color: '#666', marginTop: 4 },
  walletValue: { fontWeight: '700', color: theme.colors.green },
  profileBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#F5F5F5', justifyContent: 'center', alignItems: 'center' },
  searchContainer: { marginHorizontal: 24, backgroundColor: '#F5F5F5', borderRadius: 12, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, height: 54 },
  searchIcon: { fontSize: 18, marginRight: 12 },
  searchInput: { flex: 1, fontSize: 16, fontWeight: '500' },
  micIcon: { fontSize: 18, color: theme.colors.sky },
  section: { marginTop: 32 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 24, marginBottom: 16 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#999', letterSpacing: 1.2, paddingHorizontal: 24, marginBottom: 16 },
  categoryScroll: { paddingLeft: 24, paddingRight: 8 },
  categoryItem: { alignItems: 'center', marginRight: 20 },
  categoryIconBox: { width: 64, height: 64, borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  categoryLabel: { fontSize: 12, fontWeight: '700', color: '#444' },
  recGrid: { paddingHorizontal: 24 },
  recCard: { backgroundColor: '#FFF', borderRadius: 16, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: '#EEE', elevation: 2, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  cardTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.black },
  cardRating: { fontSize: 14, fontWeight: '700', color: theme.colors.gold },
  cardQty: { fontSize: 14, color: '#666', marginTop: 4 },
  cardPrice: { fontSize: 16, fontWeight: '800', color: theme.colors.sky, marginTop: 8 },
  cardLoc: { fontWeight: '500', color: '#999' },
  offerBtn: { backgroundColor: theme.colors.sky, borderRadius: 8, paddingVertical: 10, alignItems: 'center', marginTop: 16 },
  offerBtnText: { color: '#FFF', fontWeight: '800', fontSize: 14 },
  insightCard: { marginHorizontal: 24, backgroundColor: '#F9F9F9', borderRadius: 16, padding: 20, flexDirection: 'row', alignItems: 'center' },
  insightTitle: { fontSize: 16, fontWeight: '800', color: theme.colors.black },
  insightSub: { fontSize: 12, color: theme.colors.green, fontWeight: '600', marginTop: 4 },
  miniChart: { flexDirection: 'row', alignItems: 'flex-end', height: 40, gap: 4, marginTop: 12 },
  chartBar: { width: 20, borderTopLeftRadius: 4, borderTopRightRadius: 4, backgroundColor: '#DDD' },
  insightAction: { paddingLeft: 20, borderLeftWidth: 1, borderLeftColor: '#EEE', alignItems: 'center' },
  buyNowText: { fontSize: 16, fontWeight: '800', color: theme.colors.sky },
  orderList: { paddingHorizontal: 24 },
  orderItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 16, borderBottomWidth: 1, borderBottomColor: '#F5F5F5' },
  orderRef: { fontSize: 12, fontWeight: '800', color: '#999' },
  orderProd: { fontSize: 16, fontWeight: '700', color: theme.colors.black, marginTop: 2 },
  orderStatus: { fontSize: 12, fontWeight: '800', textAlign: 'right' },
  orderDate: { fontSize: 12, color: '#999', textAlign: 'right', marginTop: 2 },
  viewAllBtn: { margin: 24, paddingVertical: 16, backgroundColor: '#F5F5F5', borderRadius: 12, alignItems: 'center' },
  viewAllText: { fontSize: 14, fontWeight: '700', color: theme.colors.black },
  seeAll: { fontSize: 14, fontWeight: '700', color: theme.colors.sky }
});
