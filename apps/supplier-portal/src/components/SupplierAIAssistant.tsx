import React, { useEffect, useState } from 'react';
import { Bot, Send, Sparkles, TrendingUp } from 'lucide-react';
import {
  chatWithSupplierAi,
  getSupplierAiMarketIntelligence,
  getSupplierAiPriceDemandPrediction,
  getSupplierAiRecommendations,
} from '../api.ts';

export function SupplierAIAssistant() {
  const [product, setProduct] = useState('Horticulture');
  const [province, setProvince] = useState('');
  const [message, setMessage] = useState('What stock or pricing move should I make this week?');
  const [answer, setAnswer] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [market, setMarket] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const buildContext = () => ({
    product,
    province: province || null,
    portal: 'supplier',
    focus: 'inventory pricing product positioning',
  });

  const loadInsights = async () => {
    setError('');
    const context = buildContext();
    const [nextActions, marketData, priceDemand] = await Promise.all([
      getSupplierAiRecommendations(context),
      getSupplierAiMarketIntelligence(product || null, province || null),
      getSupplierAiPriceDemandPrediction(product || 'Horticulture', province || null, 30),
    ]);
    setRecommendations(nextActions);
    setMarket(marketData);
    setPrediction(priceDemand);
  };

  useEffect(() => {
    loadInsights().catch((err: any) => setError(err?.message || 'AI insights are unavailable.'));
  }, []);

  const askAssistant = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setError('');
    try {
      const [reply] = await Promise.all([
        chatWithSupplierAi(message.trim(), buildContext()),
        loadInsights(),
      ]);
      setAnswer(reply);
    } catch (err: any) {
      setError(err?.message || 'Supplier AI could not answer right now.');
    } finally {
      setLoading(false);
    }
  };

  const metrics = market?.metrics || {};
  const predictionData = prediction?.prediction || prediction || {};
  const actions = recommendations?.recommended_actions || answer?.recommended_actions || [];

  return (
    <div className="space-y-6">
      <div className="supplier-card p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-2 text-primary-700">
              <Bot className="h-5 w-5" />
              <span className="text-xs font-black uppercase tracking-[0.18em]">Supplier AI</span>
            </div>
            <h1 className="font-display text-3xl font-black text-earth-900">AI Supply Desk</h1>
            <p className="mt-2 max-w-3xl text-sm font-semibold leading-relaxed text-earth-600">
              Ask about product positioning, inventory, demand signals, pricing, fulfilment risk, and supplier growth.
            </p>
          </div>
          <button type="button" onClick={loadInsights} className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary-700 px-4 py-3 text-sm font-black text-white shadow-glow">
            <Sparkles className="h-4 w-4" />
            Refresh
          </button>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <input value={product} onChange={(event) => setProduct(event.target.value)} className="rounded-2xl border border-earth-200 px-4 py-3 text-sm font-bold text-earth-800 outline-none focus:border-primary-500" placeholder="Product or sector" />
          <input value={province} onChange={(event) => setProvince(event.target.value)} className="rounded-2xl border border-earth-200 px-4 py-3 text-sm font-bold text-earth-800 outline-none focus:border-primary-500" placeholder="Province" />
          <button type="button" onClick={askAssistant} disabled={loading} className="inline-flex items-center justify-center gap-2 rounded-2xl bg-earth-900 px-4 py-3 text-sm font-black text-white disabled:opacity-60">
            <Send className="h-4 w-4" />
            {loading ? 'Thinking...' : 'Ask AI'}
          </button>
        </div>

        <textarea value={message} onChange={(event) => setMessage(event.target.value)} className="mt-3 min-h-28 w-full rounded-2xl border border-earth-200 px-4 py-3 text-sm font-semibold text-earth-800 outline-none focus:border-primary-500" placeholder="Ask Supplier AI..." />
        {error && <p className="mt-3 text-sm font-bold text-red-600">{error}</p>}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <InsightCard title="Assistant Answer" icon={<Bot className="h-5 w-5" />}>
          <p className="text-sm font-semibold leading-relaxed text-earth-700">
            {answer?.answer || answer?.summary || 'Ask a supplier question to get a role-specific answer.'}
          </p>
        </InsightCard>

        <InsightCard title="Recommended Actions" icon={<Sparkles className="h-5 w-5" />}>
          <div className="space-y-2">
            {(actions.length ? actions : ['Review stock depth against current demand.', 'Refresh prices for high-interest products.', 'Prioritize fulfilment for escrow-backed orders.']).map((item: string, index: number) => (
              <div key={`${item}-${index}`} className="rounded-2xl bg-primary-50 px-4 py-3 text-sm font-bold text-earth-800">{item}</div>
            ))}
          </div>
        </InsightCard>

        <InsightCard title="Market Intelligence" icon={<TrendingUp className="h-5 w-5" />}>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Avg Price" value={metrics.average_price ? `$${metrics.average_price}` : 'Live'} />
            <Metric label="Listings" value={metrics.listing_count ?? '0'} />
            <Metric label="Demand" value={market?.demand_signal || market?.trend || 'Monitoring'} />
          </div>
        </InsightCard>

        <InsightCard title="Price And Demand" icon={<TrendingUp className="h-5 w-5" />}>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Forecast" value={predictionData.predicted_price ? `$${predictionData.predicted_price}` : predictionData.price_trend || 'Stable'} />
            <Metric label="Demand" value={predictionData.demand_forecast || predictionData.demand_signal || 'Balanced'} />
            <Metric label="Confidence" value={predictionData.confidence ? `${Math.round(predictionData.confidence * 100)}%` : 'Rules'} />
          </div>
        </InsightCard>
      </div>
    </div>
  );
}

function InsightCard({ title, icon, children }: any) {
  return (
    <section className="supplier-card p-5">
      <div className="mb-4 flex items-center gap-2 text-primary-700">
        {icon}
        <h2 className="font-display text-lg font-black text-earth-900">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value }: any) {
  return (
    <div className="rounded-2xl border border-earth-200 bg-white px-4 py-3">
      <div className="text-xs font-black uppercase tracking-[0.14em] text-earth-500">{label}</div>
      <div className="mt-1 text-lg font-black text-earth-900">{value}</div>
    </div>
  );
}
