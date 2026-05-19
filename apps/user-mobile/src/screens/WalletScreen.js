import React, { useState } from 'react';
import { ActivityIndicator, Alert, TextInput, View, Text, ScrollView, TouchableOpacity, StyleSheet, Modal } from 'react-native';
import { 
  ArrowLeft as IconArrowLeft, 
  Plus as IconPlus, 
  Download as IconDownload, 
  History as IconHistory, 
  ChevronRight as IconChevronRight,
  Wallet as IconWallet,
  CreditCard as IconCreditCard,
  X,
  Filter,
  ArrowUpDown,
  TrendingUp,
  TrendingDown,
  Clock
} from 'lucide-react-native';
import { theme } from '../styles';
import { depositFunds, getEarnings, getTransactions, getWalletBalance, withdrawFunds } from '../api';

export default function WalletScreen({ route, navigation }) {
  const { token, profile: initialProfile = {}, role } = route.params || {};
  const [profile, setProfile] = useState(initialProfile);
  const [balance, setBalance] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [depositing, setDepositing] = useState(false);
  const [depositMethod, setDepositMethod] = useState('ecocash');
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [withdrawing, setWithdrawing] = useState(false);
  const [withdrawMethod, setWithdrawMethod] = useState('ecocash');
  const [showSortModal, setShowSortModal] = useState(false);
  const [sortBy, setSortBy] = useState('newest');
  const [showAddPaymentModal, setShowAddPaymentModal] = useState(false);
  const [newPaymentMethod, setNewPaymentMethod] = useState('');
  const [addingPayment, setAddingPayment] = useState(false);

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
      await depositFunds(token, { amount, payment_method: depositMethod });
      setShowDeposit(false);
      setDepositAmount('');
      setBalance(await getWalletBalance(token));
      Alert.alert('Deposit started', `Follow the ${depositMethod.charAt(0).toUpperCase() + depositMethod.slice(1)} prompt to complete payment.`);
    } catch (err) {
      Alert.alert('Deposit failed', err.message || 'Could not start deposit.');
    } finally {
      setDepositing(false);
    }
  };

  const handleWithdraw = async () => {
    const amount = Number(withdrawAmount);
    const availableBalance = balance?.balance_usd || 0;
    
    if (!Number.isFinite(amount) || amount <= 0) {
      Alert.alert('Invalid amount', 'Enter a valid withdrawal amount.');
      return;
    }
    
    if (amount > availableBalance) {
      Alert.alert('Insufficient funds', `You only have $${availableBalance.toFixed(2)} available.`);
      return;
    }
    
    try {
      setWithdrawing(true);
      await withdrawFunds(token, { amount, payment_method: withdrawMethod });
      setShowWithdraw(false);
      setWithdrawAmount('');
      setBalance(await getWalletBalance(token));
      Alert.alert('Withdrawal started', 'Your withdrawal request has been submitted.');
    } catch (err) {
      Alert.alert('Withdrawal failed', err.message || 'Could not start withdrawal.');
    } finally {
      setWithdrawing(false);
    }
  };

  const sortTransactions = (txs) => {
    const sorted = [...txs];
    if (sortBy === 'newest') {
      return sorted.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    } else if (sortBy === 'oldest') {
      return sorted.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
    } else if (sortBy === 'highest') {
      return sorted.sort((a, b) => Math.abs(b.amount || 0) - Math.abs(a.amount || 0));
    } else if (sortBy === 'lowest') {
      return sorted.sort((a, b) => Math.abs(a.amount || 0) - Math.abs(b.amount || 0));
    }
    return sorted;
  };

  const handleAddPaymentMethod = async () => {
    if (!newPaymentMethod.trim()) {
      Alert.alert('Invalid', 'Please enter a payment method name.');
      return;
    }
    setAddingPayment(true);
    try {
      // Simulate API call - in real implementation, this would call an API
      await new Promise(resolve => setTimeout(resolve, 1000));
      Alert.alert('Success', 'Payment method added successfully.');
      setShowAddPaymentModal(false);
      setNewPaymentMethod('');
      // Refresh balance to get updated payment method
      setBalance(await getWalletBalance(token));
    } catch (err) {
      Alert.alert('Failed', err.message || 'Could not add payment method.');
    } finally {
      setAddingPayment(false);
    }
  };

  return (
    <>
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
                <TouchableOpacity style={styles.actionBtn} onPress={() => setShowDeposit(true)}>
                  <IconPlus size={16} color="#FFF" style={{ marginBottom: 4 }} />
                  <Text style={styles.actionBtnText}>Add Funds</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionBtn} onPress={() => setShowWithdraw(true)}>
                  <IconDownload size={16} color="#FFF" style={{ marginBottom: 4 }} />
                  <Text style={styles.actionBtnText}>Withdraw</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionBtn} onPress={() => setShowSortModal(true)}>
                  <ArrowUpDown size={16} color="#FFF" style={{ marginBottom: 4 }} />
                  <Text style={styles.actionBtnText}>Sort</Text>
                </TouchableOpacity>
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
                <View style={{ padding: 40, alignItems: 'center' }}>
                    <IconWallet size={40} color="#DDD" style={{ marginBottom: 12 }} />
                    <Text style={{ color: '#999', fontWeight: '700' }}>No transactions yet</Text>
                </View>
            ) : sortTransactions(transactions).map((tx, i) => (
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
        <TouchableOpacity style={styles.viewAllBtn} onPress={() => navigation.navigate('Transactions', { token, profile, role })}>
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
        <TouchableOpacity style={styles.addBtn} onPress={() => setShowAddPaymentModal(true)}>
          <IconPlus size={18} color="#999" style={{ marginRight: 8 }} />
          <Text style={styles.addBtnText}>Add New Payment Method</Text>
        </TouchableOpacity>
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>

    {/* Withdrawal Modal */}
    <Modal
      visible={showWithdraw}
      transparent
      animationType="slide"
      onRequestClose={() => setShowWithdraw(false)}
    >
      <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowWithdraw(false)}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Withdraw Funds</Text>
            <TouchableOpacity onPress={() => setShowWithdraw(false)}>
              <X size={24} color="#64748b" />
            </TouchableOpacity>
          </View>
          
          <View style={styles.balanceInfo}>
            <Text style={styles.balanceInfoLabel}>Available Balance</Text>
            <Text style={styles.balanceInfoValue}>${balance?.balance_usd?.toFixed(2) || '0.00'}</Text>
          </View>

          <Text style={styles.inputLabel}>Withdrawal amount (USD)</Text>
          <TextInput
            style={styles.modalInput}
            value={withdrawAmount}
            onChangeText={setWithdrawAmount}
            keyboardType="decimal-pad"
            placeholder="0.00"
            placeholderTextColor="#94a3b8"
          />

          <Text style={styles.inputLabel}>Withdrawal Method</Text>
          <View style={styles.methodOptions}>
            {['ecocash', 'onemoney', 'bank'].map(method => (
              <TouchableOpacity
                key={method}
                style={[styles.methodOption, withdrawMethod === method && styles.methodOptionActive]}
                onPress={() => setWithdrawMethod(method)}
              >
                <Text style={[styles.methodOptionText, withdrawMethod === method && styles.methodOptionTextActive]}>
                  {method.charAt(0).toUpperCase() + method.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity 
            style={[styles.modalConfirmBtn, withdrawing && styles.modalConfirmBtnDisabled]} 
            onPress={handleWithdraw}
            disabled={withdrawing}
          >
            {withdrawing ? <ActivityIndicator color="#fff" /> : <Text style={styles.modalConfirmText}>Withdraw Funds</Text>}
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Modal>

    {/* Deposit Modal */}
    <Modal
      visible={showDeposit}
      transparent
      animationType="slide"
      onRequestClose={() => setShowDeposit(false)}
    >
      <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowDeposit(false)}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Add Funds</Text>
            <TouchableOpacity onPress={() => setShowDeposit(false)}>
              <X size={24} color="#64748b" />
            </TouchableOpacity>
          </View>

          <Text style={styles.inputLabel}>Deposit amount (USD)</Text>
          <TextInput
            style={styles.modalInput}
            value={depositAmount}
            onChangeText={setDepositAmount}
            keyboardType="decimal-pad"
            placeholder="0.00"
            placeholderTextColor="#94a3b8"
          />

          <Text style={styles.inputLabel}>Payment Method</Text>
          <View style={styles.methodOptions}>
            {['ecocash', 'onemoney', 'bank'].map(method => (
              <TouchableOpacity
                key={method}
                style={[styles.methodOption, depositMethod === method && styles.methodOptionActive]}
                onPress={() => setDepositMethod(method)}
              >
                <Text style={[styles.methodOptionText, depositMethod === method && styles.methodOptionTextActive]}>
                  {method.charAt(0).toUpperCase() + method.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={[styles.modalConfirmBtn, depositing && styles.modalConfirmBtnDisabled]}
            onPress={handleDeposit}
            disabled={depositing}
          >
            {depositing ? <ActivityIndicator color="#fff" /> : <Text style={styles.modalConfirmText}>Add Funds</Text>}
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Modal>

    {/* Sort Modal */}
    <Modal
      visible={showSortModal}
      transparent
      animationType="slide"
      onRequestClose={() => setShowSortModal(false)}
    >
      <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowSortModal(false)}>
        <View style={styles.sortModalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Sort Transactions</Text>
            <TouchableOpacity onPress={() => setShowSortModal(false)}>
              <X size={24} color="#64748b" />
            </TouchableOpacity>
          </View>
          
          <TouchableOpacity 
            style={[styles.sortOption, sortBy === 'newest' && styles.sortOptionActive]} 
            onPress={() => { setSortBy('newest'); setShowSortModal(false); }}
          >
            <Clock size={18} color={sortBy === 'newest' ? '#fff' : '#64748b'} />
            <Text style={[styles.sortOptionText, sortBy === 'newest' && styles.sortOptionTextActive]}>Newest First</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.sortOption, sortBy === 'oldest' && styles.sortOptionActive]} 
            onPress={() => { setSortBy('oldest'); setShowSortModal(false); }}
          >
            <Clock size={18} color={sortBy === 'oldest' ? '#fff' : '#64748b'} />
            <Text style={[styles.sortOptionText, sortBy === 'oldest' && styles.sortOptionTextActive]}>Oldest First</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.sortOption, sortBy === 'highest' && styles.sortOptionActive]} 
            onPress={() => { setSortBy('highest'); setShowSortModal(false); }}
          >
            <TrendingUp size={18} color={sortBy === 'highest' ? '#fff' : '#64748b'} />
            <Text style={[styles.sortOptionText, sortBy === 'highest' && styles.sortOptionTextActive]}>Highest Amount</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.sortOption, sortBy === 'lowest' && styles.sortOptionActive]} 
            onPress={() => { setSortBy('lowest'); setShowSortModal(false); }}
          >
            <TrendingDown size={18} color={sortBy === 'lowest' ? '#fff' : '#64748b'} />
            <Text style={[styles.sortOptionText, sortBy === 'lowest' && styles.sortOptionTextActive]}>Lowest Amount</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Modal>

    {/* Add Payment Method Modal */}
    <Modal
      visible={showAddPaymentModal}
      transparent
      animationType="slide"
      onRequestClose={() => setShowAddPaymentModal(false)}
    >
      <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setShowAddPaymentModal(false)}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Add Payment Method</Text>
            <TouchableOpacity onPress={() => setShowAddPaymentModal(false)}>
              <X size={24} color="#64748b" />
            </TouchableOpacity>
          </View>

          <Text style={styles.inputLabel}>Payment Method Name</Text>
          <TextInput
            style={styles.modalInput}
            value={newPaymentMethod}
            onChangeText={setNewPaymentMethod}
            placeholder="e.g. EcoCash, OneMoney, Bank Account"
            placeholderTextColor="#94a3b8"
            autoCapitalize="words"
          />

          <TouchableOpacity
            style={[styles.modalConfirmBtn, addingPayment && styles.modalConfirmBtnDisabled]}
            onPress={handleAddPaymentMethod}
            disabled={addingPayment}
          >
            {addingPayment ? <ActivityIndicator color="#fff" /> : <Text style={styles.modalConfirmText}>Add Payment Method</Text>}
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Modal>
    </>
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
  divider: { height: 1, backgroundColor: '#EEE', marginVertical: 8 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24 },
  sortModalContent: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  modalTitle: { fontSize: 20, fontWeight: '900', color: '#111827' },
  balanceInfo: { backgroundColor: '#F0FDF4', borderRadius: 12, padding: 16, marginBottom: 16 },
  balanceInfoLabel: { fontSize: 12, fontWeight: '700', color: '#64748b', textTransform: 'uppercase' },
  balanceInfoValue: { fontSize: 24, fontWeight: '900', color: theme.colors.green, marginTop: 4 },
  modalInput: { backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 14, padding: 16, fontSize: 17, fontWeight: '900', marginBottom: 16 },
  methodOptions: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  methodOption: { flex: 1, paddingVertical: 12, borderRadius: 12, backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#E2E8F0', alignItems: 'center' },
  methodOptionActive: { backgroundColor: theme.colors.green, borderColor: theme.colors.green },
  methodOptionText: { fontSize: 13, fontWeight: '700', color: '#64748b' },
  methodOptionTextActive: { color: '#fff' },
  modalConfirmBtn: { backgroundColor: theme.colors.green, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  modalConfirmBtnDisabled: { backgroundColor: '#CBD5E1' },
  modalConfirmText: { color: '#fff', fontWeight: '900', fontSize: 16 },
  sortOption: { flexDirection: 'row', alignItems: 'center', padding: 16, borderRadius: 12, marginBottom: 8, backgroundColor: '#F8FAFC' },
  sortOptionActive: { backgroundColor: theme.colors.green },
  sortOptionText: { fontSize: 16, fontWeight: '700', color: '#64748b', marginLeft: 12 },
  sortOptionTextActive: { color: '#fff' },
});
