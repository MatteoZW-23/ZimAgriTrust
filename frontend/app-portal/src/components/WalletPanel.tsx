import React, { useEffect, useState } from 'react';
import { useAuthStore, useWalletStore, Card, Button, Input } from '@agritrust/shared';
import { getWalletBalance, getTransactionHistory, initiateWithdrawal, createDeposit } from '../api';
import { Wallet, ArrowUpCircle, ArrowDownCircle, Clock, CheckCircle2, X, Smartphone, Building2, Loader2, AlertCircle } from 'lucide-react';

export const WalletPanel: React.FC = () => {
  const { user } = useAuthStore();
  const { balance, transactions, loading, fetchWalletData } = useWalletStore();
  const [walletBalance, setWalletBalance] = useState<number | null>(null);
  const [txHistory, setTxHistory] = useState<any[]>([]);
  const [fetching, setFetching] = useState(true);

  // Modal state
  const [showDeposit, setShowDeposit] = useState(false);
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('mobile_money');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadWallet();
  }, []);

  const loadWallet = async () => {
    setFetching(true);
    try {
      fetchWalletData();
    } catch {}
    try {
      const [bal, txs] = await Promise.allSettled([
        getWalletBalance(),
        getTransactionHistory(),
      ]);
      if (bal.status === 'fulfilled' && bal.value) {
        setWalletBalance(bal.value.balance ?? bal.value.available ?? null);
      }
      if (txs.status === 'fulfilled' && txs.value) {
        setTxHistory(Array.isArray(txs.value) ? txs.value : txs.value.transactions || []);
      }
    } catch {}
    setFetching(false);
  };

  const handleDeposit = async () => {
    if (!amount || parseFloat(amount) <= 0) { setError('Enter a valid amount'); return; }
    setSubmitting(true); setError(''); setSuccess('');
    try {
      await createDeposit({ amount: parseFloat(amount), channel: method });
      setSuccess('Deposit initiated! Follow payment instructions.');
      setAmount('');
      setTimeout(() => { setShowDeposit(false); setSuccess(''); loadWallet(); }, 2000);
    } catch (err: any) {
      setError(err.message || 'Deposit failed');
    }
    setSubmitting(false);
  };

  const handleWithdraw = async () => {
    if (!amount || parseFloat(amount) <= 0) { setError('Enter a valid amount'); return; }
    setSubmitting(true); setError(''); setSuccess('');
    try {
      await initiateWithdrawal(parseFloat(amount), method);
      setSuccess('Withdrawal initiated! Funds will arrive shortly.');
      setAmount('');
      setTimeout(() => { setShowWithdraw(false); setSuccess(''); loadWallet(); }, 2000);
    } catch (err: any) {
      setError(err.message || 'Withdrawal failed');
    }
    setSubmitting(false);
  };

  const displayBalance = walletBalance ?? balance;
  const displayTx = txHistory.length > 0 ? txHistory : transactions;
  const isLoading = fetching && loading;

  const ModalOverlay = ({ children, onClose }: { children: React.ReactNode; onClose: () => void }) => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="bg-white dark:bg-earth-800 rounded-3xl shadow-2xl w-full max-w-md p-8" onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-earth-800 dark:text-white">My Wallet</h1>
          <p className="text-earth-500 font-bold mt-1">Manage your funds and transaction history.</p>
        </div>
        <div className="flex gap-4">
          <Button variant="outline" onClick={() => { setShowDeposit(true); setError(''); setSuccess(''); setAmount(''); }}>
            <ArrowDownCircle size={18} className="mr-2" /> Deposit
          </Button>
          <Button onClick={() => { setShowWithdraw(true); setError(''); setSuccess(''); setAmount(''); }}>
            <ArrowUpCircle size={18} className="mr-2" /> Withdraw
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <Card className="md:col-span-1 bg-primary-600 text-white border-none shadow-2xl shadow-primary-200 p-8">
          <div className="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center mb-6">
            <Wallet size={32} />
          </div>
          <p className="text-xs font-black uppercase tracking-widest opacity-80 mb-2">Available Balance</p>
          <h2 className="text-5xl font-black">${displayBalance.toFixed(2)}</h2>
          <div className="mt-8 pt-8 border-t border-white/10 space-y-4">
            <div className="flex justify-between items-center opacity-80 text-sm font-bold">
              <span>Pending Escrow</span>
              <span>$0.00</span>
            </div>
            <div className="flex justify-between items-center opacity-80 text-sm font-bold">
              <span>Role</span>
              <span className="uppercase">{user?.role || '—'}</span>
            </div>
          </div>
        </Card>

        <Card className="md:col-span-2">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-black text-earth-800 dark:text-white">Recent Transactions</h3>
            <button className="text-sm font-black text-primary-600 hover:text-primary-700">See All</button>
          </div>

          <div className="space-y-4">
            {isLoading ? (
              [...Array(3)].map((_, i) => (
                <div key={i} className="h-16 bg-earth-50 dark:bg-earth-700 rounded-2xl animate-pulse"></div>
              ))
            ) : displayTx.length === 0 ? (
              <div className="py-20 text-center text-earth-400 font-bold italic">
                No transactions yet. Your activity will appear here.
              </div>
            ) : (
              displayTx.slice(0, 10).map((tx, idx) => (
                <div key={tx.id || idx} className="flex items-center justify-between p-4 rounded-2xl bg-earth-50 dark:bg-earth-700/50 group hover:bg-white dark:hover:bg-earth-700 border-2 border-transparent hover:border-earth-100 dark:hover:border-earth-600 transition-all">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${tx.type === 'deposit' || tx.type === 'payment' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                      {tx.type === 'deposit' || tx.type === 'payment' ? <ArrowDownCircle size={20} /> : <ArrowUpCircle size={20} />}
                    </div>
                    <div>
                      <p className="font-black text-earth-800 dark:text-white capitalize">{tx.type || tx.description || 'Transaction'}</p>
                      <p className="text-[10px] font-black text-earth-400 uppercase">{tx.created_at ? new Date(tx.created_at).toLocaleDateString() : '—'}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-black text-lg ${tx.type === 'deposit' || tx.type === 'payment' ? 'text-green-600' : 'text-red-600'}`}>
                      {tx.type === 'deposit' || tx.type === 'payment' ? '+' : '-'}${(tx.amount ?? 0).toFixed(2)}
                    </p>
                    <div className="flex items-center justify-end gap-1 mt-1">
                      {tx.status === 'completed' ? (
                        <CheckCircle2 size={12} className="text-green-500" />
                      ) : (
                        <Clock size={12} className="text-yellow-500" />
                      )}
                      <span className="text-[10px] font-black uppercase text-earth-400">{tx.status || 'pending'}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Deposit Modal */}
      {showDeposit && (
        <ModalOverlay onClose={() => setShowDeposit(false)}>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-black text-earth-800 dark:text-white">Deposit Funds</h3>
            <button onClick={() => setShowDeposit(false)} className="p-2 hover:bg-earth-100 dark:hover:bg-earth-700 rounded-xl"><X size={20} /></button>
          </div>
          {error && <div className="flex items-center gap-2 p-3 bg-red-50 rounded-xl mb-4 text-red-600 text-xs font-bold"><AlertCircle size={14} />{error}</div>}
          {success && <div className="flex items-center gap-2 p-3 bg-green-50 rounded-xl mb-4 text-green-600 text-xs font-bold"><CheckCircle2 size={14} />{success}</div>}
          <div className="space-y-5">
            <Input label="Amount (USD)" type="number" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} />
            <div>
              <p className="text-[10px] font-black text-earth-400 uppercase tracking-wider mb-2">Payment Method</p>
              <div className="grid grid-cols-2 gap-3">
                <button type="button" onClick={() => setMethod('mobile_money')} className={`flex items-center gap-3 p-4 rounded-2xl border-2 transition-all ${method === 'mobile_money' ? 'border-primary-500 bg-primary-50/50' : 'border-earth-100'}`}>
                  <Smartphone size={20} className="text-primary-600" />
                  <div className="text-left">
                    <p className="font-black text-xs text-earth-800 dark:text-white">Mobile Money</p>
                    <p className="text-[10px] text-earth-400">EcoCash / OneMoney</p>
                  </div>
                </button>
                <button type="button" onClick={() => setMethod('bank_transfer')} className={`flex items-center gap-3 p-4 rounded-2xl border-2 transition-all ${method === 'bank_transfer' ? 'border-primary-500 bg-primary-50/50' : 'border-earth-100'}`}>
                  <Building2 size={20} className="text-primary-600" />
                  <div className="text-left">
                    <p className="font-black text-xs text-earth-800 dark:text-white">Bank Transfer</p>
                    <p className="text-[10px] text-earth-400">RTGS / Nostro</p>
                  </div>
                </button>
              </div>
            </div>
            <Button fullWidth size="lg" loading={submitting} onClick={handleDeposit}>
              Confirm Deposit
            </Button>
          </div>
        </ModalOverlay>
      )}

      {/* Withdraw Modal */}
      {showWithdraw && (
        <ModalOverlay onClose={() => setShowWithdraw(false)}>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-black text-earth-800 dark:text-white">Withdraw Funds</h3>
            <button onClick={() => setShowWithdraw(false)} className="p-2 hover:bg-earth-100 dark:hover:bg-earth-700 rounded-xl"><X size={20} /></button>
          </div>
          <p className="text-sm text-earth-500 mb-4">Available: <span className="font-black text-earth-800 dark:text-white">${displayBalance.toFixed(2)}</span></p>
          {error && <div className="flex items-center gap-2 p-3 bg-red-50 rounded-xl mb-4 text-red-600 text-xs font-bold"><AlertCircle size={14} />{error}</div>}
          {success && <div className="flex items-center gap-2 p-3 bg-green-50 rounded-xl mb-4 text-green-600 text-xs font-bold"><CheckCircle2 size={14} />{success}</div>}
          <div className="space-y-5">
            <Input label="Amount (USD)" type="number" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} />
            <div>
              <p className="text-[10px] font-black text-earth-400 uppercase tracking-wider mb-2">Withdraw To</p>
              <div className="grid grid-cols-2 gap-3">
                <button type="button" onClick={() => setMethod('mobile_money')} className={`flex items-center gap-3 p-4 rounded-2xl border-2 transition-all ${method === 'mobile_money' ? 'border-primary-500 bg-primary-50/50' : 'border-earth-100'}`}>
                  <Smartphone size={20} className="text-primary-600" />
                  <div className="text-left">
                    <p className="font-black text-xs text-earth-800 dark:text-white">Mobile Money</p>
                    <p className="text-[10px] text-earth-400">EcoCash / OneMoney</p>
                  </div>
                </button>
                <button type="button" onClick={() => setMethod('bank_transfer')} className={`flex items-center gap-3 p-4 rounded-2xl border-2 transition-all ${method === 'bank_transfer' ? 'border-primary-500 bg-primary-50/50' : 'border-earth-100'}`}>
                  <Building2 size={20} className="text-primary-600" />
                  <div className="text-left">
                    <p className="font-black text-xs text-earth-800 dark:text-white">Bank Transfer</p>
                    <p className="text-[10px] text-earth-400">RTGS / Nostro</p>
                  </div>
                </button>
              </div>
            </div>
            <Button fullWidth size="lg" loading={submitting} onClick={handleWithdraw}>
              Confirm Withdrawal
            </Button>
          </div>
        </ModalOverlay>
      )}
    </div>
  );
};
