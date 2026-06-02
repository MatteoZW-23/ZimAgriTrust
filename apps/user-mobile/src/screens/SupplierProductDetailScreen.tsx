import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { ArrowLeft, ShoppingBag, Star, MapPin, Shield, Heart, Share2 } from 'lucide-react-native';
import { theme } from '../styles';

export default function SupplierProductDetailScreen({ navigation, route }) {
  const { product, token, profile } = route.params || {};
  const [quantity, setQuantity] = useState(1);
  const [isSaved, setIsSaved] = useState(false);

  const addToCart = () => {
    const cart = JSON.parse(localStorage.getItem('supplierCart') || '[]');
    const existingItem = cart.find(item => item.id === product.id);
    
    if (existingItem) {
      existingItem.quantity += quantity;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        price: product.price,
        supplier_name: product.supplier_name,
        product_type: product.product_type,
        quantity: quantity,
      });
    }
    
    localStorage.setItem('supplierCart', JSON.stringify(cart));
    Alert.alert('Added to Cart', `${quantity} x ${product.name} added to your cart.`);
  };

  const buyNow = () => {
    const cart = [{
      id: product.id,
      name: product.name,
      price: product.price,
      supplier_name: product.supplier_name,
      product_type: product.product_type,
      quantity: quantity,
    }];
    navigation.navigate('SupplierCheckout', { cart, total: product.price * quantity, token, profile });
  };

  const toggleSave = () => {
    setIsSaved(!isSaved);
    // Implement save/wishlist functionality
  };

  const shareProduct = () => {
    // Implement share functionality
    Alert.alert('Share', 'Share functionality coming soon!');
  };

  if (!product) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.backBtn}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Product Detail</Text>
          <View style={{ width: 60 }} />
        </View>
        <View style={styles.loadingContainer}>
          <Text style={styles.errorText}>Product not found</Text>
        </View>
      </View>
    );
  }

  const isMachinery = product.product_type === 'machinery';
  const totalPrice = product.price * quantity;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <ArrowLeft size={24} color={theme.colors.black} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Product Detail</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.headerBtn} onPress={toggleSave}>
            <Heart size={20} color={isSaved ? '#EF4444' : '#64748B'} fill={isSaved ? '#EF4444' : 'none'} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerBtn} onPress={shareProduct}>
            <Share2 size={20} color="#64748B" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Product Image */}
        <View style={styles.imageContainer}>
          <View style={styles.productImage}>
            <Text style={styles.productEmoji}>{isMachinery ? '🚜' : '🌽'}</Text>
          </View>
        </View>

        {/* Product Info */}
        <View style={styles.productSection}>
          <View style={styles.categoryBadge}>
            <Text style={styles.categoryText}>
              {isMachinery ? 'Machinery' : 'Agricultural Input'}
            </Text>
          </View>
          <Text style={styles.productName}>{product.name}</Text>
          
          <View style={styles.supplierInfo}>
            <Text style={styles.supplierName}>{product.supplier_name || 'Verified Supplier'}</Text>
            <View style={styles.rating}>
              <Star size={14} color="#F59E0B" fill="#F59E0B" />
              <Text style={styles.ratingText}>{product.supplier_rating?.toFixed(1) || 'N/A'}</Text>
            </View>
            {product.verification_status === 'approved' && (
              <View style={styles.verifiedBadge}>
                <Shield size={12} color={theme.colors.green} />
                <Text style={styles.verifiedText}>Verified</Text>
              </View>
            )}
          </View>

          <Text style={styles.price}>${product.price?.toFixed(2)}</Text>
          <Text style={styles.priceUnit}>{isMachinery ? '' : '/unit'}</Text>
        </View>

        {/* Availability & Quantity */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Availability</Text>
          <View style={styles.availabilityCard}>
            <Text style={[
              styles.availabilityText,
              product.quantity_available > 0 ? styles.inStock : styles.outOfStock,
            ]}>
              {product.quantity_available > 0 
                ? `${product.quantity_available} units in stock` 
                : 'Out of stock'}
            </Text>
          </View>

          {!isMachinery && (
            <View style={styles.quantityCard}>
              <Text style={styles.quantityLabel}>Quantity</Text>
              <View style={styles.quantityControl}>
                <TouchableOpacity
                  style={styles.quantityButton}
                  onPress={() => setQuantity(Math.max(1, quantity - 1))}
                >
                  <Text style={styles.quantityButtonText}>−</Text>
                </TouchableOpacity>
                <Text style={styles.quantityValue}>{quantity}</Text>
                <TouchableOpacity
                  style={styles.quantityButton}
                  onPress={() => setQuantity(quantity + 1)}
                >
                  <Text style={styles.quantityButtonText}>+</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>

        {/* Product Details */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Product Details</Text>
          <View style={styles.detailsCard}>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Category</Text>
              <Text style={styles.detailValue}>{product.category || 'N/A'}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Brand</Text>
              <Text style={styles.detailValue}>{product.brand || 'Generic'}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>SKU</Text>
              <Text style={styles.detailValue}>{product.sku || 'N/A'}</Text>
            </View>
            {isMachinery && (
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Condition</Text>
                <Text style={styles.detailValue}>{product.condition || 'Standard'}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Description */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Description</Text>
          <View style={styles.descriptionCard}>
            <Text style={styles.descriptionText}>
              {product.description || 'Quality agricultural product from verified supplier.'}
            </Text>
          </View>
        </View>

        {/* Supplier Information */}
        {product.supplier && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Supplier Information</Text>
            <View style={styles.supplierCard}>
              <View style={styles.supplierHeader}>
                <View style={styles.supplierAvatar}>
                  <ShoppingBag size={24} color={theme.colors.green} />
                </View>
                <View style={styles.supplierDetails}>
                  <Text style={styles.supplierBusinessName}>{product.supplier.business_name}</Text>
                  <View style={styles.supplierLocation}>
                    <MapPin size={14} color="#64748B" />
                    <Text style={styles.locationText}>{product.supplier.location || 'Zimbabwe'}</Text>
                  </View>
                </View>
              </View>
              <View style={styles.supplierStats}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{product.supplier.total_products || 'N/A'}</Text>
                  <Text style={styles.statLabel}>Products</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{product.supplier.total_orders || 'N/A'}</Text>
                  <Text style={styles.statLabel}>Orders</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>~2h</Text>
                  <Text style={styles.statLabel}>Response</Text>
                </View>
              </View>
              <TouchableOpacity
                style={styles.viewSupplierButton}
                onPress={() => navigation.navigate('SupplierProfile', { supplier: product.supplier, token, profile })}
              >
                <Text style={styles.viewSupplierButtonText}>View Supplier Profile</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Trust Badges */}
        <View style={styles.section}>
          <View style={styles.trustBadges}>
            <View style={styles.trustBadge}>
              <Shield size={20} color={theme.colors.green} />
              <Text style={styles.trustBadgeText}>Secure Payment</Text>
            </View>
            <View style={styles.trustBadge}>
              <ShoppingBag size={20} color={theme.colors.green} />
              <Text style={styles.trustBadgeText}>Verified Supplier</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Bottom Action Bar */}
      {product.quantity_available > 0 && (
        <View style={styles.footer}>
          <View style={styles.footerInfo}>
            <Text style={styles.footerTotal}>Total: ${totalPrice.toFixed(2)}</Text>
            <Text style={styles.footerSubtotal}>{quantity} x ${product.price.toFixed(2)}</Text>
          </View>
          <TouchableOpacity style={styles.buyNowButton} onPress={buyNow}>
            <Text style={styles.buyNowButtonText}>Buy Now</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.addToCartButton} onPress={addToCart}>
            <ShoppingBag size={20} color={theme.colors.green} />
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFF',
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backBtn: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.sky,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: theme.colors.black,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  headerBtn: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: '#F8FAFC',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#64748B',
  },
  content: {
    flex: 1,
  },
  imageContainer: {
    padding: 20,
    backgroundColor: '#F8FAFC',
  },
  productImage: {
    width: '100%',
    aspectRatio: 1,
    backgroundColor: '#E2E8F0',
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  productEmoji: {
    fontSize: 80,
  },
  productSection: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    marginBottom: 12,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '700',
    color: theme.colors.green,
    textTransform: 'uppercase',
  },
  productName: {
    fontSize: 24,
    fontWeight: '800',
    color: '#111827',
    marginBottom: 12,
  },
  supplierInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    flexWrap: 'wrap',
    gap: 12,
  },
  supplierName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#64748B',
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  ratingText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111827',
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    gap: 4,
  },
  verifiedText: {
    fontSize: 11,
    fontWeight: '700',
    color: theme.colors.green,
  },
  price: {
    fontSize: 32,
    fontWeight: '900',
    color: theme.colors.green,
  },
  priceUnit: {
    fontSize: 16,
    color: '#64748B',
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#64748B',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  availabilityCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 14,
  },
  availabilityText: {
    fontSize: 14,
    fontWeight: '600',
  },
  inStock: {
    color: theme.colors.green,
  },
  outOfStock: {
    color: '#EF4444',
  },
  quantityCard: {
    marginTop: 12,
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 14,
  },
  quantityLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    marginBottom: 8,
  },
  quantityControl: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  quantityButton: {
    width: 40,
    height: 40,
    backgroundColor: '#FFF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantityButtonText: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.colors.green,
  },
  quantityValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  detailsCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 14,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  detailLabel: {
    fontSize: 13,
    color: '#64748B',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  descriptionCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 14,
  },
  descriptionText: {
    fontSize: 14,
    color: '#475569',
    lineHeight: 22,
  },
  supplierCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 16,
  },
  supplierHeader: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  supplierAvatar: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#F0FDF4',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  supplierDetails: {
    flex: 1,
  },
  supplierBusinessName: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  supplierLocation: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  locationText: {
    fontSize: 12,
    color: '#64748B',
  },
  supplierStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  statLabel: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 4,
  },
  viewSupplierButton: {
    backgroundColor: theme.colors.green,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  viewSupplierButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '800',
  },
  trustBadges: {
    flexDirection: 'row',
    gap: 12,
  },
  trustBadge: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  trustBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: theme.colors.green,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
  },
  footerInfo: {
    flex: 1,
  },
  footerTotal: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  footerSubtotal: {
    fontSize: 12,
    color: '#64748B',
  },
  buyNowButton: {
    backgroundColor: theme.colors.green,
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
  },
  buyNowButtonText: {
    color: '#FFF',
    fontSize: 15,
    fontWeight: '800',
  },
  addToCartButton: {
    width: 48,
    height: 48,
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: theme.colors.green,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
