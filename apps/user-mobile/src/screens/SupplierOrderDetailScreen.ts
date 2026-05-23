import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { ArrowLeft, Package, Truck, CheckCircle, Clock, XCircle, MapPin, Phone, MessageSquare, Star, AlertCircle } from 'lucide-react-native';
import { theme } from '../styles';
import { confirmSupplierOrderReceipt } from '../api';

export default function SupplierOrderDetailScreen({ navigation, route }) {
  const { order, token, profile } = route.params || {};
  const [loading, setLoading] = useState(false);

  const handleConfirmReceipt = async () => {
    Alert.alert(
      'Confirm Receipt',
      'Have you received your order? This will release payment to the supplier.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          style: 'destructive',
          onPress: async () => {
            setLoading(true);
            try {
              await confirmSupplierOrderReceipt(token, order.id);
              Alert.alert('Success', 'Receipt confirmed. Payment will be released to the supplier.', [
                { text: 'OK', onPress: () => navigation.goBack() }
              ]);
            } catch (error) {
              Alert.alert('Error', error.message || 'Failed to confirm receipt.');
            } finally {
              setLoading(false);
            }
          }
        }
      ]
    );
  };

  const handleRateSupplier = () => {
    navigation.navigate('RateSupplier', { order, token, profile });
  };

  const handleContactSupplier = () => {
    navigation.navigate('Chat', { supplierId: order.supplier_id, token, profile });
  };

  const getStatusInfo = (status) => {
    switch (status) {
      case 'pending':
        return { icon: <Clock size={20} color="#F59E0B" />, color: '#F59E0B', label: 'Pending Confirmation' };
      case 'confirmed':
        return { icon: <CheckCircle size={20} color={theme.colors.green} />, color: theme.colors.green, label: 'Confirmed' };
      case 'shipped':
        return { icon: <Truck size={20} color="#3B82F6" />, color: '#3B82F6', label: 'Shipped' };
      case 'delivered':
        return { icon: <Package size={20} color={theme.colors.green} />, color: theme.colors.green, label: 'Delivered' };
      case 'completed':
        return { icon: <CheckCircle size={20} color="#10B981" />, color: '#10B981', label: 'Completed' };
      case 'cancelled':
        return { icon: <XCircle size={20} color="#EF4444" />, color: '#EF4444', label: 'Cancelled' };
      default:
        return { icon: <AlertCircle size={20} color="#64748B" />, color: '#64748B', label: 'Unknown' };
    }
  };

  const statusInfo = getStatusInfo(order.status);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <ArrowLeft size={24} color={theme.colors.black} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Order Details</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Status Card */}
        <View style={styles.statusCard}>
          <View style={[styles.statusIcon, { backgroundColor: statusInfo.color + '20' }]}>
            {statusInfo.icon}
          </View>
          <Text style={[styles.statusText, { color: statusInfo.color }]}>
            {statusInfo.label}
          </Text>
          <Text style={styles.orderNumber}>#{order.order_number}</Text>
          <Text style={styles.orderDate}>
            Placed on {new Date(order.created_at).toLocaleDateString()}
          </Text>
        </View>

        {/* Order Items */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Order Items</Text>
          <View style={styles.itemsCard}>
            {order.items?.map((item, index) => (
              <View key={index} style={styles.itemRow}>
                <View style={styles.itemLeft}>
                  <Text style={styles.itemEmoji}>{item.product_type === 'machinery' ? '🚜' : '🌽'}</Text>
                  <View>
                    <Text style={styles.itemName}>{item.product_name}</Text>
                    <Text style={styles.itemSku}>SKU: {item.sku || 'N/A'}</Text>
                  </View>
                </View>
                <View style={styles.itemRight}>
                  <Text style={styles.itemQuantity}>x{item.quantity}</Text>
                  <Text style={styles.itemPrice}>${(item.price * item.quantity).toFixed(2)}</Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* Delivery Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Delivery Information</Text>
          <View style={styles.deliveryCard}>
            <View style={styles.deliveryRow}>
              <MapPin size={18} color="#64748B" />
              <View style={styles.deliveryInfo}>
                <Text style={styles.deliveryLabel}>Delivery Address</Text>
                <Text style={styles.deliveryValue}>{order.delivery_address}</Text>
              </View>
            </View>
            <View style={styles.deliveryRow}>
              <Phone size={18} color="#64748B" />
              <View style={styles.deliveryInfo}>
                <Text style={styles.deliveryLabel}>Contact Phone</Text>
                <Text style={styles.deliveryValue}>{order.delivery_phone}</Text>
              </View>
            </View>
            <View style={styles.deliveryRow}>
              <Truck size={18} color="#64748B" />
              <View style={styles.deliveryInfo}>
                <Text style={styles.deliveryLabel}>Shipping Method</Text>
                <Text style={styles.deliveryValue}>{order.shipping_method || 'Standard'}</Text>
              </View>
            </View>
            {order.tracking_number && (
              <View style={styles.deliveryRow}>
                <Package size={18} color="#64748B" />
                <View style={styles.deliveryInfo}>
                  <Text style={styles.deliveryLabel}>Tracking Number</Text>
                  <Text style={styles.deliveryValue}>{order.tracking_number}</Text>
                </View>
              </View>
            )}
          </View>
        </View>

        {/* Supplier Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Supplier Information</Text>
          <View style={styles.supplierCard}>
            <View style={styles.supplierHeader}>
              <View style={styles.supplierAvatar}>
                <Package size={24} color={theme.colors.green} />
              </View>
              <View style={styles.supplierDetails}>
                <Text style={styles.supplierName}>{order.supplier_name || 'Supplier'}</Text>
                {order.supplier_location && (
                  <View style={styles.supplierLocation}>
                    <MapPin size={14} color="#64748B" />
                    <Text style={styles.locationText}>{order.supplier_location}</Text>
                  </View>
                )}
              </View>
            </View>
            <View style={styles.supplierActions}>
              <TouchableOpacity style={styles.contactButton} onPress={handleContactSupplier}>
                <MessageSquare size={18} color={theme.colors.green} />
                <Text style={styles.contactButtonText}>Message</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.contactButton}>
                <Phone size={18} color={theme.colors.green} />
                <Text style={styles.contactButtonText}>Call</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Payment Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Payment Summary</Text>
          <View style={styles.paymentCard}>
            <View style={styles.paymentRow}>
              <Text style={styles.paymentLabel}>Subtotal</Text>
              <Text style={styles.paymentValue}>${order.subtotal?.toFixed(2) || '0.00'}</Text>
            </View>
            <View style={styles.paymentRow}>
              <Text style={styles.paymentLabel}>Platform Fee (3%)</Text>
              <Text style={styles.paymentValue}>${order.platform_fee?.toFixed(2) || '0.00'}</Text>
            </View>
            <View style={styles.paymentRow}>
              <Text style={styles.paymentLabel}>Shipping</Text>
              <Text style={styles.paymentValue}>${order.shipping_cost?.toFixed(2) || '0.00'}</Text>
            </View>
            <View style={[styles.paymentRow, styles.totalRow]}>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={styles.totalValue}>${order.total_amount?.toFixed(2) || '0.00'}</Text>
            </View>
            <View style={styles.escrowBadge}>
              <AlertCircle size={14} color="#F59E0B" />
              <Text style={styles.escrowText}>
                Payment held in escrow until delivery confirmation
              </Text>
            </View>
          </View>
        </View>

        {/* Notes */}
        {order.buyer_notes && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Order Notes</Text>
            <View style={styles.notesCard}>
              <Text style={styles.notesText}>{order.buyer_notes}</Text>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Footer Actions */}
      <View style={styles.footer}>
        {order.status === 'delivered' && (
          <>
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={handleConfirmReceipt}
              disabled={loading}
            >
              <Text style={styles.primaryButtonText}>Confirm Receipt</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.secondaryButton}
              onPress={handleRateSupplier}
            >
              <Star size={18} color={theme.colors.gold} />
              <Text style={styles.secondaryButtonText}>Rate Supplier</Text>
            </TouchableOpacity>
          </>
        )}
        {order.status === 'completed' && (
          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={handleRateSupplier}
          >
            <Star size={18} color={theme.colors.gold} />
            <Text style={styles.secondaryButtonText}>Rate Supplier</Text>
          </TouchableOpacity>
        )}
        {order.status === 'confirmed' || order.status === 'shipped' ? (
          <TouchableOpacity style={styles.contactButtonFull} onPress={handleContactSupplier}>
            <MessageSquare size={18} color={theme.colors.green} />
            <Text style={styles.contactButtonFullText}>Contact Supplier</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F0DE',
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: theme.colors.black,
  },
  content: {
    flex: 1,
  },
  statusCard: {
    backgroundColor: '#FFF',
    padding: 24,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  statusIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  statusText: {
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 8,
  },
  orderNumber: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 4,
  },
  orderDate: {
    fontSize: 12,
    color: '#94A3B8',
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
  itemsCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 14,
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  itemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  itemEmoji: {
    fontSize: 28,
    marginRight: 12,
  },
  itemName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  itemSku: {
    fontSize: 11,
    color: '#64748B',
  },
  itemRight: {
    alignItems: 'flex-end',
  },
  itemQuantity: {
    fontSize: 12,
    color: '#64748B',
  },
  itemPrice: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.green,
  },
  deliveryCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 14,
  },
  deliveryRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  deliveryInfo: {
    marginLeft: 12,
    flex: 1,
  },
  deliveryLabel: {
    fontSize: 11,
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  deliveryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  supplierCard: {
    backgroundColor: '#FFF',
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
  supplierActions: {
    flexDirection: 'row',
    gap: 8,
  },
  contactButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F0FDF4',
    paddingVertical: 10,
    borderRadius: 8,
    gap: 6,
  },
  contactButtonText: {
    fontSize: 13,
    fontWeight: '700',
    color: theme.colors.green,
  },
  paymentCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 14,
  },
  paymentRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  paymentLabel: {
    fontSize: 13,
    color: '#64748B',
  },
  paymentValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  totalRow: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  totalLabel: {
    fontSize: 15,
    fontWeight: '800',
    color: '#111827',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '900',
    color: theme.colors.green,
  },
  escrowBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFBEB',
    borderRadius: 8,
    padding: 10,
    marginTop: 12,
    gap: 8,
  },
  escrowText: {
    fontSize: 12,
    color: '#B45309',
    flex: 1,
  },
  notesCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 14,
  },
  notesText: {
    fontSize: 14,
    color: '#475569',
    lineHeight: 22,
  },
  footer: {
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
  },
  primaryButton: {
    backgroundColor: theme.colors.green,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#FFF',
    fontSize: 15,
    fontWeight: '800',
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  contactButtonFull: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: theme.colors.green,
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  contactButtonFullText: {
    fontSize: 15,
    fontWeight: '800',
    color: theme.colors.green,
  },
});
