import React, { useEffect, useState } from 'react';
import { CheckCircle, Crown, TrendingUp } from 'lucide-react';
import { getEnterpriseFeatureAccess, getSubscription, getSubscriptionPlans, setSubscription } from '../api.ts';

export function SubscriptionManagement() {
  const [subscription, setCurrent] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [entitlements, setEntitlements] = useState({ team_accounts: false, advanced_analytics: false });

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [current, availablePlans, enterpriseAccess] = await Promise.all([getSubscription(), getSubscriptionPlans(), getEnterpriseFeatureAccess()]);
      setCurrent(current);
      setPlans(availablePlans);
      setEntitlements(enterpriseAccess);
    } catch (err) {
      setError(err.message || 'Unable to load memberships');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const activate = async (code) => {
    setError('');
    try {
      await setSubscription(code, 'MONTHLY');
      await load();
    } catch (err) {
      setError(err.message || 'Unable to update membership');
    }
  };

  if (loading) {
    return <div className="rounded-2xl bg-white p-8 font-black text-earth-500">Loading membership...</div>;
  }

  const currentCode = subscription?.subscription_plan || subscription?.plan?.code || 'basic';
  const savings = subscription?.savings || {};

  return (
    <div className="space-y-6">
      <div className="rounded-[2rem] bg-gradient-to-br from-primary-700 to-earth-900 text-white p-8 relative overflow-hidden">
        <Crown className="absolute right-8 top-8 opacity-20" size={120} />
        <p className="text-xs font-black uppercase tracking-[0.3em] text-primary-100">Supplier Membership</p>
        <h2 className="text-3xl font-black mt-3">Grow with lower sales fees and stronger product visibility.</h2>
        <p className="mt-3 max-w-2xl font-bold text-primary-50">Subscriptions never block orders. They reduce fees, improve ranking, and unlock supplier growth tools.</p>
      </div>

      {error && <div className="rounded-xl bg-red-50 text-red-700 p-4 font-bold">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Metric label="Current Plan" value={(subscription?.plan?.name || currentCode).toUpperCase()} helper={`${subscription?.plan?.platform_fee_percent || 8}% sales fee`} />
        <Metric label="Total Fees Paid" value={`$${Number(savings.total_fees_paid || 0).toFixed(2)}`} helper="From completed supplier sales" />
        <Metric label="Total Fees Saved" value={`$${Number(savings.total_fees_saved || 0).toFixed(2)}`} helper="Compared with Basic fees" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Metric label="Team Accounts" value={entitlements.team_accounts ? "ENABLED" : "LOCKED"} helper="Enterprise feature access" />
        <Metric label="Advanced Analytics" value={entitlements.advanced_analytics ? "ENABLED" : "LOCKED"} helper="Enterprise feature access" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const active = currentCode === plan.code;
          return (
            <article key={plan.code} className={`bg-white rounded-[2rem] p-6 border-2 ${active ? 'border-primary-500 shadow-xl' : 'border-earth-100'}`}>
              <div className="flex justify-between gap-3">
                <h3 className="text-2xl font-black text-earth-900">{plan.name}</h3>
                {active && <span className="h-fit rounded-full bg-primary-100 text-primary-700 px-3 py-1 text-xs font-black">ACTIVE</span>}
              </div>
              <div className="mt-5">
                <span className="text-4xl font-black text-earth-900">${plan.monthly_price}</span>
                <span className="font-bold text-earth-400"> / month</span>
              </div>
              <div className="mt-4 flex items-center gap-2 text-primary-700 font-black">
                <TrendingUp size={18} />
                {plan.platform_fee_percent}% supplier sales fee
              </div>
              <ul className="mt-6 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex gap-3 text-sm font-bold text-earth-600">
                    <CheckCircle size={18} className="text-primary-600 shrink-0 mt-0.5" />
                    {feature}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => activate(plan.code)}
                disabled={active}
                className={`mt-8 w-full rounded-xl py-3 font-black ${active ? 'bg-earth-100 text-earth-400' : 'bg-primary-600 text-white hover:bg-primary-700'}`}
              >
                {active ? 'Current Plan' : `Move to ${plan.name}`}
              </button>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function Metric({ label, value, helper }) {
  return (
    <div className="bg-white rounded-2xl p-6 border border-earth-100">
      <p className="text-xs font-black uppercase tracking-widest text-earth-400">{label}</p>
      <p className="text-2xl font-black text-earth-900 mt-2">{value}</p>
      <p className="text-sm font-bold text-earth-500 mt-1">{helper}</p>
    </div>
  );
}
