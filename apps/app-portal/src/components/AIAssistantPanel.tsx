import React, { useEffect, useState } from 'react';
import { useAuthStore } from '@agritrust/shared';
import { Bot, Send, Sparkles, TrendingUp } from 'lucide-react';
import {
  chatWithPortalAi,
  getPortalAiMarketIntelligence,
  getPortalAiPriceDemandPrediction,
  getPortalAiRecommendations,
} from '../api';

type AssistantRole = 'farmer' | 'buyer';

export const AIAssistantPanel: React.FC = () => {
  const { user } = useAuthStore();
  const assistantRole: AssistantRole = user?.role === 'buyer' ? 'buyer' : 'farmer';
  const [product, setProduct] = useState('Horticulture');
  const [province, setProvince] = useState(user?.province || '');
  const [message, setMessage] = useState(
    assistantRole === 'buyer'
      ? 'What should I buy or request this week?'
      : 'How should I price and move my produce this week?',
  );
  const [answer, setAnswer] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [market, setMarket] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const buildContext = () => ({
    product,
    province: province || null,
    portal: 'app-portal',
    role: assistantRole,
  });

  const loadInsights = async () => {
    setError('');
    const context = buildContext();
    const [nextActions, marketData, priceDemand] = await Promise.all([
      getPortalAiRecommendations(assistantRole, context),
      getPortalAiMarketIntelligence(product || null, province || null),
      getPortalAiPriceDemandPrediction(product || 'Horticulture', province || null, 30),
    ]);
    setRecommendations(nextActions);
    setMarket(marketData);
    setPrediction(priceDemand);
  };

  useEffect(() => {
    loadInsights().catch((err: any) => setError(err?.message || 'AI insights are unavailable.'));
  }, [assistantRole]);

  const askAssistant = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setError('');
    try {
      const reply = await chatWithPortalAi(assistantRole, message.trim(), buildContext());
      setAnswer(reply);
      await loadInsights();
    } catch (err: any) {
      setError(err?.message || 'AI assistant could not answer right now.');
    } finally {
      setLoading(false);
    }
  };

  const roleLabel = assistantRole === 'buyer' ? 'Buyer AI' : 'Farmer AI';
  const metrics = market?.metrics || {};
  const predictionData = prediction?.prediction || prediction || {};
  const actions = recommendations?.recommended_actions || answer?.recommended_actions || [];

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-border bg-card p-6 shadow-soft">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-2 text-primary">
              <Bot size={20} />
              <span className="text-xs font-black uppercase tracking-[0.18em]">{roleLabel}</span>
            </div>
            <h1 className="text-3xl font-black text-text">AI Trading Desk</h1>
            <p className="mt-2 max-w-3xl text-sm font-semibold leading-relaxed text-dim">
              Ask for role-specific guidance on pricing, demand, listings, offers, orders, and next best actions.
            </p>
          </div>
          <button type="button" onClick={loadInsights} className="btn-primary inline-flex items-center justify-center gap-2">
            <Sparkles size={16} />
            Refresh
          </button>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <input value={product} onChange={(event) => setProduct(event.target.value)} className="form-input" placeholder="Honey, goats, flowers, fish, maize" />
          <input value={province} onChange={(event) => setProvince(event.target.value)} className="form-input" placeholder="Province" />
          <button type="button" onClick={askAssistant} disabled={loading} className="btn-secondary inline-flex items-center justify-center gap-2 disabled:opacity-60">
            <Send size={16} />
            {loading ? 'Thinking...' : 'Ask AI'}
          </button>
        </div>

        <textarea value={message} onChange={(event) => setMessage(event.target.value)} className="form-input mt-3 min-h-28" placeholder={`Ask ${roleLabel}...`} />
        {error && <p className="mt-3 text-sm font-bold text-danger-600">{error}</p>}
      </section>

      <div className="grid gap-4 xl:grid-cols-2">
        <Insight title="Assistant Answer" icon={<Bot size={20} />}>
          <p className="text-sm font-semibold leading-relaxed text-dim">
            {answer?.answer || answer?.summary || `Ask ${roleLabel} to get a role-specific answer.`}
          </p>
        </Insight>
        <Insight title="Recommended Actions" icon={<Sparkles size={20} />}>
          <div className="space-y-2">
            {(actions.length ? actions : ['Review current market prices.', 'Check pending orders and offers.', 'Use demand signals before changing price or request volume.']).map((item: string, index: number) => (
              <div key={`${item}-${index}`} className="rounded-2xl bg-primary-50 px-4 py-3 text-sm font-bold text-earth-800">{item}</div>
            ))}
          </div>
        </Insight>
        <Insight title="Market Intelligence" icon={<TrendingUp size={20} />}>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Avg Price" value={metrics.average_price ? `$${metrics.average_price}` : 'Live'} />
            <Metric label="Listings" value={metrics.listing_count ?? '0'} />
            <Metric label="Demand" value={market?.demand_signal || market?.trend || 'Monitoring'} />
          </div>
        </Insight>
        <Insight title="Price And Demand" icon={<TrendingUp size={20} />}>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Forecast" value={predictionData.predicted_price ? `$${predictionData.predicted_price}` : predictionData.price_trend || 'Stable'} />
            <Metric label="Demand" value={predictionData.demand_forecast || predictionData.demand_signal || 'Balanced'} />
            <Metric label="Confidence" value={predictionData.confidence ? `${Math.round(predictionData.confidence * 100)}%` : 'Rules'} />
          </div>
        </Insight>
      </div>
    </div>
  );
};

function Insight({ title, icon, children }: any) {
  return (
    <section className="rounded-3xl border border-border bg-card p-5 shadow-soft">
      <div className="mb-4 flex items-center gap-2 text-primary">
        {icon}
        <h2 className="text-lg font-black text-text">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value }: any) {
  return (
    <div className="rounded-2xl border border-border bg-white/70 px-4 py-3 dark:bg-white/5">
      <div className="text-xs font-black uppercase tracking-[0.14em] text-muted">{label}</div>
      <div className="mt-1 text-lg font-black text-text">{value}</div>
    </div>
  );
}
