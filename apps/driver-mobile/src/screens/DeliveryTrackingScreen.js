import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView,
  Alert, Image, Modal, TextInput, ActivityIndicator, Share, Platform,
} from 'react-native';
import {
  ArrowLeft as IconArrowLeft, MapPin as IconMapPin, 
  CheckCircle as IconCheckCircle, Truck as IconTruck, 
  Package as IconPackage, Camera as IconCamera, Phone as IconPhone,
  Navigation as IconNavigation, Upload as IconUpload, 
  MessageSquare as IconMessageSquare, AlertTriangle as IconAlertTriangle, 
  User as IconUser, Clock as IconClock,
  X as IconX, Wheat as IconWheat, DollarSign as IconDollarSign,
} from 'lucide-react-native';
import { theme } from '../styles';
import { updateDeliveryStatus, submitDeliveryProof, reportIssue, confirmPickup, confirmDelivery } from '../api';
import LocationTracker from '../utils/locationTracker';

const STEPS = [
  { key: 'pending', label: 'Job Accepted', icon: IconCheckCircle },
  { key: 'picked_up', label: 'Cargo Picked Up', icon: IconPackage },
  { key: 'in_transit', label: 'In Transit', icon: IconTruck },
  { key: 'delivered', label: 'Delivered', icon: IconMapPin },
];

export default function DeliveryTrackingScreen({ route, navigation }) {
  const { delivery = {}, token } = route.params || {};
  const [status, setStatus] = useState(delivery.status || 'pending');
  const [updating, setUpdating] = useState(false);
  const [showProofModal, setShowProofModal] = useState(false);
  const [showIssueModal, setShowIssueModal] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [notes, setNotes] = useState('');
  const [signature, setSignature] = useState(null);
  const [issueType, setIssueType] = useState('');
  const [issueDescription, setIssueDescription] = useState('');
  const [locationStatus, setLocationStatus] = useState({});
  const mapRef = useRef(null);

  const currentIdx = STEPS.findIndex(s => s.key === status);

  useEffect(() => {
    // Initialize location tracking for this delivery
    if (status === 'in_transit') {
      LocationTracker.startTracking(token);
      setLocationStatus(LocationTracker.getTrackingStatus());
    }
    
    return () => {
      LocationTracker.stopTracking();
    };
  }, [status, token]);

  const handleUpdateStatus = async (newStatus) => {
    setUpdating(true);
    try {
      if (newStatus === 'picked_up') {
        // If it's pickup, we ideally want a photo, but we can also just update status
        await updateDeliveryStatus(token, delivery.id, 'PICKUP_DONE');
      } else if (newStatus === 'in_transit') {
        await updateDeliveryStatus(token, delivery.id, 'IN_TRANSIT');
        LocationTracker.startTracking(token);
      } else {
        await updateDeliveryStatus(token, delivery.id, newStatus.toUpperCase());
      }
      
      setStatus(newStatus);
      
      if (newStatus === 'delivered') {
        setShowProofModal(true); // Open proof modal automatically
      }
    } catch (err) {
      Alert.alert('Error', err.message || 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  const handleTakePhoto = async () => {
    if (Platform.OS === 'web') {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          setPhotos(prev => [...prev, { uri: URL.createObjectURL(file), name: file.name, type: file.type }]);
        }
      };
      input.click();
      return;
    }
    try {
      const ImagePicker = require('expo-image-picker');
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });
      if (!result.canceled) {
        setPhotos(prev => [...prev, result.assets[0]]);
      }
    } catch (error) {
      Alert.alert('Camera Error', 'Could not open camera. Please try again.');
    }
  };

  const handleCaptureSignature = async () => {
    // In a real app, this would open a signature pad
    Alert.alert('Signature', 'Signature capture feature would open here');
  };

  const handleSubmitProof = async () => {
    if (photos.length === 0) {
      Alert.alert('Error', 'Please take at least one photo');
      return;
    }

    try {
      setUpdating(true);
      const photoBase64 = photos[0].uri; // In real app, convert to base64
      const signatureBase64 = signature ? signature.uri : null;

      if (status === 'picked_up' || status === 'pending') {
        await confirmPickup(token, delivery.id, photoBase64);
        setStatus('picked_up');
      } else {
        await confirmDelivery(token, delivery.id, photoBase64, signatureBase64);
        setStatus('completed');
      }
      
      setShowProofModal(false);
      setPhotos([]);
      setNotes('');
      setSignature(null);
      
      Alert.alert('Success', 'Delivery proof submitted successfully');
    } catch (error) {
      console.error('Failed to submit proof:', error);
      Alert.alert('Error', 'Failed to submit delivery proof');
    } finally {
      setUpdating(false);
    }
  };

  const handleReportIssue = async () => {
    if (!issueType || !issueDescription) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    try {
      setUpdating(true);
      await reportIssue(token, delivery.id, issueType, issueDescription, photos);
      
      setShowIssueModal(false);
      setIssueType('');
      setIssueDescription('');
      setPhotos([]);
      
      Alert.alert('Success', 'Issue reported successfully');
    } catch (error) {
      console.error('Failed to report issue:', error);
      Alert.alert('Error', 'Failed to report issue');
    } finally {
      setUpdating(false);
    }
  };

  const handleShareLocation = async () => {
    const currentLocation = LocationTracker.getLastLocation();
    if (currentLocation) {
      try {
        await Share.share({
          message: `My current location: https://maps.google.com/?q=${currentLocation.latitude},${currentLocation.longitude}`,
        });
      } catch (error) {
        console.error('Failed to share location:', error);
      }
    } else {
      Alert.alert('Error', 'Location not available');
    }
  };

  const handleCallCustomer = () => {
    // In a real app, this would make a phone call
    Alert.alert('Call Customer', `Would call ${delivery.customer_phone || 'customer'}`);
  };

  const handleNavigate = () => {
    // In a real app, this would open navigation app
    const currentLocation = LocationTracker.getLastLocation();
    if (currentLocation && delivery.delivery_location_coords) {
      const url = `https://maps.google.com/maps/dir/${currentLocation.latitude},${currentLocation.longitude}/${delivery.delivery_location_coords.latitude},${delivery.delivery_location_coords.longitude}`;
      console.log('Navigate to:', url);
    }
  };

  const nextStep = STEPS[currentIdx + 1];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <IconArrowLeft size={22} color={theme.colors.dark} />
        </TouchableOpacity>
        <Text style={styles.topTitle}>Delivery Tracking</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 120 }}>
        {/* Route Card */}
        <View style={styles.routeCard}>
          <View style={styles.routeRow}>
            <View style={[styles.dot, { backgroundColor: theme.colors.sky }]} />
            <Text style={styles.routeText} numberOfLines={1}>{delivery.pickup_location || 'Pickup'}</Text>
          </View>
          <View style={styles.routeDivider} />
          <View style={styles.routeRow}>
            <View style={[styles.dot, { backgroundColor: '#4CAF50' }]} />
            <Text style={styles.routeText} numberOfLines={1}>{delivery.delivery_location || 'Destination'}</Text>
          </View>
          <View style={styles.routeMeta}>
            <View style={styles.metaChip}>
              <IconWheat size={12} color="#16a34a" />
              <Text style={styles.metaText}>{delivery.crop_type || 'Cargo'}</Text>
            </View>
            <View style={styles.metaChip}>
              <IconPackage size={12} color="#666" />
              <Text style={styles.metaText}>{delivery.weight_kg || '—'} kg</Text>
            </View>
            <View style={[styles.metaChip, { backgroundColor: '#E1F5FE' }]}>
              <IconDollarSign size={12} color={theme.colors.sky} />
              <Text style={[styles.metaText, { color: theme.colors.sky, fontWeight: '800' }]}>{delivery.payment_amount || 0}</Text>
            </View>
          </View>
        </View>

        {/* Status Timeline */}
        <View style={styles.timelineCard}>
          <Text style={styles.sectionTitle}>Delivery Progress</Text>
          {STEPS.map((step, idx) => {
            const StepIcon = step.icon;
            const isComplete = idx <= currentIdx;
            const isCurrent = idx === currentIdx;
            return (
              <View key={step.key} style={styles.timelineRow}>
                <View style={styles.timelineLeft}>
                  <View style={[
                    styles.timelineDot,
                    isComplete ? { backgroundColor: theme.colors.sky } : { backgroundColor: '#E0E0E0' },
                    isCurrent && { borderWidth: 3, borderColor: 'rgba(41,182,246,0.3)' },
                  ]}>
                    <StepIcon size={14} color={isComplete ? '#FFF' : '#999'} />
                  </View>
                  {idx < STEPS.length - 1 && (
                    <View style={[styles.timelineLine, isComplete && { backgroundColor: theme.colors.sky }]} />
                  )}
                </View>
                <View style={styles.timelineContent}>
                  <Text style={[styles.timelineLabel, isComplete && { color: theme.colors.dark }]}>{step.label}</Text>
                  {isCurrent && <Text style={styles.timelineStatus}>Current</Text>}
                </View>
              </View>
            );
          })}
        </View>

        {/* Action Buttons */}
        {nextStep && (
          <TouchableOpacity
            style={[styles.actionBtn, updating && { opacity: 0.6 }]}
            onPress={() => handleUpdateStatus(nextStep.key)}
            disabled={updating}
          >
            <Text style={styles.actionText}>{updating ? 'Updating...' : `Mark as ${nextStep.label}`}</Text>
          </TouchableOpacity>
        )}

        {status === 'delivered' && (
          <View style={styles.completeCard}>
            <IconCheckCircle size={32} color="#4CAF50" />
            <Text style={styles.completeTitle}>Delivery Complete</Text>
            <Text style={styles.completeText}>Payment is being processed</Text>
          </View>
        )}

        {/* Live Tracking Status */}
        {locationStatus.isTracking && (
          <View style={styles.trackingCard}>
            <View style={styles.trackingHeader}>
              <IconNavigation size={20} color={theme.colors.sky} />
              <Text style={styles.trackingTitle}>Live Tracking Active</Text>
            </View>
            <View style={styles.trackingStats}>
              <View style={styles.trackingStat}>
                <Text style={styles.trackingLabel}>Speed</Text>
                <Text style={styles.trackingValue}>{locationStatus.currentSpeed || 0} km/h</Text>
              </View>
              <View style={styles.trackingDivider} />
              <View style={styles.trackingStat}>
                <Text style={styles.trackingLabel}>Distance Today</Text>
                <Text style={styles.trackingValue}>{Math.round((locationStatus.distanceTraveled24h || 0) / 1000)} km</Text>
              </View>
            </View>
          </View>
        )}

        {/* Customer Information */}
        <View style={styles.customerCard}>
          <View style={styles.customerHeader}>
            <IconUser size={20} color={theme.colors.sky} />
            <Text style={styles.customerName}>{delivery.customer_name || 'Customer'}</Text>
          </View>
          <TouchableOpacity style={styles.contactButton} onPress={handleCallCustomer}>
            <IconPhone size={18} color="#FFF" />
            <Text style={styles.contactButtonText}>Call Customer</Text>
          </TouchableOpacity>
        </View>

        {/* Enhanced Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.quickBtn} onPress={() => setShowProofModal(true)}>
            <IconCamera size={20} color={theme.colors.sky} />
            <Text style={styles.quickLabel}>Photo Proof</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickBtn} onPress={handleCallCustomer}>
            <IconPhone size={20} color={theme.colors.sky} />
            <Text style={styles.quickLabel}>Call Customer</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickBtn} onPress={handleNavigate}>
            <IconNavigation size={20} color={theme.colors.sky} />
            <Text style={styles.quickLabel}>Navigate</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickBtn} onPress={handleShareLocation}>
            <IconMapPin size={20} color={theme.colors.sky} />
            <Text style={styles.quickLabel}>Share Location</Text>
          </TouchableOpacity>
        </View>

        {/* Report Issue Button */}
        <TouchableOpacity style={styles.issueReportBtn} onPress={() => setShowIssueModal(true)}>
          <IconAlertTriangle size={20} color="#FF5722" />
          <Text style={styles.issueReportText}>Report Issue</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Proof of Delivery Modal */}
      <Modal visible={showProofModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Proof of Delivery</Text>
            <TouchableOpacity onPress={() => setShowProofModal(false)} style={styles.modalCloseBtn}>
              <IconX size={20} color="#666" />
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalSectionTitle}>Photos</Text>
            <View style={styles.photosGrid}>
              {photos.map((photo, index) => (
                <View key={index} style={styles.photoContainer}>
                  <Image source={{ uri: photo.uri }} style={styles.photo} />
                  <TouchableOpacity
                    style={styles.removePhoto}
                    onPress={() => setPhotos(prev => prev.filter((_, i) => i !== index))}
                  >
                    <IconX size={16} color="#FFF" />
                  </TouchableOpacity>
                </View>
              ))}
              <TouchableOpacity style={styles.addPhoto} onPress={handleTakePhoto}>
                <IconCamera size={24} color="#999" />
                <Text style={styles.addPhotoText}>Add Photo</Text>
              </TouchableOpacity>
            </View>
            
            <Text style={styles.modalSectionTitle}>Notes</Text>
            <TextInput
              style={styles.notesInput}
              value={notes}
              onChangeText={setNotes}
              placeholder="Add delivery notes..."
              multiline
              numberOfLines={4}
            />
            
            <TouchableOpacity style={styles.signatureButton} onPress={handleCaptureSignature}>
              <Text style={styles.signatureButtonText}>
                {signature ? 'Signature Captured' : 'Capture Signature'}
              </Text>
            </TouchableOpacity>
          </ScrollView>
          
          <View style={styles.modalFooter}>
            <TouchableOpacity 
              style={[styles.submitButton, updating && styles.submitButtonDisabled]}
              onPress={handleSubmitProof}
              disabled={updating}
            >
              {updating ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <>
                  <IconUpload size={18} color="#FFF" />
                  <Text style={styles.submitButtonText}>Submit Proof</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>

      {/* Report Issue Modal */}
      <Modal visible={showIssueModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Report Issue</Text>
            <TouchableOpacity onPress={() => setShowIssueModal(false)} style={styles.modalCloseBtn}>
              <IconX size={20} color="#666" />
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalSectionTitle}>Issue Type</Text>
            <View style={styles.issueTypes}>
              {['delay', 'damage', 'wrong_address', 'customer_not_available', 'other'].map(type => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.issueTypeChip,
                    issueType === type && styles.issueTypeSelected
                  ]}
                  onPress={() => setIssueType(type)}
                >
                  <Text style={[
                    styles.issueTypeText,
                    issueType === type && styles.issueTypeTextSelected
                  ]}>
                    {type.replace('_', ' ')}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            
            <Text style={styles.modalSectionTitle}>Description</Text>
            <TextInput
              style={styles.descriptionInput}
              value={issueDescription}
              onChangeText={setIssueDescription}
              placeholder="Describe the issue..."
              multiline
              numberOfLines={4}
            />
            
            <Text style={styles.modalSectionTitle}>Photos (Optional)</Text>
            <View style={styles.photosGrid}>
              {photos.map((photo, index) => (
                <View key={index} style={styles.photoContainer}>
                  <Image source={{ uri: photo.uri }} style={styles.photo} />
                  <TouchableOpacity
                    style={styles.removePhoto}
                    onPress={() => setPhotos(prev => prev.filter((_, i) => i !== index))}
                  >
                    <IconX size={16} color="#FFF" />
                  </TouchableOpacity>
                </View>
              ))}
              <TouchableOpacity style={styles.addPhoto} onPress={handleTakePhoto}>
                <IconCamera size={24} color="#999" />
                <Text style={styles.addPhotoText}>Add Photo</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
          
          <View style={styles.modalFooter}>
            <TouchableOpacity 
              style={[styles.submitButton, updating && styles.submitButtonDisabled]}
              onPress={handleReportIssue}
              disabled={updating}
            >
              {updating ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <>
                  <IconMessageSquare size={18} color="#FFF" />
                  <Text style={styles.submitButtonText}>Report Issue</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F0F0F0', justifyContent: 'center', alignItems: 'center' },
  topTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.dark },
  routeCard: {
    marginHorizontal: 20,
    backgroundColor: '#FFF',
    borderRadius: 20,
    padding: 20,
    ...theme.shadows.xs,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  routeRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  dot: { width: 10, height: 10, borderRadius: 5 },
  routeText: { fontSize: 15, fontWeight: '600', color: theme.colors.dark, flex: 1 },
  routeDivider: { width: 2, height: 16, backgroundColor: '#E0E0E0', marginLeft: 4, marginVertical: 4 },
  routeMeta: { flexDirection: 'row', gap: 8, marginTop: 16, paddingTop: 14, borderTopWidth: 1, borderTopColor: '#F5F5F5' },
  metaChip: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#F5F5F5', paddingHorizontal: 9, paddingVertical: 5, borderRadius: 8 },
  metaText: { fontSize: 12, fontWeight: '600', color: '#666' },
  timelineCard: {
    marginHorizontal: 20,
    marginTop: 20,
    backgroundColor: '#FFF',
    borderRadius: 20,
    padding: 24,
    ...theme.shadows.xs,
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  sectionTitle: { fontSize: 14, fontWeight: '800', color: '#999', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 20 },
  timelineRow: { flexDirection: 'row', minHeight: 52 },
  timelineLeft: { alignItems: 'center', width: 36, marginRight: 14 },
  timelineDot: { width: 30, height: 30, borderRadius: 15, justifyContent: 'center', alignItems: 'center' },
  timelineLine: { width: 2, flex: 1, backgroundColor: '#E0E0E0', marginVertical: 4 },
  timelineContent: { flex: 1, paddingBottom: 16 },
  timelineLabel: { fontSize: 15, fontWeight: '600', color: '#BBB' },
  timelineStatus: { fontSize: 11, fontWeight: '700', color: theme.colors.sky, marginTop: 4, textTransform: 'uppercase' },
  actionBtn: {
    marginHorizontal: 20,
    marginTop: 24,
    backgroundColor: theme.colors.sky,
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: 'center',
    ...theme.shadows.md,
  },
  actionText: { color: '#FFF', fontSize: 16, fontWeight: '700', letterSpacing: 0.5 },
  completeCard: { marginHorizontal: 20, marginTop: 24, backgroundColor: '#E8F5E9', borderRadius: 20, padding: 28, alignItems: 'center' },
  completeTitle: { fontSize: 20, fontWeight: '800', color: '#2E7D32', marginTop: 12 },
  completeText: { fontSize: 14, color: '#4CAF50', marginTop: 6, fontWeight: '500' },
  quickActions: { flexDirection: 'row', marginHorizontal: 20, marginTop: 24, gap: 12, flexWrap: 'wrap' },
  quickBtn: {
    width: '48%',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 18,
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    marginBottom: 12,
  },
  quickLabel: { fontSize: 13, fontWeight: '700', color: theme.colors.dark },

  trackingCard: {
    marginHorizontal: 20,
    marginTop: 20,
    backgroundColor: '#E3F2FD',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#BBDEFB',
  },
  trackingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  trackingTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: theme.colors.sky,
  },
  trackingStats: {
    flexDirection: 'row',
  },
  trackingStat: {
    flex: 1,
    alignItems: 'center',
  },
  trackingLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
  },
  trackingValue: {
    fontSize: 16,
    fontWeight: '900',
    color: theme.colors.dark,
  },
  trackingDivider: {
    width: 1,
    backgroundColor: '#BBDEFB',
    marginHorizontal: 16,
  },

  customerCard: {
    marginHorizontal: 20,
    marginTop: 20,
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    ...theme.shadows.xs,
  },
  customerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  customerName: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.dark,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    borderRadius: 12,
  },
  contactButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '700',
  },

  issueReportBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 40,
    backgroundColor: '#FFF3E0',
    paddingVertical: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#FFCC80',
  },
  issueReportText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FF5722',
  },

  modalContainer: { flex: 1, backgroundColor: '#F8F9FA' },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: theme.colors.dark,
  },
  modalCloseBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: '#F5F5F5', justifyContent: 'center', alignItems: 'center',
  },
  modalContent: { flex: 1, padding: 20 },
  modalSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.dark,
    marginBottom: 12,
  },
  
  photosGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  photoContainer: {
    position: 'relative',
    width: 100,
    height: 100,
  },
  photo: {
    width: '100%',
    height: '100%',
    borderRadius: 8,
  },
  removePhoto: {
    position: 'absolute',
    top: -4,
    right: -4,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#FF5252',
    justifyContent: 'center',
    alignItems: 'center',
  },
  removePhotoText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  addPhoto: {
    width: 100,
    height: 100,
    borderRadius: 8,
    backgroundColor: '#F5F5F5',
    borderWidth: 2,
    borderColor: '#E0E0E0',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 4,
  },
  addPhotoText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#999',
  },
  
  notesInput: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    fontSize: 15,
    marginBottom: 24,
  },
  signatureButton: {
    backgroundColor: '#F5F5F5',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    alignItems: 'center',
    marginBottom: 24,
  },
  signatureButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: theme.colors.sky,
  },

  issueTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 24,
  },
  issueTypeChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    borderColor: '#F0F0F0',
  },
  issueTypeSelected: {
    backgroundColor: theme.colors.sky,
    borderColor: theme.colors.sky,
  },
  issueTypeText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
  },
  issueTypeTextSelected: { color: '#FFF' },
  
  descriptionInput: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F0F0F0',
    fontSize: 15,
    marginBottom: 24,
  },

  modalFooter: {
    padding: 20,
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: theme.colors.sky,
    paddingVertical: 16,
    borderRadius: 16,
    ...theme.shadows.sm,
  },
  submitButtonDisabled: { backgroundColor: '#CCC' },
  submitButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '800',
  },
});
