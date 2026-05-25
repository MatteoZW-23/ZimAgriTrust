import React, { useState, useEffect, useCallback } from 'react';
import {
 fetchTransactions, fetchSecurityLogs, fetchNationalRevenue,
 fetchRevenueBreakdown,
 reconcilePlatform, downloadReceipt, listAdminTransactions,
 forceEscrowRelease, forceEscrowRefund,
} from '../api';
import { exportToCSV } from '../utils/dataTransfer';

const STATUS_META = {
 COMPLETED: { color: '#16a34a', bg: '#f0fdf4', label: 'Completed' },
 PENDING: { color: '#d97706', bg: '#fffbeb', label: 'Pending' },
 IN_ESCROW: { color: '#2563eb', bg: '#eff6ff', label: 'In Escrow' },
 DISPUTED: { color: '#dc2626', bg: '#fef2f2', label: 'Disputed' },
 REFUNDED: { color: '#7c3aed', bg: '#f5f3ff', label: 'Refunded' },
 CANCELLED: { color: '#64748b', bg: '#f8fafc', label: 'Cancelled' },
};
function StatusPill({ status = '' }) {
 const m = STATUS_META[status.toUpperCase()] || { color: '#64748b', bg: '#f8fafc', label: status };
 return (
 <span style={{ fontSize: 11, fontWeight: 800, color: m.color, background: m.bg,
 border: `1px solid ${m.color}33`, padding: '3px 10px', borderRadius: 100, whiteSpace: 'nowrap' }}>{m.label}
 </span>);
}

function KpiCard({ icon, label, value, sub, accent }) {
 return (
 <div className="erp-kpi"><div className="erp-kpi-icon" style={{ background: accent + '18', color: accent }}><i className={`fas ${icon}`} /></div><div className="erp-kpi-body"><span className="erp-kpi-label">{label}</span><span className="erp-kpi-value">{value}</span>{sub && <span className="erp-kpi-sub">{sub}</span>}
 </div></div>);
}

const PAGE_SIZE = 15;

export default function EscrowRevenuePanel({ token, onEscrowAction }) {
 const [stats, setStats] = useState({ total_earnings:0, stream_royalties:0, stream_boosts:0, gross_volume:0, platform_yield_pct:0 });
 const [breakdown, setBreakdown] = useState({ total_earnings:0, gross_volume:0, platform_yield_pct:0, streams:{} });
 const [rows, setRows] = useState([]);
 const [total, setTotal] = useState(0);
 const [page, setPage] = useState(1);
 const [filter, setFilter] = useState('ALL');
 const [search, setSearch] = useState('');
 const [busy, setBusy] = useState(false);
 const [loading, setLoading] = useState(true);
 const [selected, setSelected] = useState(null);

 const load = useCallback(async () => {
 setLoading(true);
 try {
 const [txns, rev, det] = await Promise.all([
 listAdminTransactions(token, {
 status: filter === 'ALL' ? undefined : filter,
 limit: PAGE_SIZE,
 offset: (page - 1) * PAGE_SIZE,
 }).catch(() => ({ items: [], total: 0 })),
 fetchNationalRevenue(token).catch(() => null),
 fetchRevenueBreakdown(token),
 ]);

 // listAdminTransactions may return array or { items, total }
 const items = Array.isArray(txns) ? txns : (txns?.items ?? []);
 const count = Array.isArray(txns) ? txns.length : (txns?.total ?? items.length);

 setRows(items.map(t => ({
 id: t.id,
 short: t.id ? t.id.slice(0, 8).toUpperCase() : '—',
 date: t.created_at ? new Date(t.created_at).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' }) : '—',
 buyer: t.buyer_name || ('Buyer ' + (t.buyer_id ? t.buyer_id.slice(0,6) : '—')),
 seller: t.seller_name || ('Seller ' + (t.seller_id ? t.seller_id.slice(0,6) : '—')),
 crop: t.product_type || t.crop || '—',
 amount: t.total_amount ?? t.amount ?? 0,
 fee: t.platform_fee ?? (t.total_amount ?? 0) * 0.01,
 status: t.status ?? 'PENDING',
 raw: t,
 })));
 setTotal(count);
 if (rev) setStats(rev);
 if (det) setBreakdown(det);
 } finally {
 setLoading(false);
 }
 }, [token, filter, page]);

 useEffect(() => { load(); }, [load]);

 const filtered = rows.filter(r => {
 if (!search) return true;
 const q = search.toLowerCase();
 return r.buyer.toLowerCase().includes(q) || r.seller.toLowerCase().includes(q) ||
 r.crop.toLowerCase().includes(q) || r.short.toLowerCase().includes(q);
 });

 const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

 const act = async (type, row) => {
 if (!window.confirm(`${type === 'release' ? 'Release escrow' : 'Refund'} for order ${row.short}?`)) return;
 setBusy(true);
 try {
 if (type === 'release') await forceEscrowRelease(row.id, 'Admin override', token);
 else await forceEscrowRefund(row.id, 'Admin override', token);
 load();
 if (onEscrowAction) onEscrowAction(row.id, type.toUpperCase(), 'Admin override');
 } catch (e) { alert(e.message); }
 finally { setBusy(false); }
 };

 const exportCSV = async () => {
 setBusy(true);
 try {
 const data = await fetchTransactions(token);
 exportToCSV(data, `ZimAgritrust_Ledger_${Date.now()}.csv`);
 } catch (e) { alert(e.message); }
 finally { setBusy(false); }
 };

 const auditExport = async () => {
 setBusy(true);
 try {
 const data = await fetchSecurityLogs(token);
 exportToCSV(data, `ZimAgritrust_Audit_${Date.now()}.csv`);
 } catch (e) { alert(e.message); }
 finally { setBusy(false); }
 };

 const reconcile = async () => {
 if (!window.confirm('Run national reconciliation? This audits the full platform ledger.')) return;
 setBusy(true);
 try {
 const r = await reconcilePlatform(token);
 alert(`Reconciliation complete\nLiability: $${r?.total_liability?.usd ?? 0}\nStatus: ${r?.integrity_check ?? 'OK'}`);
 load();
 } catch (e) { alert(e.message); }
 finally { setBusy(false); }
 };

 const fmt = n => '$' + Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

 const FILTERS = ['ALL','PENDING','IN_ESCROW','COMPLETED','DISPUTED','REFUNDED'];

 return (
 <div className="erp-root">
{/* ── HEADER ─────────────────────────────────────────── */}
 <div className="erp-header"><div><p className="erp-eyebrow">National Command Center</p><h1 className="erp-title">Escrow &amp; Revenue</h1><p className="erp-desc">Real-time oversight of platform earnings, escrow holds, and transaction settlements.</p></div><div className="erp-header-actions"><button className="erp-btn erp-btn-ghost" onClick={exportCSV} disabled={busy}><i className="fas fa-file-arrow-down" /> Export Ledger
 </button><button className="erp-btn erp-btn-ghost" onClick={auditExport} disabled={busy}><i className="fas fa-shield-halved" /> Audit Log
 </button><button className="erp-btn erp-btn-primary" onClick={reconcile} disabled={busy}><i className="fas fa-rotate" /> Reconcile
 </button></div></div>
{/* ── KPI ROW ────────────────────────────────────────── */}
 <div className="erp-kpi-row"><KpiCard icon="fa-circle-dollar-to-slot" label="Gross Volume" value={fmt(stats.gross_volume)} sub="All-time GMV" accent="#2563eb" /><KpiCard icon="fa-sack-dollar" label="Net Earnings" value={fmt(stats.total_earnings)} sub="Platform profit" accent="#16a34a" /><KpiCard icon="fa-percentage" label="Transaction Fees" value={fmt(stats.stream_royalties)} sub="1% per settlement" accent="#d97706" /><KpiCard icon="fa-rocket" label="Boost Revenue" value={fmt(stats.stream_boosts)} sub="Premium visibility" accent="#7c3aed" /><KpiCard icon="fa-chart-line" label="System Margin" value={`${Number(stats.platform_yield_pct||0).toFixed(2)}%`} sub="Yield efficiency" accent="#0891b2" /></div>
{/* ── REVENUE STREAMS BREAKDOWN ───────────────────────── */}
 <div className="erp-section" style={{ marginTop: 24 }}><h3 style={{ fontSize: 14, fontWeight: 800, color: '#64748b', marginBottom: 12, letterSpacing: 0.5 }}>ALL REVENUE STREAMS</h3><div className="erp-stream-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>{Object.values(breakdown.streams || {}).map((s, i) => (
 <div key={i} style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 16 }}><div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>{s.label}</div><div style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginTop: 6 }}>{fmt(s.amount)}</div><div style={{ fontSize: 11, fontWeight: 600, color: '#64748b', marginTop: 4 }}>{s.rate} · Paid by {s.payer}</div></div>))}
 </div></div>
{/* ── LEDGER TABLE ───────────────────────────────────── */}
 <div className="erp-table-card">
{/* toolbar */}
 <div className="erp-toolbar"><div className="erp-filter-tabs">{FILTERS.map(f => (
 <button key={f} className={`erp-tab ${filter===f?'active':''}`}
 onClick={() => { setFilter(f); setPage(1); }}>{f === 'ALL' ? 'All' : STATUS_META[f]?.label ?? f}
 </button>))}
 </div><div className="erp-toolbar-right"><div className="erp-search"><i className="fas fa-magnifying-glass" /><input placeholder="Search buyer, seller, crop…" value={search} onChange={e=>setSearch(e.target.value)} />{search && <button onClick={()=>setSearch('')}><i className="fas fa-xmark"/></button>}
 </div><span className="erp-count">{total} records</span></div></div>
{/* table */}
 <div className="erp-table-wrap" style={{ maxHeight: '600px', overflowY: 'auto' }}><table className="erp-table"><thead><tr><th>Order ID</th><th>Date</th><th>Buyer → Seller</th><th>Crop</th><th style={{textAlign:'right'}}>Amount</th><th style={{textAlign:'right'}}>Fee (1%)</th><th>Status</th><th>Actions</th></tr></thead><tbody>{loading ? (
 <tr><td colSpan={8} className="erp-empty"><i className="fas fa-spinner fa-spin" /> Loading…</td></tr>) : filtered.length === 0 ? (
 <tr><td colSpan={8} className="erp-empty">No transactions found</td></tr>) : filtered.map(row => (
 <tr key={row.id} className={selected===row.id?'erp-row-selected':''} onClick={()=>setSelected(row.id===selected?null:row.id)}><td><span className="erp-id">{row.short}</span></td><td className="erp-date">{row.date}</td><td><div className="erp-party"><span className="erp-party-name">{row.buyer}</span><i className="fas fa-arrow-right" style={{fontSize:9,opacity:.4}} /><span className="erp-party-name">{row.seller}</span></div></td><td className="erp-crop">{row.crop}</td><td className="erp-amount">{fmt(row.amount)}</td><td className="erp-fee">{fmt(row.fee)}</td><td><StatusPill status={row.status} /></td><td onClick={e=>e.stopPropagation()}><div className="erp-actions"><button className="erp-act erp-act-release" title="Release escrow" disabled={busy}
 onClick={()=>act('release',row)}><i className="fas fa-check-double"/></button><button className="erp-act erp-act-refund" title="Refund" disabled={busy}
 onClick={()=>act('refund',row)}><i className="fas fa-rotate-left"/></button><button className="erp-act erp-act-pdf" title="Download receipt" disabled={busy}
 onClick={()=>downloadReceipt(token,row.id).catch(e=>alert(e.message))}><i className="fas fa-file-pdf"/></button></div></td></tr>))}
 </tbody></table></div>
{/* pagination */}
 <div className="erp-pagination"><span className="erp-page-info">Page {page} of {totalPages}</span><div className="erp-page-btns"><button disabled={page<=1} onClick={()=>setPage(p=>p-1)}><i className="fas fa-chevron-left"/></button>{Array.from({length:Math.min(5,totalPages)},(_,i)=>{
 const p = Math.max(1, Math.min(page-2,totalPages-4)) + i;
 return p<=totalPages && (
 <button key={p} className={page===p?'active':''} onClick={()=>setPage(p)}>{p}</button>);
 })}
 <button disabled={page>=totalPages} onClick={()=>setPage(p=>p+1)}><i className="fas fa-chevron-right"/></button></div></div></div></div>);
}
