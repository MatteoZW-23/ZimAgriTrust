import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useAuthStore, useWalletStore, Card, Button, Input } from '@agritrust/shared';
import { getWalletBalance, getTransactionHistory, initiateWithdrawal, createDeposit, getPayoutMethods, createPayoutMethod, updatePayoutMethod, deletePayoutMethod, verifyPayoutMethod, setDefaultPayoutMethod } from '../api';
import { Wallet, ArrowUpCircle, ArrowDownCircle, Clock, CheckCircle2, X, AlertCircle, Plus, ShieldCheck, BadgeCheck, Trash2, Star } from 'lucide-react';

type PayoutMethod = {
  id: string;
  method_type: 'ecocash' | 'onemoney' | 'bank_account';
  provider: 'ecocash' | 'onemoney' | 'bank';
  account_name: string;
  account_number?: string | null;
  bank_name?: string | null;
  branch_code?: string | null;
  is_default: boolean;
  status: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'DISABLED';
};

export const WalletPanel: React.FC = () => {
  const { user } = useAuthStore();
  const { balance, transactions, loading, fetchWalletData } = useWalletStore();
  const [walletBalance, setWalletBalance] = useState<number | null>(null);
  const [txHistory, setTxHistory] = useState<any[]>([]);
  const [methods, setMethods] = useState<PayoutMethod[]>([]);
  const [fetching, setFetching] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'methods' | 'deposit' | 'withdraw'>('overview');
  const [showDeposit, setShowDeposit] = useState(false);
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [showMethod, setShowMethod] = useState(false);
  const [editingMethod, setEditingMethod] = useState<PayoutMethod | null>(null);
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('ecocash');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [methodForm, setMethodForm] = useState({
    method_type: 'ecocash',
    provider: 'ecocash',
    account_name: '',
    account_number: '',
    bank_name: '',
    branch_code: '',
    is_default: false,
  });

  const loadWallet = useCallback(async () => {
    setFetching(true);
    try { fetchWalletData(); } catch {}
    try {
      const [bal, txs, payoutMethods] = await Promise.allSettled([
        getWalletBalance(),
        getTransactionHistory(),
        getPayoutMethods(),
      ]);
      if (bal.status === 'fulfilled' && bal.value) setWalletBalance(bal.value.balance_usd ?? bal.value.balance ?? bal.value.available ?? null);
      if (txs.status === 'fulfilled' && txs.value) setTxHistory(Array.isArray(txs.value) ? txs.value : txs.value.transactions || []);
      if (payoutMethods.status === 'fulfilled' && Array.isArray(payoutMethods.value)) setMethods(payoutMethods.value);
    } catch {}
    setFetching(false);
  }, [fetchWalletData]);

  useEffect(() => {
    loadWallet();
  }, [loadWallet]);

  const handleDeposit = useCallback(async () => {
    if (!amount || parseFloat(amount) <= 0) { setError('Enter a valid amount'); return; }
    setSubmitting(true); setError(''); setSuccess('');
    try {
      await createDeposit({ amount: parseFloat(amount), channel: method });
      setSuccess('Deposit initiated. Follow the payment prompt.');
      setAmount('');
      setTimeout(() => { setShowDeposit(false); setSuccess(''); loadWallet(); }, 1500);
    } catch (err: any) {
      setError(err.message || 'Deposit failed');
    }
    setSubmitting(false);
  }, [amount, method, loadWallet]);

  const handleWithdraw = useCallback(async () => {
    if (!amount || parseFloat(amount) <= 0) { setError('Enter a valid amount'); return; }
    const chosen = methods.find((m) => m.id === method);
    if (!chosen) { setError('Select a payout method'); return; }
    if (chosen.status !== 'VERIFIED') { setError('Withdrawal requires a verified payout method'); return; }
    setSubmitting(true); setError(''); setSuccess('');
    try {
      await initiateWithdrawal(parseFloat(amount), chosen.provider);
      setSuccess('Withdrawal submitted successfully.');
      setAmount('');
      setTimeout(() => { setShowWithdraw(false); setSuccess(''); loadWallet(); }, 1500);
    } catch (err: any) {
      setError(err.message || 'Withdrawal failed');
    }
    setSubmitting(false);
  }, [amount, method, methods, loadWallet]);

  const submitMethod = useCallback(async () => {
    if (!methodForm.account_name.trim()) { setError('Enter an account name'); return; }
    setSubmitting(true);
    setError('');
    try {
      const payload = {
        ...methodForm,
        method_type: methodForm.method_type,
        provider: methodForm.provider,
      };
      if (editingMethod) {
        await updatePayoutMethod(editingMethod.id, payload);
      } else {
        await createPayoutMethod(payload);
      }
      setSuccess('Payout method saved.');
      setShowMethod(false);
      setEditingMethod(null);
      setMethodForm({ method_type: 'ecocash', provider: 'ecocash', account_name: '', account_number: '', bank_name: '', branch_code: '', is_default: false });
      loadWallet();
    } catch (err: any) {
      setError(err.message || 'Could not save payout method');
    }
    setSubmitting(false);
  }, [methodForm, editingMethod, loadWallet]);

  const displayBalance = walletBalance ?? balance ?? 0;
  const displayTx = txHistory.length > 0 ? txHistory : transactions;
  const isLoading = fetching && loading;

  const shownMethods = useMemo(() => methods, [methods]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="rounded-2xl bg-gradient-to-br from-blue-700 via-blue-600 to-gray-900 text-white p-8 md:p-10 shadow-lg">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-[11px] font-bold uppercase tracking-wider"><Wallet size={12} /> Financial Hub</p>
                <h1 className="mt-4 text-3xl md:text-4xl font-bold tracking-tight">Wallets, deposits, withdrawals, and payout methods in one place.</h1>
                <p className="mt-3 text-sm md:text-base text-white/80 font-medium leading-7">Manage money safely with verified payout methods and real transaction history.</p>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" className="border-white/20 text-white hover:bg-white hover:text-gray-900" onClick={() => { setActiveTab('deposit'); setShowDeposit(true); }}>
                  <ArrowDownCircle size={16} className="mr-2" /> Deposit
                </Button>
                <Button className="bg-white text-gray-900 hover:bg-gray-100" onClick={() => { setActiveTab('withdraw'); setShowWithdraw(true); }}>
                  <ArrowUpCircle size={16} className="mr-2" /> Withdraw
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 mb-8">
          {['overview', 'methods', 'deposit', 'withdraw'].map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab as any)} className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider ${activeTab === tab ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-300 border border-gray-200 dark:border-gray-700'}`}>
              {tab}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div className="md:col-span-1 rounded-2xl bg-blue-600 text-white border-none shadow-lg p-8">
            <div className="w-16 h-16 rounded-xl bg-white/20 flex items-center justify-center mb-6">
              <Wallet size={32} />
            </div>
            <p className="text-xs font-bold uppercase tracking-wider opacity-80 mb-2">Available Balance</p>
            <h2 className="text-5xl font-bold">${Number(displayBalance || 0).toFixed(2)}</h2>
            <div className="mt-8 pt-8 border-t border-white/10 space-y-4">
              <div className="flex justify-between items-center opacity-80 text-sm font-semibold"><span>Pending Balance</span><span>$0.00</span></div>
              <div className="flex justify-between items-center opacity-80 text-sm font-semibold"><span>Role</span><span className="uppercase">{user?.role || '—'}</span></div>
            </div>
          </div>

          <div className="md:col-span-2 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Payout Methods</h3>
                <Button variant="outline" onClick={() => { setEditingMethod(null); setShowMethod(true); }} className="border-gray-300 dark:border-gray-600">
                  <Plus size={16} className="mr-2" /> Add Method
                </Button>
              </div>
            </div>
            <div className="p-6 space-y-3">
              {shownMethods.length === 0 ? (
                <div className="py-10 text-center text-gray-500 font-semibold">No payout methods yet.</div>
              ) : shownMethods.map((m) => (
                <div key={m.id} className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-bold text-gray-900 dark:text-white">{m.account_name}</p>
                      {m.is_default && <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">Default</span>}
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${m.status === 'VERIFIED' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400' : m.status === 'REJECTED' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}`}>{m.status}</span>
                    </div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mt-1">{m.provider} • {m.account_number || m.branch_code || '—'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {!m.is_default && <button className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-blue-100 dark:hover:bg-blue-900/30 text-gray-500 hover:text-blue-600 transition-colors" onClick={async () => { await setDefaultPayoutMethod(m.id); loadWallet(); }}><Star size={16} /></button>}
                    <button className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-blue-100 dark:hover:bg-blue-900/30 text-gray-500 hover:text-blue-600 transition-colors" onClick={async () => { await verifyPayoutMethod(m.id); loadWallet(); }}><ShieldCheck size={16} /></button>
                    <button className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-blue-100 dark:hover:bg-blue-900/30 text-gray-500 hover:text-blue-600 transition-colors" onClick={() => { setEditingMethod(m); setMethodForm({ method_type: m.method_type, provider: m.provider, account_name: m.account_name, account_number: m.account_number || '', bank_name: m.bank_name || '', branch_code: m.branch_code || '', is_default: m.is_default }); setShowMethod(true); }}><BadgeCheck size={16} /></button>
                    <button className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-500 hover:text-red-600 transition-colors" onClick={async () => { await deletePayoutMethod(m.id); loadWallet(); }}><Trash2 size={16} /></button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Recent Transactions</h3>
              <button className="text-sm font-bold text-blue-600 hover:text-blue-700">See All</button>
            </div>
          </div>
          <div className="p-6 space-y-4">
            {isLoading ? [...Array(3)].map((_, i) => <div key={i} className="h-16 bg-gray-100 dark:bg-gray-700 rounded-xl animate-pulse"></div>) : displayTx.length === 0 ? (
              <div className="py-16 text-center text-gray-500 font-semibold italic">No transactions yet. Your activity will appear here.</div>
            ) : displayTx.slice(0, 10).map((tx, idx) => (
              <div key={tx.id || idx} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50 group hover:bg-white dark:hover:bg-gray-700 border-2 border-transparent hover:border-gray-200 dark:hover:border-gray-600 transition-all">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${String(tx.type).toLowerCase().includes('deposit') || String(tx.type).toLowerCase().includes('payment') ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'}`}>
                    {String(tx.type).toLowerCase().includes('deposit') || String(tx.type).toLowerCase().includes('payment') ? <ArrowDownCircle size={20} /> : <ArrowUpCircle size={20} />}
                  </div>
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white capitalize">{tx.type || tx.description || 'Transaction'}</p>
                    <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase">{tx.created_at ? new Date(tx.created_at).toLocaleDateString() : '—'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-bold text-lg ${String(tx.type).toLowerCase().includes('deposit') || String(tx.type).toLowerCase().includes('payment') ? 'text-emerald-600' : 'text-red-600'}`}>
                    {String(tx.type).toLowerCase().includes('deposit') || String(tx.type).toLowerCase().includes('payment') ? '+' : '-'}${Number(tx.amount ?? 0).toFixed(2)}
                  </p>
                  <div className="flex items-center justify-end gap-1 mt-1">
                    {String(tx.status).toLowerCase() === 'completed' ? <CheckCircle2 size={12} className="text-emerald-500" /> : <Clock size={12} className="text-yellow-500" />}
                    <span className="text-[10px] font-bold uppercase text-gray-500 dark:text-gray-400">{tx.status || 'pending'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {showMethod && (
          <Modal title={editingMethod ? 'Edit Payout Method' : 'Add Payout Method'} onClose={() => { setShowMethod(false); setEditingMethod(null); }}>
            {error && <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-xl mb-4 text-red-600 dark:text-red-400 text-xs font-bold"><AlertCircle size={14} />{error}</div>}
            {success && <div className="flex items-center gap-2 p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl mb-4 text-emerald-600 dark:text-emerald-400 text-xs font-bold"><CheckCircle2 size={14} />{success}</div>}
            <div className="space-y-4">
              <Input label="Account Name" value={methodForm.account_name} onChange={(e) => setMethodForm({ ...methodForm, account_name: e.target.value })} />
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Method Type</label>
                  <select className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" value={methodForm.method_type} onChange={(e) => setMethodForm({ ...methodForm, method_type: e.target.value, provider: e.target.value === 'bank_account' ? 'bank' : e.target.value })}>
                    <option value="ecocash">EcoCash</option>
                    <option value="onemoney">OneMoney</option>
                    <option value="bank_account">Bank Account</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Provider</label>
                  <select className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" value={methodForm.provider} onChange={(e) => setMethodForm({ ...methodForm, provider: e.target.value })}>
                    <option value="ecocash">EcoCash</option>
                    <option value="onemoney">OneMoney</option>
                    <option value="bank">Bank</option>
                  </select>
                </div>
              </div>
              {(methodForm.method_type === 'ecocash' || methodForm.method_type === 'onemoney') && <Input label="Mobile Number" value={methodForm.account_number} onChange={(e) => setMethodForm({ ...methodForm, account_number: e.target.value })} />}
              {methodForm.method_type === 'bank_account' && (
                <>
                  <Input label="Bank Name" value={methodForm.bank_name} onChange={(e) => setMethodForm({ ...methodForm, bank_name: e.target.value })} />
                  <Input label="Account Number" value={methodForm.account_number} onChange={(e) => setMethodForm({ ...methodForm, account_number: e.target.value })} />
                  <Input label="Branch Code" value={methodForm.branch_code} onChange={(e) => setMethodForm({ ...methodForm, branch_code: e.target.value })} />
                </>
              )}
              <label className="flex items-center gap-3 font-semibold text-sm text-gray-700 dark:text-gray-300">
                <input type="checkbox" checked={methodForm.is_default} onChange={(e) => setMethodForm({ ...methodForm, is_default: e.target.checked })} />
                Set as default
              </label>
              <div className="flex gap-3">
                <Button fullWidth loading={submitting} onClick={submitMethod} className="bg-blue-600 hover:bg-blue-700">Save Method</Button>
                <Button variant="ghost" onClick={() => setShowMethod(false)} className="text-gray-600 dark:text-gray-400">Cancel</Button>
              </div>
            </div>
          </Modal>
        )}

        {showDeposit && (
          <Modal title="Deposit Funds" onClose={() => setShowDeposit(false)}>
            <div className="space-y-5">
              <Input label="Amount (USD)" type="number" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} />
              <div className="grid grid-cols-2 gap-3">
                {['ecocash', 'onemoney', 'bank_transfer', 'innbucks', 'zipit'].map((m) => (
                  <button key={m} type="button" onClick={() => setMethod(m)} className={`p-4 rounded-xl border-2 transition-all text-left ${method === m ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/30' : 'border-gray-200 dark:border-gray-700'}`}>
                    <p className="font-bold text-xs text-gray-900 dark:text-white uppercase">{m}</p>
                  </button>
                ))}
              </div>
              <Button fullWidth size="lg" loading={submitting} onClick={handleDeposit} className="bg-blue-600 hover:bg-blue-700">Confirm Deposit</Button>
            </div>
          </Modal>
        )}

        {showWithdraw && (
          <Modal title="Withdraw Funds" onClose={() => setShowWithdraw(false)}>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Available: <span className="font-bold text-gray-900 dark:text-white">${Number(displayBalance || 0).toFixed(2)}</span></p>
            <div className="space-y-5">
              <Input label="Amount (USD)" type="number" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} />
              <div className="space-y-3">
                <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Select verified payout method</p>
                {shownMethods.filter((m) => m.status === 'VERIFIED').map((m) => (
                  <button key={m.id} type="button" onClick={() => setMethod(m.id)} className={`w-full p-4 rounded-xl border-2 transition-all text-left ${method === m.id ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/30' : 'border-gray-200 dark:border-gray-700'}`}>
                    <p className="font-bold text-gray-900 dark:text-white">{m.account_name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{m.provider} • {m.account_number || m.branch_code || '—'}</p>
                  </button>
                ))}
              </div>
              <Button fullWidth size="lg" loading={submitting} onClick={handleWithdraw} className="bg-blue-600 hover:bg-blue-700">Confirm Withdrawal</Button>
            </div>
          </Modal>
        )}
      </div>
    </div>
  );
};

const Modal = ({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={onClose}>
    <div className="bg-white dark:bg-earth-800 rounded-3xl shadow-2xl w-full max-w-2xl p-8" onClick={(e) => e.stopPropagation()}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-black text-earth-800 dark:text-white">{title}</h3>
        <button onClick={onClose} className="p-2 hover:bg-earth-100 dark:hover:bg-earth-700 rounded-xl"><X size={20} /></button>
      </div>
      {children}
    </div>
  </div>
);
