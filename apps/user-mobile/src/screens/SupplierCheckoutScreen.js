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
import { MapPin, Truck, CreditCard, CheckCircle, AlertCircle } from 'lucide-react-native';
import { theme } from '../styles';
import { createSupplierOrder, getWalletBalance } from '../api';

export default function SupplierCheckoutScreen({ navigation, route }) {
  const { cart, total, token, profile } = route.params || {};
  const [loading, setLoading] = useState(false);
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [deliveryPhone, setDeliveryPhone] = useState(profile?.phone_number || '');
  const [shippingMethod, setShippingMethod] = useState('standard');
  const [buyerNotes, setBuyerNotes] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('wallet');
  const [walletBalance, setWalletBalance] = useState(0);
  const [platformFee] = useState(total * 0.03);
  const [grandTotal] = useState(total * 1.03);

  const shippingOptions = [
    { id: 'standard', name: 'Standard Delivery (5-7 days)', cost: 0 },
    { id: 'express', name: 'Express Delivery (2-3 days)', cost: 15 },
    { id: 'pickup', name: 'Self Pickup (Free)', cost: 0 },
  ];

  const loadWalletBalance = async () => {
    try {
      const balance = await getWalletBalance(token);
      setWalletBalance(balance.available_usd || 0);
    } catch (error) {
      console.error('Failed to load wallet balance:', error);
    }
  };

  React.useEffect(() => {
    loadWalletBalance();
  }, []);

  const handlePlaceOrder = async () => {
    if (!deliveryAddress.trim()) {
      Alert.alert('Missing Information', 'Please enter a delivery address.');
      return;
    }

    if (!deliveryPhone.trim()) {
      Alert.alert('Missing Information', 'Please enter a delivery phone number.');
      return;
    }

    if (paymentMethod === 'wallet' && walletBalance < grandTotal) {
      Alert.alert('Insufficient Balance', 'Please top up your wallet or choose another payment method.');
      return;
    }

    setLoading(true);

    try {
      const orderData = {
        items: cart.map(item => ({
          product_id: item.id,
          quantity: item.quantity,
        })),
        delivery_address: deliveryAddress,
        delivery_phone: deliveryPhone,
        shipping_method: shippingMethod,
        buyer_notes: buyerNotes,
      };

      const response = await createSupplierOrder(token, orderData);

      // Clear cart
      localStorage.removeItem('supplierCart');

      Alert.alert(
        'Order Placed Successfully!',
        `Order #${response.order_number}\nYour order has been placed and will be processed soon.`,
        [
          {
            text: 'View Orders',
            onPress: () => navigation.replace('MyOrders', { token, profile }),
          },
        ]
      );
    } catch (error) {
      Alert.alert('Order Failed', error.message || 'Failed to place order. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backBtn}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Checkout</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Order Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Order Summary</Text>
          {cart.map((item) => (
            <View key={item.id} style={styles.orderItem}>
              <View style={styles.itemLeft}>
                <Text style={styles.itemEmoji}>{item.product_type === 'machinery' ? '🚜' : '🌽'}</Text>
                <View>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemQuantity}>Qty: {item.quantity}</Text>
                </View>
              </View>
              <Text style={styles.itemPrice}>${(item.price * item.quantity).toFixed(2)}</Text>
            </View>
          ))}
        </View>

        {/* Delivery Address */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Delivery Address</Text>
          <View style={styles.inputContainer}>
            <MapPin size={20} color="#64748B" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Enter your delivery address"
              placeholderTextColor="#94A3B8"
              value={deliveryAddress}
              onChangeText={setDeliveryAddress}
              multiline
              numberOfLines={3}
            />
          </View>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="Delivery phone number"
              placeholderTextColor="#94A3B8"
              value={deliveryPhone}
              onChangeText={setDeliveryPhone}
              keyboardType="phone-pad"
            />
          </View>
        </View>

        {/* Shipping Method */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Shipping Method</Text>
          {shippingOptions.map((option) => (
            <TouchableOpacity
              key={option.id}
              style={[
                styles.shippingOption,
                shippingMethod === option.id && styles.shippingOptionActive,
              ]}
              onPress={() => setShippingMethod(option.id)}
            >
              <View style={styles.shippingLeft}>
                <Truck size={20} color={shippingMethod === option.id ? theme.colors.green : '#64748B'} />
                <View>
                  <Text style={[
                    styles.shippingName,
                    shippingMethod === option.id && styles.shippingNameActive,
                  ]}>
                    {option.name}
                  </Text>
                  <Text style={styles.shippingCost}>
                    {option.cost === 0 ? 'Free' : `$${option.cost.toFixed(2)}`}
                  </Text>
                </View>
              </View>
              {shippingMethod === option.id && (
                <CheckCircle size={20} color={theme.colors.green} />
              )}
            </TouchableOpacity>
          ))}
        </View>

        {/* Payment Method */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Payment Method</Text>
          <TouchableOpacity
            style={[styles.paymentOption, paymentMethod === 'wallet' && styles.paymentOptionActive]}
            onPress={() => setPaymentMethod('wallet')}
          >
            <View style={styles.paymentLeft}>
              <CreditCard size={20} color={paymentMethod === 'wallet' ? theme.colors.green : '#64748B'} />
              <View>
                <Text style={[
                  styles.paymentName,
                  paymentMethod === 'wallet' && styles.paymentNameActive,
                ]}>
                  Wallet Balance
                </Text>
                <Text style={styles.paymentBalance}>Available: ${walletBalance.toFixed(2)}</Text>
              </View>
            </View>
            {paymentMethod === 'wallet' && (
              <CheckCircle size={20} color={theme.colors.green} />
            )}
          </TouchableOpacity>
          {paymentMethod === 'wallet' && walletBalance < grandTotal && (
            <View style={styles.warningBanner}>
              <AlertCircle size={16} color="#F59E0B" />
              <Text style={styles.warningText}>
                Insufficient balance. Please top up your wallet.
              </Text>
            </View>
          )}
        </View>

        {/* Additional Notes */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Additional Notes (Optional)</Text>
          <TextInput
            style={styles.textArea}
            placeholder="Add any special instructions for the supplier..."
            placeholderTextColor="#94A3B8"
            value={buyerNotes}
            onChangeText={setBuyerNotes}
            multiline
            numberOfLines={4}
          />
        </View>

        {/* Price Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Price Summary</Text>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Subtotal</Text>
            <Text style={styles.summaryValue}>${total.toFixed(2)}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Platform Fee (3%)</Text>
            <Text style={styles.summaryValue}>${platformFee.toFixed(2)}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Shipping</Text>
            <Text style={styles.summaryValue}>
              ${shippingOptions.find(o => o.id === shippingMethod)?.cost || 0}
            </Text>
          </View>
          <View style={[styles.summaryRow, styles.totalRow]}>
            <Text style={styles.totalLabel}>Total</Text>
            <Text style={styles.totalValue}>${grandTotal.toFixed(2)}</Text>
          </View>
        </View>
      </ScrollView>

      {/* Place Order Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.placeOrderButton, loading && styles.placeOrderButtonDisabled]}
          onPress={handlePlaceOrder}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.placeOrderButtonText}>Place Order • ${grandTotal.toFixed(2)}</Text>
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
    paddingBottom: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#64748B',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  orderItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
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
  itemQuantity: {
    fontSize: 12,
    color: '#64748B',
  },
  itemPrice: {
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.green,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 12,
    paddingHorizontal: 12,
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    paddingVertical: 14,
    fontSize: 15,
    color: '#111827',
  },
  textArea: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 14,
    fontSize: 15,
    color: '#111827',
    minHeight: 100,
  },
  shippingOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 8,
  },
  shippingOptionActive: {
    backgroundColor: '#F0FDF4',
    borderColor: theme.colors.green,
  },
  shippingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  shippingName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 12,
  },
  shippingNameActive: {
    color: theme.colors.green,
  },
  shippingCost: {
    fontSize: 12,
    color: '#64748B',
    marginLeft: 12,
  },
  paymentOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  paymentOptionActive: {
    backgroundColor: '#F0FDF4',
    borderColor: theme.colors.green,
  },
  paymentLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  paymentName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 12,
  },
  paymentNameActive: {
    color: theme.colors.green,
  },
  paymentBalance: {
    fontSize: 12,
    color: '#64748B',
    marginLeft: 12,
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFBEB',
    borderRadius: 8,
    padding: 10,
    marginTop: 8,
  },
  warningText: {
    fontSize: 12,
    color: '#B45309',
    marginLeft: 8,
    flex: 1,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#64748B',
  },
  summaryValue: {
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
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '900',
    color: theme.colors.green,
  },
  footer: {
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 32,
  },
  placeOrderButton: {
    backgroundColor: theme.colors.green,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  placeOrderButtonDisabled: {
    opacity: 0.6,
  },
  placeOrderButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '800',
  },
});
