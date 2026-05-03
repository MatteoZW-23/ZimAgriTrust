import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { theme } from '../styles';

export default function WalletScreen({ navigation, route }) {
  const { token } = route.params || {};
  const [transactions, setTransactions] = React.useState([]);
  const [balance, setBalance] = React.useState(null);
  const [earnings, setEarnings] = React.useState(null);

  React.useEffect(() => {
    if (!token) return;
    import('../api').then(({ getWalletBalance, getTransactions, getEarnings }) => {
      getWalletBalance(token).then(data => setBalance(data)).catch(() => {});
      getTransactions(token).then(data => setTransactions(Array.isArray(data) ? data : data?.data || [])).catch(() => {});
      getEarnings(token).then(data => setEarnings(data)).catch(() => {});
    });
  }, [token]);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}><Text style={styles.backBtn}>← Back</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>My Wallet</Text>
        <View style={{ width: 60 }} />
      </View>

      {/* Balance Card */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>WALLET BALANCE</Text>
        <View style={styles.balanceCard}>
           <Text style={styles.currencySymbol}>$</Text>
           <Text style={styles.balanceValue}>{balance?.balance_usd != null ? balance.balance_usd.toFixed(2) : '--'}</Text>
           <Text style={styles.balanceTag}>ZIG: {balance?.balance_zig != null ? balance.balance_zig.toFixed(2) : '--'} · Pending: ${balance?.pending_usd != null ? balance.pending_usd.toFixed(2) : '--'}</Text>

           <View style={styles.actionRow}>
                <TouchableOpacity style={styles.actionBtn}><Text style={styles.actionBtnText}>Add Funds</Text></TouchableOpacity>
                <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('Withdraw', { token })}>
                  <Text style={styles.actionBtnText}>Withdraw</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionBtn}><Text style={styles.actionBtnText}>History</Text></TouchableOpacity>
           </View>
        </View>
      </View>

      {/* Earnings Summary */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>EARNINGS SUMMARY</Text>
        <View style={styles.card}>
          <View style={styles.rowBetween}>
            <Text style={styles.label}>Total Sales</Text>
            <Text style={styles.value}>${(earnings?.total_sales ?? 0).toFixed(2)}</Text>
          </View>
          <View style={styles.rowBetween}>
            <Text style={styles.label}>Platform Fees</Text>
            <Text style={styles.valueRed}>-${(earnings?.total_fees ?? 0).toFixed(2)}</Text>
          </View>
          <View style={styles.rowBetween}>
            <Text style={styles.label}>Net Payout</Text>
            <Text style={styles.valueGreen}>${(earnings?.net_payout ?? 0).toFixed(2)}</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.rowBetween}>
            <Text style={styles.label}>Transport Commission</Text>
            <Text style={styles.value}>${(earnings?.transport_commission ?? 0).toFixed(2)}</Text>
          </View>
          <View style={styles.rowBetween}>
            <Text style={styles.label}>Boost Fees Paid</Text>
            <Text style={styles.valueRed}>-${(earnings?.boost_fees_paid ?? 0).toFixed(2)}</Text>
          </View>
          <View style={styles.rowBetween}>
            <Text style={styles.label}>Orders Completed</Text>
            <Text style={styles.value}>{earnings?.order_count ?? 0}</Text>
          </View>
        </View>
      </View>

      {/* Transactions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>RECENT TRANSACTIONS</Text>
        <View style={styles.listCard}>
            {transactions.length === 0 ? (
                <View style={{ padding: 24, alignItems: 'center' }}>
                    <Text style={{ color: '#999', fontWeight: '700' }}>No transactions yet</Text>
                </View>
            ) : transactions.map((tx, i) => (
                <View key={i} style={[styles.txItem, i === 0 && { borderTopWidth: 0 }]}>
                    <View style={styles.txLeft}>
                        <Text style={styles.txDate}>{tx.date || tx.created_at?.slice(0, 10)}</Text>
                        <Text style={styles.txRef}>{tx.id} • {tx.product || tx.description}</Text>
                    </View>
                    <View style={styles.txRight}>
                        <Text style={[styles.txAmount, tx.amount > 0 ? { color: theme.colors.green } : { color: theme.colors.red }]}>{tx.amount > 0 ? '+' : ''}${Math.abs(tx.amount).toFixed(2)}</Text>
                        <Text style={styles.txStatus}>{tx.status}</Text>
                    </View>
                </View>
            ))}
        </View>
        <TouchableOpacity style={styles.viewAllBtn}><Text style={styles.viewAllText}>View All Transactions →</Text></TouchableOpacity>
      </View>

      {/* Saved Payment Methods */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>SAVED PAYMENT METHODS</Text>
        <View style={styles.card}>
            <View style={styles.methodRow}>
                <View style={[styles.radioCircle, { backgroundColor: theme.colors.sky, borderColor: theme.colors.sky }]} />
                <View style={{ flex: 1 }}>
                    <Text style={styles.methodTitle}>{balance?.payment_method || 'No payment method saved'}</Text>
                    <Text style={styles.methodSub}>{balance?.payment_method ? '[Default Payment Method]' : ''}</Text>
                </View>
            </View>
        </View>
        <TouchableOpacity style={styles.addBtn}><Text style={styles.addBtnText}>Add New Payment Method +</Text></TouchableOpacity>
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { padding: 24, paddingTop: 60, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backBtn: { fontSize: 16, fontWeight: '700', color: theme.colors.sky },
  headerTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.black },
  section: { marginTop: 24, paddingHorizontal: 24 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#999', letterSpacing: 1.2, marginBottom: 16 },
  balanceCard: { padding: 40, backgroundColor: theme.colors.black, borderRadius: 24, alignItems: 'center' },
  currencySymbol: { color: theme.colors.sky, fontSize: 24, fontWeight: '700' },
  balanceValue: { color: '#FFF', fontSize: 44, fontWeight: '900', marginTop: 4 },
  balanceTag: { color: '#666', fontSize: 12, fontWeight: '700', marginTop: 8 },
  actionRow: { flexDirection: 'row', gap: 12, marginTop: 32 },
  actionBtn: { paddingVertical: 12, paddingHorizontal: 20, backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 12 },
  actionBtnText: { color: '#FFF', fontSize: 13, fontWeight: '700' },
  listCard: { backgroundColor: '#F9F9F9', borderRadius: 20, overflow: 'hidden' },
  txItem: { flexDirection: 'row', justifyContent: 'space-between', padding: 20, borderTopWidth: 1, borderTopColor: '#EEE' },
  txDate: { fontSize: 12, fontWeight: '800', color: '#999' },
  txRef: { fontSize: 16, fontWeight: '700', color: theme.colors.black, marginTop: 4 },
  txAmount: { fontSize: 16, fontWeight: '800', textAlign: 'right' },
  txStatus: { fontSize: 12, fontWeight: '800', textAlign: 'right', marginTop: 4 },
  viewAllBtn: { marginVertical: 16, alignItems: 'center' },
  viewAllText: { fontSize: 14, fontWeight: '700', color: theme.colors.sky },
  card: { padding: 24, backgroundColor: '#FFF', borderRadius: 20, borderWidth: 1, borderColor: '#EEE' },
  methodRow: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  radioCircle: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: '#DDD' },
  methodTitle: { fontSize: 15, fontWeight: '700', color: theme.colors.black },
  methodSub: { fontSize: 12, color: theme.colors.green, fontWeight: '700', marginTop: 2 },
  editBtn: { color: theme.colors.sky, fontWeight: '700', fontSize: 13 },
  addBtn: { margin: 24, paddingVertical: 14, borderStyle: 'dashed', borderWidth: 2, borderColor: '#DDD', borderRadius: 16, alignItems: 'center' },
  addBtnText: { color: '#999', fontWeight: '800', fontSize: 14 },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#EEE' },
  label: { fontSize: 14, fontWeight: '700', color: theme.colors.black },
  value: { fontSize: 14, fontWeight: '800', color: theme.colors.black },
  valueRed: { fontSize: 14, fontWeight: '800', color: theme.colors.red || '#dc2626' },
  valueGreen: { fontSize: 14, fontWeight: '800', color: theme.colors.green },
  divider: { height: 1, backgroundColor: '#EEE', marginVertical: 8 }
});
