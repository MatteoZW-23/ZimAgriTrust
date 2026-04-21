import React, { useState } from "react";
import { Text, TextInput, TouchableOpacity, View, ScrollView } from "react-native";

import { createListing } from "../api";
import { appStyles } from "../styles";

const SECTORS = [
  { id: "CROPS", label: "Crops", icon: "🌽", color: '#E8F5E9' },
  { id: "LIVESTOCK", label: "Livestock", icon: "🐂", color: '#FFF3E0' },
  { id: "POULTRY", label: "Poultry", icon: "🐔", color: '#FFEBEE' },
  { id: "DAIRY", label: "Dairy", icon: "🥛", color: '#E3F2FD' },
  { id: "FISHERIES", label: "Fisheries", icon: "🐟", color: '#E0F2F1' },
  { id: "VALUE_ADDED", label: "Processed", icon: "🍯", color: '#F3E5F5' },
];

export default function CreateListingScreen({ navigation, route }) {
  const { role = 'farmer' } = route.params || {};
  const [form, setForm] = useState({ sector: 'CROPS', crop: '', qty: '', price: '', grade: 'A' });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>List New Produce</Text>
        <Text style={styles.subTitle}>Select a sector to see market trends</Text>
      </View>

      {/* Sector Grid */}
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

      {/* Form */}
      <View style={styles.form}>
        <Text style={styles.label}>Product Name</Text>
        <TextInput style={styles.input} placeholder="e.g. White Maize, Beef Cattle" value={form.crop} onChangeText={v => setForm({...form, crop: v})} />

        <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={styles.label}>Quantity</Text>
                <TextInput style={styles.input} placeholder="e.g. 500" keyboardType="numeric" />
            </View>
            <View style={{ flex: 1 }}>
                <Text style={styles.label}>Price ($/unit)</Text>
                <TextInput style={styles.input} placeholder="e.g. 0.45" keyboardType="numeric" />
            </View>
        </View>

        <Text style={styles.label}>Quality Grade</Text>
        <View style={styles.chipRow}>
            {['Grade A', 'Grade B', 'Grade C'].map(g => (
                <TouchableOpacity key={g} style={[styles.chip, form.grade === g && styles.chipActive]} onPress={() => setForm({...form, grade: g})}>
                    <Text style={[styles.chipText, form.grade === g && styles.chipTextActive]}>{g}</Text>
                </TouchableOpacity>
            ))}
        </View>

        <TouchableOpacity style={styles.primaryBtn}>
            <Text style={styles.primaryBtnText}>Post to National Market</Text>
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
