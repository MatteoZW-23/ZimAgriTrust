/**
 * MapViewComponent — safe cross-platform wrapper.
 * On native: renders react-native-maps MapView + Marker.
 * On web: renders a styled placeholder (react-native-maps doesn't support web).
 */
import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { MapPin } from 'lucide-react-native';
import { theme } from '../styles';

let NativeMapView = null;
let NativeMarker = null;

if (Platform.OS !== 'web') {
  try {
    const maps = require('react-native-maps');
    NativeMapView = maps.default;
    NativeMarker = maps.Marker;
  } catch {
    // react-native-maps not installed — fall through to placeholder
  }
}

// ── Web / fallback placeholder ────────────────────────────────────────────────
function MapPlaceholder({ style, children }) {
  return (
    <View style={[styles.placeholder, style]}>
      <MapPin size={36} color={theme.colors.sky} />
      <Text style={styles.placeholderTitle}>Map View</Text>
      <Text style={styles.placeholderSub}>
        Interactive map is available on the mobile app.{'\n'}
        Job locations are shown in the list below.
      </Text>
      {children}
    </View>
  );
}

function MarkerPlaceholder() {
  return null;
}

// ── Exports ───────────────────────────────────────────────────────────────────
const MapView = NativeMapView || MapPlaceholder;
const Marker  = NativeMarker  || MarkerPlaceholder;

export { Marker };
export default MapView;

const styles = StyleSheet.create({
  placeholder: {
    backgroundColor: '#EFF6FF',
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    borderWidth: 1,
    borderColor: '#BFDBFE',
    minHeight: 200,
  },
  placeholderTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: theme.colors.dark,
    marginTop: 12,
  },
  placeholderSub: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 20,
  },
});
