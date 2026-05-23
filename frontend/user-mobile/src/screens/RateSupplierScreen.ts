import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Star, Send, Package, MapPin, Shield } from 'lucide-react-native';
import { theme } from '../styles';
import { rateSupplier } from '../api';

export default function RateSupplierScreen({ navigation, route }) {
  const { order, token, profile } = route.params || {};
  const [rating, setRating] = useState(0);
  const [review, setReview] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRating = (value) => {
    setRating(value);
  };

  const handleSubmitRating = async () => {
    if (rating === 0) {
      Alert.alert('Rating Required', 'Please select a star rating.');
      return;
    }

    setLoading(true);

    try {
      await rateSupplier(token, order.id, rating, review);
      Alert.alert(
        'Thank You!',
        'Your rating has been submitted successfully.',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error) {
      Alert.alert('Submission Failed', error.message || 'Failed to submit rating. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backBtn}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Rate Supplier</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Order Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Order Summary</Text>
          <View style={styles.orderCard}>
            <View style={styles.orderHeader}>
              <Text style={styles.orderNumber}>#{order.order_number}</Text>
              <Text style={styles.orderDate}>
                {new Date(order.created_at).toLocaleDateString()}
              </Text>
            </View>
            <View style={styles.orderItems}>
              {order.items?.slice(0, 2).map((item, index) => (
                <View key={index} style={styles.orderItem}>
                  <Text style={styles.itemEmoji}>{item.product_type === 'machinery' ? '🚜' : '🌽'}</Text>
                  <View style={styles.itemInfo}>
                    <Text style={styles.itemName}>{item.product_name}</Text>
                    <Text style={styles.itemQuantity}>Qty: {item.quantity}</Text>
                  </View>
                  <Text style={styles.itemPrice}>${(item.price * item.quantity).toFixed(2)}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>

        {/* Supplier Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Supplier Information</Text>
          <View style={styles.supplierCard}>
            <View style={styles.supplierHeader}>
              <View style={styles.supplierAvatar}>
                <Package size={24} color={theme.colors.green} />
              </View>
              <View style={styles.supplierDetails}>
                <Text style={styles.supplierName}>{order.supplier_name || 'Supplier'}</Text>
                <View style={styles.supplierLocation}>
                  <MapPin size={14} color="#64748B" />
                  <Text style={styles.locationText}>{order.supplier_location || 'Zimbabwe'}</Text>
                </View>
              </View>
            </View>
            {order.verification_status === 'approved' && (
              <View style={styles.verifiedBadge}>
                <Shield size={14} color={theme.colors.green} />
                <Text style={styles.verifiedText}>Verified Supplier</Text>
              </View>
            )}
          </View>
        </View>

        {/* Rating */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Rate Your Experience</Text>
          <View style={styles.ratingContainer}>
            <Text style={styles.ratingPrompt}>
              How was your experience with this supplier?
            </Text>
            <View style={styles.starsContainer}>
              {[1, 2, 3, 4, 5].map((value) => (
                <TouchableOpacity
                  key={value}
                  onPress={() => handleRating(value)}
                  activeOpacity={0.7}
                >
                  <Star
                    size={36}
                    color={value <= rating ? '#F59E0B' : '#CBD5E1'}
                    fill={value <= rating ? '#F59E0B' : 'none'}
                  />
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.ratingLabel}>
              {rating === 0 ? 'Select a rating' : `${rating} star${rating > 1 ? 's' : ''}`}
            </Text>
          </View>
        </View>

        {/* Review */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Write a Review (Optional)</Text>
          <TextInput
            style={styles.reviewInput}
            placeholder="Share your experience with this supplier..."
            placeholderTextColor="#94A3B8"
            value={review}
            onChangeText={setReview}
            multiline
            numberOfLines={5}
            textAlignVertical="top"
            maxLength={500}
          />
          <Text style={styles.charCount}>{review.length}/500</Text>
        </View>

        {/* Rating Guidelines */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Rating Guidelines</Text>
          <View style={styles.guidelinesCard}>
            <View style={styles.guidelineItem}>
              <Star size={16} color="#F59E0B" fill="#F59E0B" />
              <Text style={styles.guidelineText}>5 stars - Excellent experience</Text>
            </View>
            <View style={styles.guidelineItem}>
              <Star size={16} color="#F59E0B" fill="#F59E0B" />
              <Text style={styles.guidelineText}>4 stars - Good experience</Text>
            </View>
            <View style={styles.guidelineItem}>
              <Star size={16} color="#F59E0B" fill="#F59E0B" />
              <Text style={styles.guidelineText}>3 stars - Average experience</Text>
            </View>
            <View style={styles.guidelineItem}>
              <Star size={16} color="#F59E0B" fill="#F59E0B" />
              <Text style={styles.guidelineText}>2 stars - Below average</Text>
            </View>
            <View style={styles.guidelineItem}>
              <Star size={16} color="#F59E0B" fill="#F59E0B" />
              <Text style={styles.guidelineText}>1 star - Poor experience</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Submit Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.submitButton, loading && styles.submitButtonDisabled]}
          onPress={handleSubmitRating}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Text style={styles.submitButtonText}>Submit Rating</Text>
              <Send size={20} color="#FFF" />
            </>
          )}
        </TouchableOpacity>
      </View>
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
  content: {
    flex: 1,
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
  orderCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 14,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  orderNumber: {
    fontSize: 15,
    fontWeight: '700',
    color: '#111827',
  },
  orderDate: {
    fontSize: 12,
    color: '#64748B',
  },
  orderItems: {
    gap: 8,
  },
  orderItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  itemEmoji: {
    fontSize: 24,
    marginRight: 12,
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111827',
  },
  itemQuantity: {
    fontSize: 11,
    color: '#64748B',
  },
  itemPrice: {
    fontSize: 13,
    fontWeight: '700',
    color: theme.colors.green,
  },
  supplierCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 14,
  },
  supplierHeader: {
    flexDirection: 'row',
    marginBottom: 12,
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
  supplierName: {
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
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 6,
    alignSelf: 'flex-start',
  },
  verifiedText: {
    fontSize: 12,
    fontWeight: '700',
    color: theme.colors.green,
  },
  ratingContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  ratingPrompt: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 20,
  },
  starsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  ratingLabel: {
    fontSize: 14,
    color: '#64748B',
  },
  reviewInput: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 14,
    fontSize: 15,
    color: '#111827',
    minHeight: 120,
  },
  charCount: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'right',
    marginTop: 8,
  },
  guidelinesCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 14,
  },
  guidelineItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  guidelineText: {
    fontSize: 13,
    color: '#475569',
  },
  footer: {
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  submitButton: {
    backgroundColor: theme.colors.green,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '800',
  },
});
