import React, { useState } from "react";
import { Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet, Alert, ActivityIndicator, Image, Platform } from "react-native";
import { theme } from "../styles";
import { createListing } from "../api";
import { appStyles } from "../styles";
import * as ImagePicker from 'expo-image-picker';
import { Camera, X, Info, Calendar, MapPin, Package, DollarSign } from 'lucide-react-native';

const SECTORS = [
  { id: 'CROPS', label: 'Crops', icon: '🌾', color: '#F0FDF4' },
  { id: 'LIVESTOCK', label: 'Livestock', icon: '🐄', color: '#FFFBEB' },
  { id: 'POULTRY', label: 'Poultry', icon: '🐔', color: '#FEF2F2' },
  { id: 'DAIRY', label: 'Dairy', icon: '🥛', color: '#EFF6FF' },
  { id: 'HORTICULTURE', label: 'Horticulture', icon: '🥬', color: '#F5F3FF' },
  { id: 'AGRI_INPUTS', label: 'Inputs', icon: '🧪', color: '#FFF7ED' },
];

export default function CreateListingScreen({ navigation, route }) {
  const { role = 'farmer', token } = route.params || {};
  const [form, setForm] = useState({ 
    sector: 'CROPS', 
    crop: '', 
    qty: '', 
    price: '', 
    grade: 'A', 
    location: '',
    description: '',
    harvestDate: '',
    unit: 'kg'
  });
  const [submitting, setSubmitting] = useState(false);
  const [images, setImages] = useState([]);
  const [errors, setErrors] = useState({});

  const pickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
        allowsMultipleSelection: true,
      });

      if (!result.canceled) {
        const newImages = result.assets.map(asset => asset.uri);
        setImages([...images, ...newImages].slice(0, 5)); // Max 5 images
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const takePhoto = async () => {
    try {
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled) {
        setImages([...images, result.assets[0].uri].slice(0, 5));
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to take photo');
    }
  };

  const removeImage = (index) => {
    setImages(images.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!form.crop.trim()) newErrors.crop = 'Product name is required';
    if (!form.qty || isNaN(Number(form.qty)) || Number(form.qty) <= 0) newErrors.qty = 'Valid quantity is required';
    if (!form.price || isNaN(Number(form.price)) || Number(form.price) <= 0) newErrors.price = 'Valid price is required';
    if (!form.location.trim()) newErrors.location = 'Location is required';
    if (!form.description.trim()) newErrors.description = 'Description is required';
    if (images.length === 0) newErrors.images = 'At least one image is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const calculateTotal = () => {
    const qty = Number(form.qty) || 0;
    const price = Number(form.price) || 0;
    return qty * price;
  };

  const calculateFee = () => {
    const total = calculateTotal();
    return total * 0.02; // 2% platform fee
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      Alert.alert('Validation Error', 'Please fix the errors before submitting.');
      return;
    }

    try {
      setSubmitting(true);
      const payload = {
        sector: form.sector,
        crop: form.crop,
        quantity: Number(form.qty),
        quantity_unit: form.unit,
        price_per_unit: Number(form.price),
        currency: 'USD',
        grade: form.grade,
        location: form.location,
        description: form.description,
        harvest_date: form.harvestDate,
        images: images,
      };

      await createListing(token, payload);
      Alert.alert('Success', 'Your listing has been posted to the market!', [
        { text: 'OK', onPress: () => navigation.navigate('FarmerListings', { token }) }
      ]);
    } catch (err) {
      Alert.alert('Error', err.message || 'Failed to create listing. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>List New Produce</Text>
        <Text style={styles.subTitle}>Select a sector to see market trends</Text>
      </View>

      {/* Sector Grid */}
      {SECTORS.length > 0 ? (
        <View style={styles.grid}>
          {SECTORS.map(s => (
            <TouchableOpacity 
              key={s.id} 
              style={[styles.sectorCard, { backgroundColor: s.color }, form.sector === s.id && styles.sectorActive]}
              onPress={() => setForm({...form, sector: s.id})}
            >
              <Text style={{ fontSize: 30 }}>{s.icon}</Text>
              <Text style={styles.sectorLabel}>{s.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      ) : (
        <View style={{ padding: 24, alignItems: 'center' }}>
          <Text style={{ fontSize: 14, color: '#999' }}>Select a sector to begin</Text>
        </View>
      )}

      {/* Image Upload */}
      <View style={styles.form}>
        <Text style={styles.label}>Product Images <Text style={{ color: '#EF4444' }}>*</Text></Text>
        <View style={styles.imageUploadSection}>
          {images.length === 0 ? (
            <View style={styles.imagePlaceholder}>
              <Camera size={40} color="#CBD5E1" />
              <Text style={styles.imagePlaceholderText}>Add product photos</Text>
              <Text style={styles.imagePlaceholderSub}>Max 5 images</Text>
            </View>
          ) : (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.imageScroll}>
              {images.map((uri, index) => (
                <View key={index} style={styles.imageWrapper}>
                  <Image source={{ uri }} style={styles.image} />
                  <TouchableOpacity style={styles.removeImageButton} onPress={() => removeImage(index)}>
                    <X size={16} color="#FFF" />
                  </TouchableOpacity>
                </View>
              ))}
              {images.length < 5 && (
                <TouchableOpacity style={styles.addImageButton} onPress={pickImage}>
                  <Camera size={24} color="#10B981" />
                </TouchableOpacity>
              )}
            </ScrollView>
          )}
          <View style={styles.imageButtonRow}>
            <TouchableOpacity style={styles.secondaryBtn} onPress={pickImage}>
              <Text style={styles.secondaryBtnText}>From Gallery</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondaryBtn} onPress={takePhoto}>
              <Text style={styles.secondaryBtnText}>Take Photo</Text>
            </TouchableOpacity>
          </View>
        </View>
        {errors.images && <Text style={styles.errorText}>{errors.images}</Text>}
      </View>

      {/* Form */}
      <View style={styles.form}>
        <Text style={styles.label}>Product Name <Text style={{ color: '#EF4444' }}>*</Text></Text>
        <TextInput 
          style={[styles.input, errors.crop && styles.inputError]} 
          placeholder="e.g. White Maize, Beef Cattle" 
          value={form.crop} 
          onChangeText={v => setForm({...form, crop: v})} 
        />
        {errors.crop && <Text style={styles.errorText}>{errors.crop}</Text>}

        <Text style={styles.label}>Description <Text style={{ color: '#EF4444' }}>*</Text></Text>
        <TextInput 
          style={[styles.input, styles.textArea, errors.description && styles.inputError]} 
          placeholder="Describe your product, quality, and any special features..."
          multiline
          numberOfLines={4}
          value={form.description}
          onChangeText={v => setForm({...form, description: v})}
        />
        {errors.description && <Text style={styles.errorText}>{errors.description}</Text>}

        <Text style={styles.label}>Location <Text style={{ color: '#EF4444' }}>*</Text></Text>
        <TextInput 
          style={[styles.input, errors.location && styles.inputError]} 
          placeholder="e.g. Harare, Bulawayo" 
          value={form.location} 
          onChangeText={v => setForm({...form, location: v})} 
        />
        {errors.location && <Text style={styles.errorText}>{errors.location}</Text>}

        <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={styles.label}>Quantity <Text style={{ color: '#EF4444' }}>*</Text></Text>
                <TextInput 
                  style={[styles.input, errors.qty && styles.inputError]} 
                  placeholder="e.g. 500" 
                  keyboardType="numeric"
                  value={form.qty}
                  onChangeText={v => setForm({...form, qty: v})}
                />
                {errors.qty && <Text style={styles.errorText}>{errors.qty}</Text>}
            </View>
            <View style={{ flex: 1 }}>
                <Text style={styles.label}>Unit</Text>
                <TextInput 
                  style={styles.input} 
                  placeholder="kg, tons, etc."
                  value={form.unit}
                  onChangeText={v => setForm({...form, unit: v})}
                />
            </View>
        </View>

        <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={styles.label}>Price per Unit ($) <Text style={{ color: '#EF4444' }}>*</Text></Text>
                <TextInput 
                  style={[styles.input, errors.price && styles.inputError]} 
                  placeholder="e.g. 0.45" 
                  keyboardType="numeric"
                  value={form.price}
                  onChangeText={v => setForm({...form, price: v})}
                />
                {errors.price && <Text style={styles.errorText}>{errors.price}</Text>}
            </View>
            <View style={{ flex: 1 }}>
                <Text style={styles.label}>Quality Grade</Text>
                <TextInput 
                  style={styles.input} 
                  placeholder="Grade A, Premium"
                  value={form.grade}
                  onChangeText={v => setForm({...form, grade: v})}
                />
            </View>
        </View>

        <Text style={styles.label}>Harvest Date (Optional)</Text>
        <TextInput 
          style={styles.input} 
          placeholder="YYYY-MM-DD"
          value={form.harvestDate}
          onChangeText={v => setForm({...form, harvestDate: v})}
        />

        {/* Pricing Summary */}
        {(form.qty && form.price) && (
          <View style={styles.pricingSummary}>
            <View style={styles.pricingHeader}>
              <DollarSign size={20} color="#10B981" />
              <Text style={styles.pricingTitle}>Pricing Summary</Text>
            </View>
            <View style={styles.pricingRow}>
              <Text style={styles.pricingLabel}>Total Value</Text>
              <Text style={styles.pricingValue}>${calculateTotal().toFixed(2)}</Text>
            </View>
            <View style={styles.pricingRow}>
              <Text style={styles.pricingLabel}>Platform Fee (2%)</Text>
              <Text style={styles.pricingValue}>-${calculateFee().toFixed(2)}</Text>
            </View>
            <View style={[styles.pricingRow, styles.pricingTotal]}>
              <Text style={styles.pricingTotalLabel}>You'll Receive</Text>
              <Text style={styles.pricingTotalValue}>${(calculateTotal() - calculateFee()).toFixed(2)}</Text>
            </View>
          </View>
        )}

        <TouchableOpacity 
          style={styles.primaryBtn} 
          onPress={handleSubmit}
          disabled={submitting}
        >
            {submitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.primaryBtnText}>Post to National Market</Text>
            )}
        </TouchableOpacity>
      </View>
      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { padding: 24, paddingTop: 60 },
  title: { fontSize: 24, fontWeight: '900', color: theme.colors.black },
  subTitle: { fontSize: 14, color: '#999', marginTop: 4 },
  grid: { padding: 16, flexDirection: 'row', flexWrap: 'wrap' },
  sectorCard: { width: '30%', margin: '1.6%', aspectRatio: 1, borderRadius: 16, justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: 'transparent' },
  sectorActive: { borderColor: theme.colors.green },
  sectorLabel: { fontSize: 11, fontWeight: '800', color: '#666', marginTop: 8 },
  form: { padding: 24 },
  label: { fontSize: 13, fontWeight: '800', color: '#999', textTransform: 'uppercase', marginBottom: 8, marginTop: 16 },
  input: { height: 60, borderRadius: 16, backgroundColor: '#F9F9F9', paddingHorizontal: 20, fontSize: 16, fontWeight: '600' },
  inputError: { borderWidth: 2, borderColor: '#EF4444' },
  textArea: { height: 120, textAlignVertical: 'top', paddingTop: 16 },
  errorText: { color: '#EF4444', fontSize: 12, fontWeight: '600', marginTop: 4 },
  row: { flexDirection: 'row' },
  
  // Image upload styles
  imageUploadSection: { marginBottom: 16 },
  imagePlaceholder: { 
    height: 150, borderRadius: 16, backgroundColor: '#F9F9F9', 
    justifyContent: 'center', alignItems: 'center', borderWidth: 2, 
    borderColor: '#E5E7EB', borderStyle: 'dashed' 
  },
  imagePlaceholderText: { fontSize: 16, fontWeight: '700', color: '#64748B', marginTop: 12 },
  imagePlaceholderSub: { fontSize: 12, color: '#94A3B8', marginTop: 4 },
  imageScroll: { marginBottom: 12 },
  imageWrapper: { marginRight: 12, position: 'relative' },
  image: { width: 100, height: 100, borderRadius: 12 },
  removeImageButton: { 
    position: 'absolute', top: -8, right: -8, width: 24, height: 24, 
    borderRadius: 12, backgroundColor: '#EF4444', justifyContent: 'center', alignItems: 'center' 
  },
  addImageButton: { 
    width: 100, height: 100, borderRadius: 12, backgroundColor: '#F0FDF4', 
    justifyContent: 'center', alignItems: 'center', borderWidth: 2, 
    borderColor: '#10B981', borderStyle: 'dashed' 
  },
  imageButtonRow: { flexDirection: 'row', gap: 12 },
  secondaryBtn: { 
    flex: 1, height: 48, borderRadius: 12, backgroundColor: '#F3F4F6', 
    justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: '#E5E7EB' 
  },
  secondaryBtnText: { fontSize: 14, fontWeight: '700', color: '#374151' },
  
  // Pricing summary styles
  pricingSummary: { 
    backgroundColor: '#F0FDF4', borderRadius: 16, padding: 16, marginTop: 24,
    borderWidth: 1, borderColor: '#10B981' 
  },
  pricingHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  pricingTitle: { fontSize: 16, fontWeight: '800', color: '#065F46', marginLeft: 8 },
  pricingRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  pricingLabel: { fontSize: 14, fontWeight: '600', color: '#64748B' },
  pricingValue: { fontSize: 14, fontWeight: '700', color: '#374151' },
  pricingTotal: { marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: '#10B981' },
  pricingTotalLabel: { fontSize: 16, fontWeight: '800', color: '#065F46' },
  pricingTotalValue: { fontSize: 18, fontWeight: '900', color: '#10B981' },
  
  chipRow: { flexDirection: 'row', gap: 10, marginTop: 8 },
  chip: { paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, backgroundColor: '#F0F0F0' },
  chipActive: { backgroundColor: theme.colors.green },
  chipText: { fontSize: 13, fontWeight: '700', color: '#666' },
  chipTextActive: { color: '#FFF' },
  primaryBtn: { backgroundColor: theme.colors.green, height: 64, borderRadius: 20, justifyContent: 'center', alignItems: 'center', marginTop: 40 },
  primaryBtnText: { color: '#FFF', fontSize: 18, fontWeight: '800' }
});
