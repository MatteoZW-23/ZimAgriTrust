import React, { useEffect, useState, useCallback } from 'react';
import { useAuthStore } from '@agritrust/shared';
import { CheckCircle2, Crown, TrendingUp, RefreshCw, BadgeCheck } from 'lucide-react';
import { getMySubscription, getSubscriptionPlans, upgradeSubscription, cancelSubscription } from '../api';

export const SubscriptionPanel: React.FC = () => {
  const { user } = useAuthStore();
  const role = (user?.role || 'farmer').toLowerCase();
  const [plans, setPlans] = useState<any[]>([]);
  const [subscription, setSubscription] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [planData, current] = await Promise.all([getSubscriptionPlans(role), getMySubscription()]);
      setPlans(planData);
      setSubscription(current);
    } catch (err: any) {
      setError(err.message || 'Unable to load subscriptions');
    } finally {
      setLoading(false);
    }
  }, [role]);

  useEffect(() => {
    load();
  }, [load]);

  const currentCode = subscription?.plan?.code;
  const savings = subscription?.savings || {};

  const changePlan = useCallback(async (code: string) => {
    setError('');
    try {
      const next = await upgradeSubscription(code, 'MONTHLY');
      setSubscription(next);
      await load();
    } catch (err: any) {
      setError(err.message || 'Unable to update plan');
    }
  }, [load]);

  const renewPlan = useCallback(async () => {
    if (!currentCode) return;
    await changePlan(currentCode);
  }, [currentCode, changePlan]);

  const cancelPlan = useCallback(async () => {
    setError('');
    try {
      await cancelSubscription();
      await load();
    } catch (err: any) {
      setError(err.message || 'Unable to cancel plan');
    }
  }, [load]);

  if (loading) {
    return <div className="p-8 rounded-2xl bg-white dark:bg-gray-800 font-bold text-gray-500">Loading membership...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="rounded-2xl bg-gradient-to-br from-blue-700 to-gray-900 text-white p-8 shadow-lg overflow-hidden relative">
            <div className="absolute right-8 top-8 opacity-20"><Crown size={120} /></div>
            <p className="text-sm font-bold uppercase tracking-wider text-blue-100">Membership Growth Engine</p>
            <h1 className="text-4xl font-bold mt-3">Lower fees, higher visibility, stronger trust.</h1>
            <p className="mt-4 max-w-2xl text-blue-50 font-semibold">Core trading stays open on every plan. Membership increases earnings through reduced platform fees, badges, priority ranking, and better business tools.</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button onClick={renewPlan} className="inline-flex items-center gap-2 rounded-xl bg-white text-blue-700 px-4 py-2 font-bold text-sm hover:bg-gray-100 transition-colors">
                <RefreshCw size={16} /> Renew
              </button>
              <button onClick={cancelPlan} className="inline-flex items-center gap-2 rounded-xl bg-white/10 text-white px-4 py-2 font-bold text-sm hover:bg-white/20 transition-colors">
                Cancel Plan
              </button>
            </div>
          </div>
        </div>

        {error && <div className="rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 p-4 font-semibold mb-8">{error}</div>}

        <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="rounded-2xl bg-white dark:bg-gray-800 p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Current Plan</p>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{subscription?.plan?.name}</h2>
            <p className="text-blue-600 font-semibold mt-1">{subscription?.plan?.platform_fee_percent}% platform fee</p>
          </div>
          <div className="rounded-2xl bg-white dark:bg-gray-800 p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total Fees Saved</p>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mt-2">${Number(savings.total_fees_saved || 0).toFixed(2)}</h2>
            <p className="text-gray-500 dark:text-gray-400 font-semibold mt-1">Compared with baseline fees</p>
          </div>
          <div className="rounded-2xl bg-white dark:bg-gray-800 p-6 border border-gray-200 dark:border-gray-700">
            <p className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Visibility</p>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{subscription?.plan?.visibility_weight}</h2>
            <p className="text-gray-500 dark:text-gray-400 font-semibold mt-1">Enterprise ranks highest, then Pro, then Free</p>
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const active = currentCode === plan.code;
            return (
              <article key={plan.code} className={`rounded-2xl p-6 border-2 bg-white dark:bg-gray-800 ${active ? 'border-blue-500 shadow-md' : 'border-gray-200 dark:border-gray-700'}`}>
                <div className="flex items-center justify-between">
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{plan.name}</h3>
                  {active && <span className="rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-3 py-1 text-xs font-bold inline-flex items-center gap-1"><BadgeCheck size={12} /> CURRENT</span>}
                </div>
                <div className="mt-5">
                  <span className="text-4xl font-bold text-gray-900 dark:text-white">${plan.monthly_price}</span>
                  <span className="text-gray-400 font-semibold"> / month</span>
                </div>
                <div className="mt-4 flex items-center gap-2 text-blue-700 dark:text-blue-400 font-semibold">
                  <TrendingUp size={18} />
                  {plan.platform_fee_percent}% fee
                </div>
                <ul className="mt-6 space-y-3">
                  {plan.features.map((feature: string) => (
                    <li key={feature} className="flex items-start gap-3 text-sm font-semibold text-gray-600 dark:text-gray-300">
                      <CheckCircle2 size={18} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  disabled={active}
                  onClick={() => changePlan(plan.code)}
                  className={`mt-8 w-full rounded-xl py-3 font-bold transition ${active ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-default' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
                >
                  {active ? 'Active Plan' : `Move to ${plan.name}`}
                </button>
              </article>
            );
          })}
        </section>
      </div>
    </div>
  );
};
