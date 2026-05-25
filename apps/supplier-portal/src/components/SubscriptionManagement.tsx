import React, { useState, useEffect } from 'react';
import { getSubscription, cancelSubscription, checkFeatureEntitlement } from '../api.ts';
import { CreditCard, CheckCircle, XCircle, Zap, Shield, TrendingUp, AlertCircle } from 'lucide-react';

export function SubscriptionManagement() {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [featureChecks, setFeatureChecks] = useState({});

  const features = [
    { key: 'bulk_upload', name: 'Bulk CSV Upload', icon: Zap },
    { key: 'analytics', name: 'Advanced Analytics', icon: TrendingUp },
    { key: 'priority_support', name: 'Priority Support', icon: Shield },
    { key: 'custom_branding', name: 'Custom Branding', icon: CreditCard },
  ];

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = async () => {
    try {
      const data = await getSubscription();
      setSubscription(data);
      const checks = {};
      for (const feature of features) {
        try {
          const result = await checkFeatureEntitlement(feature.key);
          checks[feature.key] = result.has_access;
        } catch {
          checks[feature.key] = false;
        }
      }
      setFeatureChecks(checks);
    } catch (err) {
      console.error('Failed to load subscription:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel your subscription?')) return;
    setCancelling(true);
    try {
      await cancelSubscription();
      loadSubscription();
    } catch (err) {
      console.error('Failed to cancel subscription:', err);
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const planColors = {
    basic: 'bg-gray-100 text-gray-700',
    pro: 'bg-blue-100 text-blue-700',
    enterprise: 'bg-purple-100 text-purple-700',
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-black text-earth-800 mb-4">Current Subscription</h3>
        {subscription ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-earth-50 rounded-xl">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 ${planColors[subscription.subscription_plan] || planColors.basic} rounded-xl flex items-center justify-center`}>
                  <CreditCard className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-2xl font-black text-earth-800 capitalize">{subscription.subscription_plan}</p>
                  <p className="text-sm text-earth-600 capitalize">{subscription.subscription_status}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-earth-500">Billing Cycle</p>
                <p className="font-bold text-earth-800 capitalize">{subscription.billing_cycle}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-earth-50 rounded-xl p-4">
                <p className="text-sm text-earth-500">Start Date</p>
                <p className="font-bold text-earth-800">{new Date(subscription.subscription_start_date).toLocaleDateString()}</p>
              </div>
              <div className="bg-earth-50 rounded-xl p-4">
                <p className="text-sm text-earth-500">End Date</p>
                <p className="font-bold text-earth-800">{new Date(subscription.subscription_end_date).toLocaleDateString()}</p>
              </div>
            </div>

            {subscription.subscription_status === 'active' && (
              <button
                onClick={handleCancel}
                disabled={cancelling}
                className="w-full py-3 bg-red-100 text-red-700 font-black rounded-xl hover:bg-red-200 transition-colors disabled:opacity-50"
              >
                {cancelling ? 'Cancelling...' : 'Cancel Subscription'}
              </button>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
            <p className="text-earth-600 font-bold mb-4">No active subscription</p>
            <button className="px-6 py-3 bg-primary-600 text-white font-black rounded-xl hover:bg-primary-700 transition-colors">
              Choose a Plan
            </button>
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-black text-earth-800 mb-4">Feature Entitlements</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {features.map((feature) => (
            <FeatureCard key={feature.key} feature={feature} hasAccess={featureChecks[feature.key]} />
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-black text-earth-800 mb-4">Plan Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-earth-100">
                <th className="text-left py-3 text-sm font-black text-earth-600 uppercase">Feature</th>
                <th className="text-center py-3 text-sm font-black text-earth-600 uppercase">Basic</th>
                <th className="text-center py-3 text-sm font-black text-earth-600 uppercase">Pro</th>
                <th className="text-center py-3 text-sm font-black text-earth-600 uppercase">Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {[
                { feature: 'Products Limit', basic: '50', pro: '200', enterprise: 'Unlimited' },
                { feature: 'Bulk Upload', basic: '❌', pro: '✅', enterprise: '✅' },
                { feature: 'Analytics', basic: 'Basic', pro: 'Advanced', enterprise: 'Full' },
                { feature: 'Priority Support', basic: '❌', pro: '✅', enterprise: '✅' },
                { feature: 'Custom Branding', basic: '❌', pro: '❌', enterprise: '✅' },
                { feature: 'API Access', basic: '❌', pro: '✅', enterprise: '✅' },
              ].map((row, i) => (
                <tr key={i} className="border-b border-earth-50">
                  <td className="py-3 font-bold text-earth-800">{row.feature}</td>
                  <td className="py-3 text-center text-earth-600">{row.basic}</td>
                  <td className="py-3 text-center text-earth-600">{row.pro}</td>
                  <td className="py-3 text-center text-earth-600">{row.enterprise}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ feature, hasAccess }) {
  const Icon = feature.icon;
  return (
    <div className={`p-4 rounded-xl ${hasAccess ? 'bg-green-50' : 'bg-gray-50'}`}>
      <div className="flex items-center gap-3 mb-2">
        <Icon className={`w-5 h-5 ${hasAccess ? 'text-green-600' : 'text-gray-400'}`} />
        <span className="font-bold text-earth-800">{feature.name}</span>
      </div>
      <div className="flex items-center gap-2">
        {hasAccess ? (
          <CheckCircle className="w-4 h-4 text-green-600" />
        ) : (
          <XCircle className="w-4 h-4 text-gray-400" />
        )}
        <span className={`text-sm ${hasAccess ? 'text-green-700' : 'text-gray-500'}`}>
          {hasAccess ? 'Available' : 'Not Available'}
        </span>
      </div>
    </div>
  );
}
