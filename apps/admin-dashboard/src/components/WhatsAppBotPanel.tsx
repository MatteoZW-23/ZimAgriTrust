import React, { useEffect, useState } from 'react';
import {
  fetchWhatsAppStatus,
  sendWhatsAppBroadcast,
  sendWhatsAppHarvestReminder,
  sendWhatsAppPriceAlert,
  sendWhatsAppWeatherAlert,
} from '../api';

export default function WhatsAppBotPanel({ token }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState('');
  const [broadcast, setBroadcast] = useState({ message: '', role_filter: '', province_filter: '', verified_only: false });
  const [price, setPrice] = useState({ commodity: '', old_price: '', new_price: '', province: '' });
  const [weather, setWeather] = useState({ province: '', alert_type: '', message_body: '' });
  const [harvest, setHarvest] = useState({ crop_type: '', province: '' });

  async function loadStatus() {
    setLoading(true);
    setError('');
    try {
      setStatus(await fetchWhatsAppStatus(token));
    } catch (err) {
      setError(err.message || 'Failed to load WhatsApp status.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStatus();
  }, [token]);

  async function runAction(action) {
    setLoading(true);
    setError('');
    setResult('');
    try {
      const response = await action();
      setResult(JSON.stringify(response, null, 2));
    } catch (err) {
      setError(err.message || 'WhatsApp action failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="reality-stack-v4 animate-fade-in">
      <div className="v4-glass-card-premium" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 24, fontWeight: 900 }}>WhatsApp Bot Control</h2>
            <p style={{ margin: '6px 0 0', color: 'var(--v4-text-dim)' }}>
              Monitor the WhatsApp bridge and send operational broadcasts, price alerts, weather alerts, and harvest reminders.
            </p>
          </div>
          <button className="v4-action-btn" onClick={loadStatus} disabled={loading}>
            <i className="fas fa-rotate"></i> Refresh
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14, marginTop: 22 }}>
          <StatusCard label="Bridge" value={status?.status || status?.connected || 'UNKNOWN'} />
          <StatusCard label="Provider" value={status?.provider || status?.bridge || 'WhatsApp'} />
          <StatusCard label="Checked" value={new Date().toLocaleTimeString()} />
        </div>

        {error && <Notice kind="error" text={error} />}
        {result && <pre style={resultStyle}>{result}</pre>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 18 }}>
        <ActionCard title="Broadcast Message" icon="fa-bullhorn">
          <Field label="Message" value={broadcast.message} onChange={(v) => setBroadcast({ ...broadcast, message: v })} textarea required />
          <Field label="Province Filter" value={broadcast.province_filter} onChange={(v) => setBroadcast({ ...broadcast, province_filter: v })} placeholder="Optional" />
          <div>
            <label style={labelStyle}>Role Filter</label>
            <select value={broadcast.role_filter} onChange={(e) => setBroadcast({ ...broadcast, role_filter: e.target.value })} style={inputStyle}>
              <option value="">All Roles</option>
              <option value="farmer">Farmers</option>
              <option value="buyer">Buyers</option>
              <option value="agent">Agents</option>
              <option value="transporter">Transporters</option>
            </select>
          </div>
          <label style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 10, fontWeight: 800 }}>
            <input type="checkbox" checked={broadcast.verified_only} onChange={(e) => setBroadcast({ ...broadcast, verified_only: e.target.checked })} />
            Verified users only
          </label>
          <button className="v4-action-btn primary" disabled={loading || !broadcast.message} onClick={() => runAction(() => sendWhatsAppBroadcast(token, cleanPayload(broadcast)))}>
            Send Broadcast
          </button>
        </ActionCard>

        <ActionCard title="Price Alert" icon="fa-chart-line">
          <Field label="Commodity" value={price.commodity} onChange={(v) => setPrice({ ...price, commodity: v })} required />
          <Field label="Old Price" type="number" value={price.old_price} onChange={(v) => setPrice({ ...price, old_price: v })} required />
          <Field label="New Price" type="number" value={price.new_price} onChange={(v) => setPrice({ ...price, new_price: v })} required />
          <Field label="Province" value={price.province} onChange={(v) => setPrice({ ...price, province: v })} placeholder="Optional" />
          <button className="v4-action-btn primary" disabled={loading || !price.commodity || !price.old_price || !price.new_price} onClick={() => runAction(() => sendWhatsAppPriceAlert(token, cleanPayload({ ...price, old_price: Number(price.old_price), new_price: Number(price.new_price) })))}>
            Send Price Alert
          </button>
        </ActionCard>

        <ActionCard title="Weather Alert" icon="fa-cloud-bolt">
          <Field label="Province" value={weather.province} onChange={(v) => setWeather({ ...weather, province: v })} required />
          <Field label="Alert Type" value={weather.alert_type} onChange={(v) => setWeather({ ...weather, alert_type: v })} placeholder="drought, flood, storm..." required />
          <Field label="Message" value={weather.message_body} onChange={(v) => setWeather({ ...weather, message_body: v })} textarea required />
          <button className="v4-action-btn primary" disabled={loading || !weather.province || !weather.alert_type || !weather.message_body} onClick={() => runAction(() => sendWhatsAppWeatherAlert(token, cleanPayload(weather)))}>
            Send Weather Alert
          </button>
        </ActionCard>

        <ActionCard title="Harvest Reminder" icon="fa-seedling">
          <Field label="Crop Type" value={harvest.crop_type} onChange={(v) => setHarvest({ ...harvest, crop_type: v })} required />
          <Field label="Province" value={harvest.province} onChange={(v) => setHarvest({ ...harvest, province: v })} placeholder="Optional" />
          <button className="v4-action-btn primary" disabled={loading || !harvest.crop_type} onClick={() => runAction(() => sendWhatsAppHarvestReminder(token, cleanPayload(harvest)))}>
            Send Harvest Reminder
          </button>
        </ActionCard>
      </div>
    </div>
  );
}

function ActionCard({ title, icon, children }) {
  return (
    <div className="v4-glass-card-premium" style={{ padding: 22 }}>
      <h3 style={{ marginTop: 0 }}><i className={`fas ${icon}`} style={{ marginRight: 10, color: 'var(--v4-primary)' }}></i>{title}</h3>
      <div style={{ display: 'grid', gap: 12 }}>{children}</div>
    </div>
  );
}

function StatusCard({ label, value }) {
  return (
    <div style={{ background: 'var(--v4-surface)', border: '1px solid var(--v4-border)', borderRadius: 16, padding: 16 }}>
      <div style={{ color: 'var(--v4-text-dim)', fontSize: 11, fontWeight: 900, textTransform: 'uppercase' }}>{label}</div>
      <strong style={{ display: 'block', marginTop: 6 }}>{String(value)}</strong>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', required, placeholder, textarea }) {
  return (
    <div>
      <label style={labelStyle}>{label}</label>
      {textarea ? (
        <textarea value={value} onChange={(e) => onChange(e.target.value)} required={required} placeholder={placeholder} style={{ ...inputStyle, minHeight: 92, resize: 'vertical' }} />
      ) : (
        <input type={type} value={value} onChange={(e) => onChange(e.target.value)} required={required} placeholder={placeholder} style={inputStyle} />
      )}
    </div>
  );
}

function Notice({ text }) {
  return <div style={{ background: 'rgba(239,68,68,.12)', border: '1px solid rgba(239,68,68,.35)', color: '#ef4444', padding: 12, borderRadius: 12, marginTop: 16 }}>{text}</div>;
}

function cleanPayload(payload) {
  return Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== '' && value !== undefined && value !== null));
}

const labelStyle = { display: 'block', marginBottom: 6, fontSize: 12, fontWeight: 900, color: 'var(--v4-text-dim)' };
const inputStyle = { width: '100%', padding: '11px 12px', borderRadius: 12, border: '1px solid var(--v4-border)', background: 'var(--v4-bg)', color: 'var(--v4-text)', outline: 'none' };
const resultStyle = { marginTop: 16, padding: 14, borderRadius: 12, background: '#020617', color: '#22c55e', overflowX: 'auto', fontSize: 12 };
