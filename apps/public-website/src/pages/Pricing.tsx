import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Check, TrendingUp } from 'lucide-react';

type Plan = {
  id?: string;
  role: string;
  code: string;
  name: string;
  monthly_price?: number;
  annual_price?: number;
  fee_percent?: number;
  features?: string[];
  benefits?: Array<{ label?: string; value?: any }>;
};

const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8080/api/v1';

const roleOrder = ['farmer', 'buyer', 'supplier'];

const Pricing = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      try {
        const roles = ['farmer', 'buyer', 'supplier'];
        const responses = await Promise.all(
          roles.map(async (role) => {
            const res = await fetch(`${API}/subscriptions/plans?role=${encodeURIComponent(role)}`);
            if (!res.ok) return [];
            const data = await res.json();
            return (Array.isArray(data) ? data : []).map((p: any) => ({
              ...p,
              role,
            }));
          }),
        );
        if (active) setPlans(responses.flat());
      } catch {
        if (active) setPlans([]);
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, []);

  const grouped = useMemo(() => {
    const byRole: Record<string, Plan[]> = {};
    for (const plan of plans) {
      const key = String(plan.role || '').toLowerCase();
      if (!byRole[key]) byRole[key] = [];
      byRole[key].push(plan);
    }
    return byRole;
  }, [plans]);

  const fees = useMemo(() => {
    const cards: Array<{ label: string; value: string; sub: string }> = [];
    for (const role of roleOrder) {
      const rolePlans = grouped[role] || [];
      if (!rolePlans.length) continue;
      const min = Math.min(...rolePlans.map((p) => Number(p.fee_percent ?? 0)));
      const max = Math.max(...rolePlans.map((p) => Number(p.fee_percent ?? 0)));
      const value = min === max ? `${min}%` : `${max}-${min}%`;
      cards.push({
        label: `${role.charAt(0).toUpperCase()}${role.slice(1)} fees`,
        value,
        sub: 'Configurable by platform governance',
      });
    }
    return cards;
  }, [grouped]);

  const planCards = roleOrder.flatMap((role) => grouped[role] || []);

  return (
    <div className="pt-24 pb-20">
      <div className="container-custom">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-4xl sm:text-5xl font-display font-bold text-earth-900 mb-6">
            Flexible, <span className="text-primary-600">Live</span> Pricing
          </motion.h1>
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="text-lg text-earth-600">
            Pricing and fees are loaded dynamically from the platform configuration.
          </motion.p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto mb-20">
          {loading ? (
            [...Array(6)].map((_, i) => <div key={i} className="h-72 rounded-3xl bg-earth-100 animate-pulse" />)
          ) : planCards.map((plan, i) => {
            const rawBenefits = Array.isArray(plan.benefits) ? plan.benefits : [];
            const benefitLabels = rawBenefits.map((b) => b?.label || b?.value?.text || b?.value).filter(Boolean);
            const features = Array.isArray(plan.features) && plan.features.length > 0 ? plan.features : benefitLabels;
            const monthly = Number(plan.monthly_price ?? 0);
            const badge = String(plan.name || '').toLowerCase() === 'pro';
            return (
              <motion.div
                key={`${plan.role}-${plan.code}-${plan.name}`}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                className={`relative bg-white rounded-3xl p-8 shadow-xl border-2 ${badge ? 'border-primary-500' : 'border-earth-100'}`}
              >
                {badge && <div className="absolute top-0 right-8 -translate-y-1/2 bg-primary-600 text-white px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest">Growth</div>}
                <p className="text-xs font-black uppercase tracking-[0.25em] text-primary-600 mb-3">{String(plan.role).toUpperCase()}</p>
                <h3 className="text-2xl font-bold text-earth-800 mb-2">{plan.name}</h3>
                <div className="flex items-baseline gap-1 mb-4">
                  <span className="text-5xl font-black text-earth-900">${monthly.toFixed(0)}</span>
                  <span className="text-earth-500 font-bold">/month</span>
                </div>
                <div className="flex items-center gap-2 text-primary-700 font-black mb-8">
                  <TrendingUp size={18} /> {Number(plan.fee_percent ?? 0)}% platform fee
                </div>
                <ul className="space-y-4 mb-8">
                  {(features.length ? features : ['Configurable benefits']).slice(0, 8).map((feat: any) => (
                    <li key={String(feat)} className="flex items-start gap-3 text-earth-700 font-medium">
                      <div className="w-5 h-5 rounded-full bg-primary-100 flex items-center justify-center shrink-0 mt-0.5">
                        <Check className="w-3 h-3 text-primary-600" />
                      </div>
                      {String(feat)}
                    </li>
                  ))}
                </ul>
                <button className={`w-full py-4 rounded-2xl font-black transition-all ${badge ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-200' : 'bg-earth-100 text-earth-700 hover:bg-earth-200'}`}>
                  {monthly <= 0 ? 'Start Free' : 'Increase Growth'}
                </button>
              </motion.div>
            );
          })}
        </div>

        <div className="bg-earth-900 rounded-[3rem] p-12 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 blur-[100px] rounded-full"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-secondary-500/10 blur-[100px] rounded-full"></div>
          <div className="relative z-10">
            <h2 className="text-3xl font-bold mb-12 text-center">Transaction Fees</h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
              {(fees.length ? fees : [{ label: 'Platform fees', value: 'Live', sub: 'Managed by admin config' }]).map((fee, i) => (
                <div key={i} className="text-center">
                  <p className="text-earth-400 font-bold uppercase tracking-widest text-xs mb-2">{fee.label}</p>
                  <p className="text-4xl font-black text-primary-500 mb-2">{fee.value}</p>
                  <p className="text-sm text-earth-300 font-medium">{fee.sub}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
