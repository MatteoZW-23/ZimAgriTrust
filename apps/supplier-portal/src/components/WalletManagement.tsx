import React, { useState, useEffect } from 'react';
import { getWallet, getWalletTransactions, withdraw, getEarnings } from '../api.ts';
import { DollarSign, ArrowUpRight, Download, TrendingUp } from 'lucide-react';

export function WalletManagement() {
  const [wallet, setWallet] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [earnings, setEarnings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawForm, setWithdrawForm] = useState({ amount: '', method: 'bank_transfer', account_details: '' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [w, tx, e] = await Promise.all([
        getWallet(),
        getWalletTransactions(50),
        getEarnings(),
      ]);
      setWallet(w);
      setTransactions(tx);
      setEarnings(e);
    } catch (err) {
      console.error('Load wallet error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async (e) => {
    e.preventDefault();
    try {
      await withdraw(parseFloat(withdrawForm.amount), withdrawForm.method, withdrawForm.account_details);
      setShowWithdrawModal(false);
      setWithdrawForm({ amount: '', method: 'bank_transfer', account_details: '' });
      loadData();
      alert('Withdrawal request submitted');
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading wallet...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black text-earth-800">Wallet Management</h2>
        <button
          onClick={() => setShowWithdrawModal(true)}
          className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white font-bold px-4 py-2 rounded-xl"
        >
          <ArrowUpRight className="w-5 h-5" /> Withdraw
        </button>
      </div>

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <BalanceCard icon={DollarSign} label="Available Balance" value={wallet?.available_balance || 0} color="green" />
        <BalanceCard icon={TrendingUp} label="Pending Balance" value={wallet?.pending_balance || 0} color="yellow" />
        <BalanceCard icon={DollarSign} label="Lifetime Earnings" value={earnings?.lifetime_earnings || 0} color="blue" />
      </div>

      {/* Earnings Summary */}
      {earnings && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="font-black text-earth-800 mb-4">Earnings Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-earth-600">Total Sales</p>
              <p className="text-xl font-black text-earth-800">{earnings.total_sales}</p>
            </div>
            <div>
              <p className="text-sm text-earth-600">Total Revenue</p>
              <p className="text-xl font-black text-earth-800">${earnings.total_revenue?.toFixed(2) || '0.00'}</p>
            </div>
            <div>
              <p className="text-sm text-earth-600">Total Withdrawn</p>
              <p className="text-xl font-black text-earth-800">${earnings.total_withdrawn?.toFixed(2) || '0.00'}</p>
            </div>
            <div>
              <p className="text-sm text-earth-600">Available</p>
              <p className="text-xl font-black text-earth-800">${earnings.available_balance?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Transactions */}
      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-earth-200 flex justify-between items-center">
          <h3 className="font-black text-earth-800">Transaction History</h3>
          <button className="flex items-center gap-2 text-sm text-earth-600 hover:text-earth-800">
            <Download className="w-4 h-4" /> Export
          </button>
        </div>
        <table className="w-full">
          <thead className="bg-earth-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Amount</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Fee</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Net</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-earth-600 uppercase">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-earth-200">
            {transactions.map((txn) => (
              <tr key={txn.id} className="hover:bg-earth-50">
                <td className="px-6 py-4 capitalize font-bold text-earth-800">{txn.txn_type}</td>
                <td className="px-6 py-4 font-bold text-earth-800">${txn.amount.toFixed(2)}</td>
                <td className="px-6 py-4 text-sm text-earth-600">${txn.fee.toFixed(2)}</td>
                <td className="px-6 py-4 font-bold text-earth-800">${txn.net_amount.toFixed(2)}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                    txn.status === 'completed' ? 'bg-green-100 text-green-700' :
                    txn.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {txn.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-earth-600">{new Date(txn.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {transactions.length === 0 && (
          <div className="text-center py-12 text-earth-500">No transactions yet</div>
        )}
      </div>

      {showWithdrawModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-black text-earth-800 mb-4">Withdraw Funds</h3>
            <p className="text-sm text-earth-600 mb-4">Available: ${wallet?.available_balance?.toFixed(2) || '0.00'}</p>
            <form onSubmit={handleWithdraw} className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Amount (USD) *</label>
                <input
                  type="number"
                  step="0.01"
                  min="50"
                  value={withdrawForm.amount}
                  onChange={(e) => setWithdrawForm({ ...withdrawForm, amount: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  required
                />
                <p className="text-xs text-earth-500 mt-1">Minimum withdrawal: $50</p>
              </div>
              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Method *</label>
                <select
                  value={withdrawForm.method}
                  onChange={(e) => setWithdrawForm({ ...withdrawForm, method: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                >
                  <option value="bank_transfer">Bank Transfer</option>
                  <option value="ecocash">EcoCash</option>
                  <option value="onemoney">OneMoney</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Account Details</label>
                <input
                  type="text"
                  value={withdrawForm.account_details}
                  onChange={(e) => setWithdrawForm({ ...withdrawForm, account_details: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  placeholder="Account number / phone number"
                />
              </div>
              <div className="flex gap-3 mt-6">
                <button type="submit" className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 rounded-xl">
                  Submit Withdrawal
                </button>
                <button type="button" onClick={() => setShowWithdrawModal(false)} className="flex-1 bg-earth-200 hover:bg-earth-300 text-earth-800 font-bold py-2 rounded-xl">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function BalanceCard({ icon: Icon, label, value, color }) {
  const colors = {
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    blue: 'bg-blue-50 text-blue-600',
  };
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className={`w-12 h-12 ${colors[color]} rounded-xl flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6" />
      </div>
      <p className="text-earth-600 font-bold text-sm">{label}</p>
      <p className="text-2xl font-black text-earth-800">${value.toFixed(2)}</p>
    </div>
  );
}
