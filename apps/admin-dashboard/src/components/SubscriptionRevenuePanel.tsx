import React, { useEffect, useState } from 'react';
import {
  fetchSubscribers,
  fetchSubscriptionAnalytics,
  fetchSubscriptionPlans,
  setSubscriptionPlanEnabled,
  updateSubscriptionPlan,
} from '../api';

export default function SubscriptionRevenuePanel() {
  const [analytics, setAnalytics] = useState(null);
  const [subscribers, setSubscribers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [role, setRole] = useState('farmer');
  const [error, setError] = useState('');

  const load = async () => {
    setError('');
    try {
      const [stats, subs, planRows] = await Promise.all([
        fetchSubscriptionAnalytics(),
        fetchSubscribers(),
        fetchSubscriptionPlans(role),
      ]);
      setAnalytics(stats);
      setSubscribers(subs);
      setPlans(planRows);
    } catch (err) {
      setError(err.message || 'Unable to load subscription revenue');
    }
  };

  useEffect(() => {
    load();
  }, [role]);

  const saveFee = async (plan, value) => {
    await updateSubscriptionPlan(plan.id, { platform_fee_percent: Number(value) });
    await load();
  };

  const togglePlan = async (plan) => {
    await setSubscriptionPlanEnabled(plan.id, !plan.is_active);
    await load();
  };

  return (
    <div className="v4-dashboard-container animate-fade-in compact-mode">
      <header className="v4-hero-professional theme-finance">
        <div className="hero-content-v4">
          <div className="kicker"><span className="pill">MEMBERSHIP REVENUE</span></div>
          <h1>Subscription <span>Engine</span>.</h1>
          <p>Manage fee reductions, visibility tiers, subscriber revenue, churn, renewals, and plan configuration without restricting marketplace access.</p>
        </div>
      </header>

      {error && <div className="v4-alert danger">{error}</div>}

      <section className="v4-kpi-grid">
        <Kpi label="Subscribers" value={analytics?.subscriber_count || 0} />
        <Kpi label="Revenue" value={`$${Number(analytics?.subscription_revenue || 0).toFixed(2)}`} />
        <Kpi label="Churn" value={`${Number(analytics?.churn_rate || 0).toFixed(1)}%`} />
        <Kpi label="Renewal Rate" value={`${Number(analytics?.renewal_rate || 0).toFixed(1)}%`} />
      </section>

      <section className="v4-card" style={{ padding: 24, marginTop: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <h2>Plan Controls</h2>
          <select value={role} onChange={(event) => setRole(event.target.value)} className="v4-input">
            <option value="farmer">Farmers</option>
            <option value="buyer">Buyers</option>
            <option value="supplier">Suppliers</option>
          </select>
        </div>
        <div className="table-responsive" style={{ marginTop: 16 }}>
          <table className="v4-table">
            <thead>
              <tr>
                <th>Plan</th>
                <th>Monthly</th>
                <th>Fee %</th>
                <th>Visibility</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((plan) => (
                <tr key={plan.id}>
                  <td><strong>{plan.name}</strong><br /><small>{plan.code}</small></td>
                  <td>${plan.monthly_price}</td>
                  <td>
                    <input
                      className="v4-input"
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      defaultValue={plan.platform_fee_percent}
                      onBlur={(event) => saveFee(plan, event.target.value)}
                      style={{ maxWidth: 100 }}
                    />
                  </td>
                  <td>{plan.visibility_weight}</td>
                  <td>{plan.is_active ? 'Enabled' : 'Disabled'}</td>
                  <td><button className="q-btn small" onClick={() => togglePlan(plan)}>{plan.is_active ? 'Disable' : 'Enable'}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="v4-card" style={{ padding: 24, marginTop: 24 }}>
        <h2>Recent Subscribers</h2>
        <div className="table-responsive" style={{ marginTop: 16 }}>
          <table className="v4-table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Plan</th>
                <th>Status</th>
                <th>Billing</th>
                <th>Period End</th>
              </tr>
            </thead>
            <tbody>
              {subscribers.map((sub) => (
                <tr key={sub.id}>
                  <td>{sub.role}</td>
                  <td>{sub.plan?.name}</td>
                  <td>{sub.status}</td>
                  <td>{sub.billing_cycle}</td>
                  <td>{sub.current_period_end ? new Date(sub.current_period_end).toLocaleDateString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Kpi({ label, value }) {
  return (
    <div className="v4-kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
