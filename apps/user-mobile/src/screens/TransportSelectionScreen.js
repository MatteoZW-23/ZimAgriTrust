import React, { useState, useEffect } from "react";
import { Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet, Alert, ActivityIndicator } from "react-native";
import { theme } from "../styles";
import { appStyles } from "../styles";

const TRANSPORT_MODES = [
  {
    id: 'PLATFORM_DELIVERY_BUYER_REQUESTED',
    label: 'Platform Delivery (I Pay)',
    description: 'ZimAgriTrust driver delivers. You pay transport fee.',
    icon: '🚚',
    color: '#EFF6FF',
    payer: 'BUYER',
  },
  {
    id: 'PLATFORM_DELIVERY_FARMER_REQUESTED',
    label: 'Platform Delivery (Farmer Pays)',
    description: 'ZimAgriTrust driver delivers. Farmer pays transport fee.',
    icon: '🚚',
    color: '#F0FDF4',
    payer: 'FARMER',
  },
  {
    id: 'SELF_PICKUP',
    label: 'Self Pickup',
    description: 'I will collect directly from the farmer.',
    icon: '📦',
    color: '#FEF2F2',
    payer: 'NONE',
  },
  {
    id: 'SELF_DELIVERY',
    label: 'Farmer Delivery',
    description: 'Farmer will deliver directly to me.',
    icon: '🚜',
    color: '#FFF7ED',
    payer: 'NONE',
  },
  {
    id: 'NEGOTIATED_TRANSPORT',
    label: 'Negotiate Transport',
    description: 'Discuss transport fee and payment responsibility with farmer.',
    icon: '💬',
    color: '#F5F3FF',
    payer: 'NEGOTIATED',
  },
  {
    id: 'DEFERRED',
    label: 'Decide Later',
    description: 'Let the other party decide transport method.',
    icon: '⏳',
    color: '#F3F4F6',
    payer: 'DEFERRED',
  },
];

const VEHICLE_TYPES = [
  { id: 'motorcycle', label: 'Motorcycle', icon: '🏍️', capacity: '50kg' },
  { id: 'car', label: 'Car', icon: '🚗', capacity: '200kg' },
  { id: 'van', label: 'Van', icon: '🚐', capacity: '500kg' },
  { id: 'truck', label: 'Truck', icon: '🚛', capacity: '1000kg+' },
];

export default function TransportSelectionScreen({ navigation, route }) {
  const { role = 'buyer', token, orderDetails, listing } = route.params || {};
  
  const [selectedMode, setSelectedMode] = useState(null);
  const [selectedVehicle, setSelectedVehicle] = useState('van');
  const [pickupAddress, setPickupAddress] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [urgency, setUrgency] = useState('STANDARD');
  const [loading, setLoading] = useState(false);
  const [quote, setQuote] = useState(null);
  const [calculatingQuote, setCalculatingQuote] = useState(false);

  const handleModeSelect = (mode) => {
    setSelectedMode(mode);
    setQuote(null);
  };

  const handleCalculateQuote = async () => {
    if (!pickupAddress || !deliveryAddress) {
      Alert.alert('Missing Information', 'Please enter pickup and delivery addresses.');
      return;
    }

    setCalculatingQuote(true);
    try {
      // TODO: Call API to calculate distance and quote
      // For now, simulate quote
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setQuote({
        distance_km: 15.5,
        base_fee: 5.00,
        distance_fee: 6.98,
        weight_fee: 0.00,
        urgency_fee: 0.00,
        subtotal: 11.98,
        tax_amount: 1.80,
        total_amount: 13.78,
        estimated_minutes: 45,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to calculate quote. Please try again.');
    } finally {
      setCalculatingQuote(false);
    }
  };

  const handleConfirm = async () => {
    if (!selectedMode) {
      Alert.alert('Selection Required', 'Please select a transport mode.');
      return;
    }

    if (selectedMode === 'PLATFORM_DELIVERY_BUYER_REQUESTED' || 
        selectedMode === 'PLATFORM_DELIVERY_FARMER_REQUESTED') {
      if (!pickupAddress || !deliveryAddress) {
        Alert.alert('Missing Information', 'Please enter pickup and delivery addresses.');
        return;
      }
    }

    setLoading(true);
    try {
      // TODO: Call API to request transport
      const payload = {
        order_id: orderDetails?.id,
        requested_by: role === 'buyer' ? 'BUYER' : 'FARMER',
        mode: selectedMode,
        pickup_address: pickupAddress,
        delivery_address: deliveryAddress,
        vehicle_type: selectedVehicle,
        urgency_level: urgency,
        cargo_weight_kg: listing?.quantity || 100,
      };

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      Alert.alert('Success', 'Transport request submitted successfully.', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to submit transport request.');
    } finally {
      setLoading(false);
    }
  };

  const getTransportFeePayer = (mode) => {
    const modeData = TRANSPORT_MODES.find(m => m.id === mode);
    return modeData?.payer || 'UNKNOWN';
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Select Transport Method</Text>
        <Text style={styles.subtitle}>
          Choose how you want the goods to be delivered
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Transport Options</Text>
        {TRANSPORT_MODES.map((mode) => (
          <TouchableOpacity
            key={mode.id}
            style={[
              styles.modeCard,
              selectedMode === mode.id && styles.modeCardSelected,
              { backgroundColor: mode.color }
            ]}
            onPress={() => handleModeSelect(mode.id)}
          >
            <View style={styles.modeCardHeader}>
              <Text style={styles.modeIcon}>{mode.icon}</Text>
              <View style={styles.modeCardTitleContainer}>
                <Text style={styles.modeTitle}>{mode.label}</Text>
                <Text style={styles.modeDescription}>{mode.description}</Text>
              </View>
              {selectedMode === mode.id && (
                <View style={styles.checkmark}>
                  <Text style={styles.checkmarkText}>✓</Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {(selectedMode === 'PLATFORM_DELIVERY_BUYER_REQUESTED' || 
        selectedMode === 'PLATFORM_DELIVERY_FARMER_REQUESTED') && (
        <>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Delivery Details</Text>
            
            <Text style={styles.label}>Pickup Address</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter pickup address"
              value={pickupAddress}
              onChangeText={setPickupAddress}
            />

            <Text style={styles.label}>Delivery Address</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter delivery address"
              value={deliveryAddress}
              onChangeText={setDeliveryAddress}
            />

            <Text style={styles.label}>Vehicle Type</Text>
            <View style={styles.vehicleGrid}>
              {VEHICLE_TYPES.map((vehicle) => (
                <TouchableOpacity
                  key={vehicle.id}
                  style={[
                    styles.vehicleCard,
                    selectedVehicle === vehicle.id && styles.vehicleCardSelected,
                  ]}
                  onPress={() => setSelectedVehicle(vehicle.id)}
                >
                  <Text style={styles.vehicleIcon}>{vehicle.icon}</Text>
                  <Text style={styles.vehicleLabel}>{vehicle.label}</Text>
                  <Text style={styles.vehicleCapacity}>{vehicle.capacity}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.label}>Urgency</Text>
            <View style={styles.urgencyOptions}>
              {['STANDARD', 'URGENT', 'EXPEDITED'].map((level) => (
                <TouchableOpacity
                  key={level}
                  style={[
                    styles.urgencyButton,
                    urgency === level && styles.urgencyButtonSelected,
                  ]}
                  onPress={() => setUrgency(level)}
                >
                  <Text style={[
                    styles.urgencyText,
                    urgency === level && styles.urgencyTextSelected,
                  ]}>
                    {level}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity
              style={styles.calculateButton}
              onPress={handleCalculateQuote}
              disabled={calculatingQuote}
            >
              {calculatingQuote ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.calculateButtonText}>Calculate Quote</Text>
              )}
            </TouchableOpacity>
          </View>

          {quote && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Transport Quote</Text>
              <View style={styles.quoteCard}>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Distance:</Text>
                  <Text style={styles.quoteValue}>{quote.distance_km} km</Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Base Fee:</Text>
                  <Text style={styles.quoteValue}>${quote.base_fee.toFixed(2)}</Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Distance Fee:</Text>
                  <Text style={styles.quoteValue}>${quote.distance_fee.toFixed(2)}</Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Subtotal:</Text>
                  <Text style={styles.quoteValue}>${quote.subtotal.toFixed(2)}</Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Tax (15%):</Text>
                  <Text style={styles.quoteValue}>${quote.tax_amount.toFixed(2)}</Text>
                </View>
                <View style={[styles.quoteRow, styles.quoteRowTotal]}>
                  <Text style={styles.quoteLabelTotal}>Total:</Text>
                  <Text style={styles.quoteValueTotal}>${quote.total_amount.toFixed(2)}</Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Estimated Time:</Text>
                  <Text style={styles.quoteValue}>{quote.estimated_minutes} min</Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Paid By:</Text>
                  <Text style={styles.quoteValue}>
                    {getTransportFeePayer(selectedMode) === 'BUYER' ? 'You (Buyer)' : 'Farmer'}
                  </Text>
                </View>
              </View>
            </View>
          )}
        </>
      )}

      {selectedMode === 'NEGOTIATED_TRANSPORT' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Negotiation Details</Text>
          <View style={styles.infoCard}>
            <Text style={styles.infoText}>
              You will enter a negotiation with the {role === 'buyer' ? 'farmer' : 'buyer'} 
              to discuss the transport fee and payment responsibility.
            </Text>
            <Text style={styles.infoText}>
              • Negotiation window: 72 hours
            </Text>
            <Text style={styles.infoText}>
              • Support for split payments
            </Text>
            <Text style={styles.infoText}>
              • Real-time chat available
            </Text>
          </View>
        </View>
      )}

      {selectedMode === 'DEFERRED' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Deferred Decision</Text>
          <View style={styles.infoCard}>
            <Text style={styles.infoText}>
              The {role === 'buyer' ? 'farmer' : 'buyer'} will have 48 hours to choose a transport method.
            </Text>
            <Text style={styles.infoText}>
              If no decision is made, the system will automatically assign platform delivery.
            </Text>
          </View>
        </View>
      )}

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.confirmButton, !selectedMode && styles.confirmButtonDisabled]}
          onPress={handleConfirm}
          disabled={!selectedMode || loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.confirmButtonText}>Confirm Transport</Text>
          )}
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  section: {
    padding: 20,
    marginTop: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 16,
  },
  modeCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  modeCardSelected: {
    borderColor: '#3B82F6',
  },
  modeCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  modeIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  modeCardTitleContainer: {
    flex: 1,
  },
  modeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 4,
  },
  modeDescription: {
    fontSize: 13,
    color: '#6B7280',
  },
  checkmark: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#3B82F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmarkText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    marginBottom: 16,
  },
  vehicleGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  vehicleCard: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    marginRight: 8,
    marginBottom: 8,
    alignItems: 'center',
    width: 80,
  },
  vehicleCardSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#EFF6FF',
  },
  vehicleIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  vehicleLabel: {
    fontSize: 12,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 2,
  },
  vehicleCapacity: {
    fontSize: 10,
    color: '#6B7280',
  },
  urgencyOptions: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  urgencyButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
    marginRight: 8,
  },
  urgencyButtonSelected: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  urgencyText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#374151',
  },
  urgencyTextSelected: {
    color: '#fff',
  },
  calculateButton: {
    backgroundColor: '#6B7280',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
    marginBottom: 16,
  },
  calculateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  quoteCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  quoteRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  quoteRowTotal: {
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingTop: 8,
    marginTop: 8,
  },
  quoteLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  quoteLabelTotal: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  quoteValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1F2937',
  },
  quoteValueTotal: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#3B82F6',
  },
  infoCard: {
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  infoText: {
    fontSize: 14,
    color: '#92400E',
    marginBottom: 8,
  },
  footer: {
    padding: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  confirmButton: {
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  confirmButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  cancelButton: {
    backgroundColor: 'transparent',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#6B7280',
    fontSize: 16,
    fontWeight: '500',
  },
});
