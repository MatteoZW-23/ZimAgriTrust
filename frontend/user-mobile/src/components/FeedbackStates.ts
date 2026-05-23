import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { theme } from '../styles';

export const EmptyState = ({ icon, title, desc, actionLabel, onAction }) => (
  <View style={styles.emptyContainer}>
    <View style={styles.emptyIconBox}>
        <Text style={{ fontSize: 48 }}>{icon}</Text>
    </View>
    <Text style={styles.emptyTitle}>{title}</Text>
    <Text style={styles.emptyDesc}>{desc}</Text>
    {actionLabel && (
        <TouchableOpacity style={styles.emptyBtn} onPress={onAction}>
            <Text style={styles.emptyBtnText}>{actionLabel}</Text>
        </TouchableOpacity>
    )}
  </View>
);

export const Skeleton = ({ width = '100%', height = 20, radius = 8 }) => {
  const animatedValue = new Animated.Value(0);

  React.useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(animatedValue, { toValue: 1, duration: 1000, useNativeDriver: true }),
        Animated.timing(animatedValue, { toValue: 0, duration: 1000, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const opacity = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.6]
  });

  return (
    <Animated.View style={[styles.skeleton, { width, height, borderRadius: radius, opacity }]} />
  );
};

const styles = StyleSheet.create({
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyIconBox: { width: 100, height: 100, borderRadius: 50, backgroundColor: '#F9F9F9', justifyContent: 'center', alignItems: 'center', marginBottom: 24 },
  emptyTitle: { fontSize: 22, fontWeight: '800', color: theme.colors.black, textAlign: 'center' },
  emptyDesc: { fontSize: 14, color: '#666', textAlign: 'center', marginTop: 12, lineHeight: 22 },
  emptyBtn: { marginTop: 32, paddingVertical: 18, paddingHorizontal: 40, backgroundColor: theme.colors.green, borderRadius: 20 },
  emptyBtnText: { color: '#FFF', fontWeight: '800', fontSize: 15 },
  skeleton: { backgroundColor: '#EEE' }
});
