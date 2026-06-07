import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { TransactionsScreen } from './TransactionsScreen';
import { theme } from '../styles';

export default function MyOrdersScreen({ navigation, route }) {
  const { role = 'buyer', token, profile = {} } = route.params || {};

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>{role === 'farmer' ? 'Farm Orders' : 'My Orders'}</Text>
          <Text style={styles.subtitle}>
            Live escrow, delivery, and payout status pulled from your real transaction flow.
          </Text>
        </View>
        <TouchableOpacity
          style={styles.detailsButton}
          onPress={() => navigation.navigate('Transactions', { token, profile })}
        >
          <Text style={styles.detailsButtonText}>Full Ledger</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.body} contentContainerStyle={styles.bodyContent} showsVerticalScrollIndicator={false}>
        <TransactionsScreen token={token} profile={{ ...profile, role: String(role || profile?.role || '').toUpperCase() }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F8FA',
  },
  header: {
    paddingTop: 56,
    paddingHorizontal: 20,
    paddingBottom: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E8ECF2',
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: '900',
    color: theme.colors.black,
  },
  subtitle: {
    marginTop: 6,
    fontSize: 13,
    lineHeight: 19,
    color: '#667085',
    maxWidth: 240,
  },
  detailsButton: {
    backgroundColor: theme.colors.sky,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 12,
  },
  detailsButtonText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 12,
    letterSpacing: 0.3,
  },
  body: {
    flex: 1,
  },
  bodyContent: {
    paddingBottom: 120,
  },
});
