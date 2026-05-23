import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { ArrowLeft } from 'lucide-react-native';
import { theme } from '../styles';

/**
 * Reusable screen header with back button.
 * Usage:
 *   <ScreenHeader title="Settings" navigation={navigation} />
 *   <ScreenHeader title="Edit Profile" navigation={navigation} rightElement={<SaveBtn />} />
 */
export default function ScreenHeader({ title, subtitle, navigation, onBack, rightElement }) {
  const handleBack = () => {
    if (onBack) { onBack(); return; }
    if (navigation?.canGoBack?.()) { navigation.goBack(); return; }
    if (navigation?.goBack) navigation.goBack();
  };

  return (
    <View style={styles.header}>
      <TouchableOpacity
        style={styles.backBtn}
        onPress={handleBack}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        activeOpacity={0.7}
      >
        <ArrowLeft size={22} color={theme.colors.dark} />
      </TouchableOpacity>

      <View style={styles.titleBlock}>
        <Text style={styles.title} numberOfLines={1}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle} numberOfLines={1}>{subtitle}</Text> : null}
      </View>

      <View style={styles.right}>
        {rightElement || <View style={{ width: 40 }} />}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  backBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: '#F5F5F5',
    justifyContent: 'center', alignItems: 'center',
  },
  titleBlock: { flex: 1, alignItems: 'center' },
  title: { fontSize: 17, fontWeight: '800', color: theme.colors.dark },
  subtitle: { fontSize: 12, color: '#999', fontWeight: '500', marginTop: 1 },
  right: { width: 40, alignItems: 'flex-end' },
});
