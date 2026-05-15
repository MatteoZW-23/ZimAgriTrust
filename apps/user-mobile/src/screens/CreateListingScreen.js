import React, { useState } from "react";
import { Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet, Alert, ActivityIndicator } from "react-native";
import { theme } from "../styles";
import { createListing } from "../api";
import { appStyles } from "../styles";

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
  const [form, setForm] = useState({ sector: 'CROPS', crop: '', qty: '', price: '', grade: 'A', location: '' });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!form.crop || !form.qty || !form.price) {
      Alert.alert('Missing Information', 'Please fill in product name, quantity, and price.');
      return;
    }

    const quantity = Number(form.qty);
    const price = Number(form.price);

    if (isNaN(quantity) || quantity <= 0) {
      Alert.alert('Invalid Quantity', 'Please enter a valid quantity.');
      return;
    }

    if (isNaN(price) || price <= 0) {
      Alert.alert('Invalid Price', 'Please enter a valid price.');
      return;
    }

    try {
      setSubmitting(true);
      const payload = {
        sector: form.sector,
        crop: form.crop,
        quantity: quantity,
        quantity_unit: 'kg',
        price_per_unit: price,
        currency: 'USD',
        grade: form.grade,
        location: form.location || 'Zimbabwe',
      };

      await createListing(token, payload);
      Alert.alert('Success', 'Your listing has been posted to the market!', [
        { text: 'OK', onPress: () => navigation.goBack() }
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

      {/* Form */}
      <View style={styles.form}>
        <Text style={styles.label}>Product Name</Text>
        <TextInput 
          style={styles.input} 
          placeholder="e.g. White Maize, Beef Cattle" 
          value={form.crop} 
          onChangeText={v => setForm({...form, crop: v})} 
        />

        <Text style={styles.label}>Location</Text>
        <TextInput 
          style={styles.input} 
          placeholder="e.g. Harare, Bulawayo" 
          value={form.location} 
          onChangeText={v => setForm({...form, location: v})} 
        />

        <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={styles.label}>Quantity (kg)</Text>
                <TextInput 
                  style={styles.input} 
                  placeholder="e.g. 500" 
                  keyboardType="numeric"
                  value={form.qty}
                  onChangeText={v => setForm({...form, qty: v})}
                />
            </View>
            <View style={{ flex: 1 }}>
                <Text style={styles.label}>Price ($/kg)</Text>
                <TextInput 
                  style={styles.input} 
                  placeholder="e.g. 0.45" 
                  keyboardType="numeric"
                  value={form.price}
                  onChangeText={v => setForm({...form, price: v})}
                />
            </View>
        </View>

        <Text style={styles.label}>Quality Grade</Text>
        <TextInput 
          style={[styles.input, { flex: 1 }]} 
          placeholder="e.g. Grade A, Premium, etc."
          value={form.grade}
          onChangeText={v => setForm({...form, grade: v})}
        />

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
  row: { flexDirection: 'row' },
  chipRow: { flexDirection: 'row', gap: 10, marginTop: 8 },
  chip: { paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12, backgroundColor: '#F0F0F0' },
  chipActive: { backgroundColor: theme.colors.green },
  chipText: { fontSize: 13, fontWeight: '700', color: '#666' },
  chipTextActive: { color: '#FFF' },
  primaryBtn: { backgroundColor: theme.colors.green, height: 64, borderRadius: 20, justifyContent: 'center', alignItems: 'center', marginTop: 40 },
  primaryBtnText: { color: '#FFF', fontSize: 18, fontWeight: '800' }
});
