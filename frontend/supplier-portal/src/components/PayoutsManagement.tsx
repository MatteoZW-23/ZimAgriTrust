import React, { useState, useEffect } from 'react';
import { getPayoutHistory, getTaxReport } from '../api.ts';
import { DollarSign, Calendar, Download, FileText, TrendingUp, AlertCircle } from 'lucide-react';

export function PayoutsManagement() {
  const [payouts, setPayouts] = useState([]);
  const [totals, setTotals] = useState({ total_withdrawn: 0, total_fees: 0, total_net: 0 });
  const [loading, setLoading] = useState(true);
  const [taxYear, setTaxYear] = useState(new Date().getFullYear());
  const [taxMonth, setTaxMonth] = useState(null);
  const [taxReport, setTaxReport] = useState(null);

  useEffect(() => {
    loadPayouts();
  }, []);

  const loadPayouts = async () => {
    try {
      const data = await getPayoutHistory(50, 0);
      setPayouts(data.payouts || []);
      setTotals({
        total_withdrawn: data.total_withdrawn,
        total_fees: data.total_fees,
        total_net: data.total_net,
      });
    } catch (err) {
      console.error('Failed to load payouts:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTaxReport = async () => {
    try {
      const data = await getTaxReport(taxYear, taxMonth);
      setTaxReport(data);
    } catch (err) {
      console.error('Failed to load tax report:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  };

  return (
    <div className="space-y-6">
      {/* Payout Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          icon={DollarSign}
          label="Total Withdrawn"
          value={`$${totals.total_withdrawn.toFixed(2)}`}
          color="green"
        />
        <StatCard
          icon={TrendingUp}
          label="Total Fees"
          value={`$${totals.total_fees.toFixed(2)}`}
          color="red"
        />
        <StatCard
          icon={DollarSign}
          label="Net Payouts"
          value={`$${totals.total_net.toFixed(2)}`}
          color="blue"
        />
      </div>

      {/* Tax Report Generator */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-black text-earth-800 mb-4">Tax Report Generator</h3>
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="block text-sm font-bold text-earth-600 mb-2">Year</label>
            <select
              value={taxYear}
              onChange={(e) => setTaxYear(parseInt(e.target.value))}
              className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
            >
              {[2024, 2025, 2026].map((year) => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-bold text-earth-600 mb-2">Month (Optional)</label>
            <select
              value={taxMonth || ''}
              onChange={(e) => setTaxMonth(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full p-3 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none"
            >
              <option value="">Full Year</option>
              {['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'].map((month, i) => (
                <option key={month} value={i + 1}>{month}</option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={loadTaxReport}
          className="w-full py-3 bg-primary-600 text-white font-black rounded-xl hover:bg-primary-700 transition-colors"
        >
          Generate Report
        </button>

        {taxReport && (
          <div className="mt-6 bg-earth-50 rounded-xl p-6">
            <h4 className="font-black text-earth-800 mb-4">Tax Report: {taxReport.period}</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-earth-500">Total Gross</p>
                <p className="font-bold text-earth-800">${taxReport.total_gross.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-earth-500">Platform Fees</p>
                <p className="font-bold text-earth-800">${taxReport.total_platform_fees.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-earth-500">Net Income</p>
                <p className="font-bold text-earth-800">${taxReport.total_net.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-earth-500">Taxable Income</p>
                <p className="font-bold text-earth-800">${taxReport.taxable_income.toFixed(2)}</p>
              </div>
            </div>
            <button className="mt-4 flex items-center gap-2 text-primary-600 font-bold hover:text-primary-700">
              <Download size={16} />
              Download PDF
            </button>
          </div>
        )}
      </div>

      {/* Payout History */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-black text-earth-800 mb-4">Payout History</h3>
        {payouts.length === 0 ? (
          <p className="text-earth-500 text-center py-8">No payouts yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-earth-100">
                  <th className="text-left py-3 text-sm font-black text-earth-600 uppercase">Date</th>
                  <th className="text-left py-3 text-sm font-black text-earth-600 uppercase">Method</th>
                  <th className="text-right py-3 text-sm font-black text-earth-600 uppercase">Amount</th>
                  <th className="text-right py-3 text-sm font-black text-earth-600 uppercase">Fee</th>
                  <th className="text-right py-3 text-sm font-black text-earth-600 uppercase">Net</th>
                  <th className="text-center py-3 text-sm font-black text-earth-600 uppercase">Status</th>
                </tr>
              </thead>
              <tbody>
                {payouts.map((payout) => (
                  <tr key={payout.id} className="border-b border-earth-50">
                    <td className="py-4 text-earth-800">
                      {new Date(payout.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 text-earth-600 capitalize">{payout.method}</td>
                    <td className="py-4 text-right font-bold text-earth-800">
                      ${payout.amount.toFixed(2)}
                    </td>
                    <td className="py-4 text-right text-earth-600">
                      ${payout.fee.toFixed(2)}
                    </td>
                    <td className="py-4 text-right font-bold text-earth-800">
                      ${payout.net_amount.toFixed(2)}
                    </td>
                    <td className="py-4 text-center">
                      <span className={`px-3 py-1 rounded-lg text-xs font-black uppercase ${statusColors[payout.status]}`}>
                        {payout.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    blue: 'bg-blue-50 text-blue-600',
  };
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className={`w-12 h-12 ${colors[color]} rounded-xl flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6" />
      </div>
      <p className="text-earth-600 font-bold text-sm">{label}</p>
      <p className="text-2xl font-black text-earth-800">{value}</p>
    </div>
  );
}
