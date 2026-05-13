import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export const Marker = () => null;

const MapViewComponent = ({ children, style }) => {
  return (
    <View style={[styles.container, style]}>
      <Text style={styles.text}>Map View is not available on Web</Text>
      <Text style={styles.subText}>Use a physical device or emulator to see the map</Text>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  text: {
    color: '#6B7280',
    fontSize: 16,
    fontWeight: '700',
  },
  subText: {
    color: '#9CA3AF',
    fontSize: 12,
    marginTop: 4,
  }
});

export default MapViewComponent;
