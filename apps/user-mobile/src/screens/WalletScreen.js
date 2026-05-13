import React from 'react';
import { ActivityIndicator, Alert, TextInput, View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { 
  ArrowLeft as IconArrowLeft, 
  Plus as IconPlus, 
  Download as IconDownload, 
  History as IconHistory, 
  ChevronRight as IconChevronRight,
  Wallet as IconWallet,
  CreditCard as IconCreditCard
} from 'lucide-react-native';
import { theme } from '../styles';
import { depositFunds, getEarnings, getTransactions, getWalletBalance } from '../api';

export default function WalletScreen({ navigation, route }) {
  const { token } = route.params || {};
  const [transactions, setTransactions] = React.useState([]);
  const [balance, setBalance] = React.useState(null);
  const [earnings, setEarnings] = React.useState(null);
  const [showDeposit, setShowDeposit] = React.useState(false);
  const [depositAmount, setDepositAmount] = React.useState('');
  const [depositing, setDepositing] = React.useState(false);

  React.useEffect(() => {
    if (!token) return;
    getWalletBalance(token).then(data => setBalance(data)).catch(() => {});
    getTransactions(token).then(data => setTransactions(Array.isArray(data) ? data : data?.data || [])).catch(() => {});
    getEarnings(token).then(data => setEarnings(data)).catch(() => {});
  }, [token]);

  const handleDeposit = async () => {
    const amount = Number(depositAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      Alert.alert('Invalid amount', 'Enter a valid deposit amount.');
      return;
    }
    try {
      setDepositing(true);
      await depositFunds(token, { amount, payment_method: 'ecocash' });
      setShowDeposit(false);
      setDepositAmount('');
      setBalance(await getWalletBalance(token));
      Alert.alert('Deposit started', 'Follow the EcoCash/OneMoney prompt to complete payment.');
    } catch (err) {
      Alert.alert('Deposit failed', err.message || 'Could not start deposit.');
    } finally {
      setDepositing(false);
    }
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backCircle}>
          <IconArrowLeft size={20} color={theme.colors.black} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>My Wallet</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Balance Card */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>WALLET BALANCE</Text>
        <View style={styles.balanceCard}>
           <Text style={styles.currencySymbol}>$</Text>
           <Text style={styles.balanceValue}>{balance?.balance_usd != null ? balance.balance_usd.toFixed(2) : '--'}</Text>
           <Text style={styles.balanceTag}>ZIG: {balance?.balance_zig != null ? balance.balance_zig.toFixed(2) : '--'} · Pending: ${balance?.pending_usd != null ? balance.pending_usd.toFixed(2) : '--'}</Text>

           <View style={styles.actionRow}>
                <TouchableOpacity style={styles.actionBtn} onPress={() => setShowDeposit((v) => !v)}>
                  <IconPlus size={16} color="#FFF" style={{ marginBottom: 4 }} />
                  <Text style={styles.actionBtnText}>Add Funds</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('Withdraw', { token })}>
                  <IconDownload size={16} color="#FFF" style={{ marginBottom: 4 }} />
                  <Text style={styles.actionBtnText}>Withdraw</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionBtn} onPress={() => {}}>
                  <IconHistory size={16} color="#FFF" style={{ marginBottom: 4 }} />
                  <Text style={styles.actionBtnText}>History</Text>
                </TouchableOpacity>
           </View>
        </View>
        {showDeposit && (
          <View style={styles.depositCard}>
            <Text style={styles.inputLabel}>Deposit amount (USD)</Text>
            <TextInput
              style={styles.depositInput}
              value={depositAmount}
              onChangeText={setDepositAmount}
              keyboardType="decimal-pad"
              placeholder="10.00"
              placeholderTextColor="#94a3b8"
            />
            <TouchableOpacity style={styles.depositBtn} onPress={handleDeposit} disabled={depositing}>
              {depositing ? <ActivityIndicator color="#fff" /> : <Text style={styles.depositBtnText}>Start Mobile Money Deposit</Text>}
            </TouchableOpacity>
          </View>
        )}
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
                <View style={{ padding: 40, alignItems: 'center' }}>
                    <IconWallet size={40} color="#DDD" style={{ marginBottom: 12 }} />
                    <Text style={{ color: '#999', fontWeight: '700' }}>No transactions yet</Text>
                </View>
            ) : transactions.map((tx, i) => (
                <View key={i} style={[styles.txItem, i === 0 && { borderTopWidth: 0 }]}>
                    <View style={styles.txLeft}>
                        <Text style={styles.txDate}>{tx.date || tx.created_at?.slice(0, 10)}</Text>
                        <Text style={styles.txRef} numberOfLines={1}>{tx.id} • {tx.product || tx.description}</Text>
                    </View>
                    <View style={styles.txRight}>
                        <Text style={[styles.txAmount, tx.amount > 0 ? { color: theme.colors.green } : { color: theme.colors.red }]}>{tx.amount > 0 ? '+' : ''}${Math.abs(tx.amount).toFixed(2)}</Text>
                        <Text style={styles.txStatus}>{tx.status}</Text>
                    </View>
                </View>
            ))}
        </View>
        <TouchableOpacity style={styles.viewAllBtn}>
          <Text style={styles.viewAllText}>View All Transactions</Text>
          <IconChevronRight size={16} color={theme.colors.sky} />
        </TouchableOpacity>
      </View>

      {/* Saved Payment Methods */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>SAVED PAYMENT METHODS</Text>
        <View style={styles.card}>
            <View style={styles.methodRow}>
                <View style={styles.methodIconBox}>
                  <IconCreditCard size={20} color={theme.colors.sky} />
                </View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.methodTitle}>{balance?.payment_method || 'No payment method saved'}</Text>
                    <Text style={styles.methodSub}>{balance?.payment_method ? '[Default Payment Method]' : ''}</Text>
                </View>
            </View>
        </View>
        <TouchableOpacity style={styles.addBtn}>
          <IconPlus size={18} color="#999" style={{ marginRight: 8 }} />
          <Text style={styles.addBtnText}>Add New Payment Method</Text>
        </TouchableOpacity>
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  header: { padding: 24, paddingTop: 60, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backCircle: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F5F5F5', justifyContent: 'center', alignItems: 'center' },
  headerTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.black },
  section: { marginTop: 24, paddingHorizontal: 24 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#999', letterSpacing: 1.2, marginBottom: 16 },
  balanceCard: { padding: 40, backgroundColor: theme.colors.black, borderRadius: 24, alignItems: 'center' },
  currencySymbol: { color: theme.colors.sky, fontSize: 24, fontWeight: '700' },
  balanceValue: { color: '#FFF', fontSize: 44, fontWeight: '900', marginTop: 4 },
  balanceTag: { color: '#666', fontSize: 12, fontWeight: '700', marginTop: 8 },
  actionRow: { flexDirection: 'row', gap: 12, marginTop: 32 },
  actionBtn: { flex: 1, paddingVertical: 12, paddingHorizontal: 8, backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 12, alignItems: 'center' },
  actionBtnText: { color: '#FFF', fontSize: 11, fontWeight: '700' },
  depositCard: { marginTop: 14, backgroundColor: '#FFF', borderRadius: 18, padding: 16, borderWidth: 1, borderColor: '#EEE' },
  inputLabel: { color: '#64748b', fontSize: 12, fontWeight: '900', textTransform: 'uppercase', marginBottom: 8 },
  depositInput: { backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 14, padding: 14, fontSize: 17, fontWeight: '900' },
  depositBtn: { backgroundColor: theme.colors.green, borderRadius: 14, paddingVertical: 14, alignItems: 'center', marginTop: 12 },
  depositBtnText: { color: '#FFF', fontWeight: '900' },
  listCard: { backgroundColor: '#F9F9F9', borderRadius: 20, overflow: 'hidden' },
  txItem: { flexDirection: 'row', justifyContent: 'space-between', padding: 20, borderTopWidth: 1, borderTopColor: '#EEE' },
  txLeft: { flex: 1, paddingRight: 12 },
  txDate: { fontSize: 12, fontWeight: '800', color: '#999' },
  txRef: { fontSize: 15, fontWeight: '700', color: theme.colors.black, marginTop: 4 },
  txRight: { alignItems: 'flex-end' },
  txAmount: { fontSize: 16, fontWeight: '800', textAlign: 'right' },
  txStatus: { fontSize: 11, fontWeight: '800', textAlign: 'right', marginTop: 4, color: '#999', textTransform: 'uppercase' },
  viewAllBtn: { marginVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4 },
  viewAllText: { fontSize: 14, fontWeight: '700', color: theme.colors.sky },
  card: { padding: 24, backgroundColor: '#FFF', borderRadius: 20, borderWidth: 1, borderColor: '#EEE' },
  methodRow: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  methodIconBox: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#F0F9FF', justifyContent: 'center', alignItems: 'center' },
  methodTitle: { fontSize: 15, fontWeight: '700', color: theme.colors.black },
  methodSub: { fontSize: 12, color: theme.colors.green, fontWeight: '700', marginTop: 2 },
  addBtn: { margin: 24, paddingVertical: 14, borderStyle: 'dashed', borderWidth: 2, borderColor: '#DDD', borderRadius: 16, alignItems: 'center', flexDirection: 'row', justifyContent: 'center' },
  addBtnText: { color: '#999', fontWeight: '800', fontSize: 14 },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#EEE' },
  label: { fontSize: 14, fontWeight: '700', color: theme.colors.black },
  value: { fontSize: 14, fontWeight: '800', color: theme.colors.black },
  valueRed: { fontSize: 14, fontWeight: '800', color: theme.colors.red || '#dc2626' },
  valueGreen: { fontSize: 14, fontWeight: '800', color: theme.colors.green },
  divider: { height: 1, backgroundColor: '#EEE', marginVertical: 8 }
});
