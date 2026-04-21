import React, { useState, useEffect } from 'react';
import { fetchWalletBalance, fetchTransactions, initiateDeposit, initiateWithdrawal } from '../api';

export default function WalletPanel({ token, profile }) {
    const [balance, setBalance] = useState({ balance_usd: 0, balance_zig: 0, pending_usd: 0, pending_zig: 0 });
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('summary');
    const [showWithdraw, setShowWithdraw] = useState(false);
    const [amount, setAmount] = useState('');
    const [method, setMethod] = useState('ecocash');

    const loadData = async () => {
        try {
            const [b, txs] = await Promise.all([
                fetchWalletBalance(token),
                fetchTransactions(token)
            ]);
            setBalance(b);
            setTransactions(txs || []);
        } catch (err) {
            console.error("Financial Sync Failed", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [token]);

    const handleWithdraw = async (e) => {
        e.preventDefault();
        try {
            await initiateWithdrawal(token, {
                amount: parseFloat(amount),
                currency: 'USD', // Default for now
                payment_method: method
            });
            alert('PAYOUT_REQUESTED: Transfer initiated via regional gateway.');
            setShowWithdraw(false);
            loadData();
        } catch (err) {
            alert(`PAYOUT_FAILURE: ${err.message}`);
        }
    };

    if (loading) return <div className="p-40">Synchronizing Financial Ledger...</div>;

    return (
        <div className="v4-dashboard-container animate-fade-in compact-mode">
            <header className="v4-hero-professional theme-finance" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #171717 100%)' }}>
                <div className="hero-content-v4">
                    <div className="kicker">
                        <span className="pill" style={{ background: 'rgba(34,197,94,0.2)', color: '#22c55e' }}>FISCAL AUTHORITY</span>
                        <div className="sync-pulse"><div className="p-dot" style={{ background: '#22c55e' }}></div>SYNCED WITH NMB BANK</div>
                    </div>
                    <h1>Financial <span>Inventory</span>.</h1>
                    <p>Managing your agricultural capital with sovereign-grade security. Track escrow balances, settlement cycles, and regional payouts.</p>
                    
                    <div className="hero-actions" style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                         <button className="q-btn primary-btn small" onClick={() => setShowWithdraw(true)} style={{ background: '#22c55e', color: '#000' }}>
                            <i className="fas fa-file-invoice-dollar"></i> Request Payout
                        </button>
                        <button className="q-btn ghost small" onClick={loadData} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff' }}>
                            <i className="fas fa-rotate"></i> Refresh Ledger
                        </button>
                    </div>
                </div>
                
                <div className="hero-visual" style={{ display: 'flex', gap: '20px' }}>
                    <div className="v4-glass-card-mini dark">
                        <label>AVAILABLE (USD)</label>
                        <strong>${balance.balance_usd?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                    </div>
                    <div className="v4-glass-card-mini dark neon">
                        <label>ESCROW PENDING</label>
                        <strong>${balance.pending_usd?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                    </div>
                </div>
            </header>

            <div className="v4-main-panel">
                <div className="v4-glass-card-premium">
                    <div className="v4-tabs-v5">
                        <button className={activeTab === 'summary' ? 'active' : ''} onClick={() => setActiveTab('summary')}>Operational Summary</button>
                        <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>Transaction History</button>
                    </div>

                    <div className="v4-tab-content" style={{ marginTop: '32px' }}>
                        {activeTab === 'summary' && (
                            <div className="v4-finance-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                                <div className="f-card">
                                    <div className="f-icon"><i className="fas fa-building-columns"></i></div>
                                    <div className="f-info">
                                        <label>Settlement Gateway</label>
                                        <strong>AgriTrust Trust Account</strong>
                                        <span className="v4-status-pill ghost green small">ACTIVE</span>
                                    </div>
                                </div>
                                <div className="f-card">
                                    <div className="f-icon"><i className="fab fa-whatsapp"></i></div>
                                    <div className="f-info">
                                        <label>USSD/M-Wallet</label>
                                        <strong>EcoCash Business</strong>
                                        <span className="v4-status-pill ghost green small">+263 77***567</span>
                                    </div>
                                </div>
                                <div className="f-card">
                                    <div className="f-icon"><i className="fas fa-shield-virus"></i></div>
                                    <div className="f-info">
                                        <label>Risk Reserve</label>
                                        <strong>$0.00 (Standard)</strong>
                                        <span className="v4-status-pill ghost small">LEVEL 1 AUTH</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'history' && (
                            <div className="v4-table-shell">
                                <table className="v4-data-table">
                                    <thead>
                                        <tr>
                                            <th>TRANSACTION</th>
                                            <th>TYPE</th>
                                            <th>AMOUNT</th>
                                            <th>STATUS</th>
                                            <th>TIMESTAMP</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {transactions.map(tx => (
                                            <tr key={tx.id}>
                                                <td><span style={{ fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)' }}>#TXN-{tx.id.slice(0,8).toUpperCase()}</span></td>
                                                <td><span className={`v4-status-pill ghost`} style={{ border: 'none', background: 'var(--v4-surface)', padding: '4px 10px' }}>{tx.type}</span></td>
                                                <td><strong style={{ color: tx.type === 'DEPOSIT' || tx.type === 'SALE' ? '#22c55e' : 'inherit' }}>{tx.type === 'DEPOSIT' ? '+' : '-'}${tx.amount?.toFixed(2)}</strong></td>
                                                <td><span className={`v4-status-pill ${tx.status.toLowerCase()}`}>{tx.status}</span></td>
                                                <td><span style={{ fontSize: '12px', opacity: 0.6 }}>{new Date(tx.created_at).toLocaleDateString()}</span></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                                {!transactions.length && <div className="p-40 text-center opacity-50 italic">No recorded transactions in the institutional ledger.</div>}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {showWithdraw && (
                <div className="v4-modal-overlay">
                    <div className="v5-ultra-glass-modal animate-rise" style={{ background: '#020617', maxWidth: '500px' }}>
                        <div style={{ padding: '40px' }}>
                            <h2 style={{ color: '#fff', fontSize: '24px', fontWeight: 1000, marginBottom: '8px' }}>Request <span>Payout</span>.</h2>
                            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px', marginBottom: '32px' }}>Initiating transfer from AgriTrust Vault to your personal settlement channel.</p>
                            
                            <form onSubmit={handleWithdraw}>
                                <div className="v4-form-group" style={{ marginBottom: '24px' }}>
                                    <label style={{ color: '#22c55e', fontSize: '10px', fontWeight: 1000 }}>WITHDRAWAL AMOUNT (USD)</label>
                                    <div style={{ position: 'relative', marginTop: '8px' }}>
                                        <span style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', fontWeight: 1000, color: '#fff' }}>$</span>
                                        <input 
                                            type="number" 
                                            value={amount}
                                            onChange={e => setAmount(e.target.value)}
                                            style={{ width: '100%', padding: '16px 16px 16px 32px', borderRadius: '16px', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '18px', fontWeight: 900 }} 
                                            placeholder="0.00"
                                            required
                                        />
                                    </div>
                                    <div style={{ marginTop: '8px', fontSize: '11px', color: 'rgba(255,255,255,0.4)', textAlign: 'right' }}>MAX: ${balance.balance_usd?.toFixed(2)}</div>
                                </div>

                                <div className="v4-form-group" style={{ marginBottom: '40px' }}>
                                    <label style={{ color: 'rgba(255,255,255,0.4)', fontSize: '10px', fontWeight: 1000 }}>PAYOUT GATEWAY</label>
                                    <select value={method} onChange={e => setMethod(e.target.value)} style={{ width: '100%', padding: '16px', borderRadius: '16px', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', color: '#fff', marginTop: '8px', fontWeight: 800 }}>
                                        <option value="ecocash">EcoCash Wallet (+263***767)</option>
                                        <option value="bank">Bank Transfer (NMB Bank)</option>
                                        <option value="innbucks">Innbucks Voucher (Zim)</option>
                                    </select>
                                </div>

                                <div style={{ display: 'flex', gap: '16px' }}>
                                    <button type="button" className="q-btn ghost full-w" onClick={() => setShowWithdraw(false)} style={{ color: '#fff' }}>Cancel</button>
                                    <button type="submit" className="q-btn primary-btn full-w" style={{ background: '#22c55e', color: '#000' }}>AUTHORIZE PAYOUT</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            <style>{`
                .v4-glass-card-mini.dark { background: rgba(255,255,255,0.02); border: 1.5px solid rgba(255,255,255,0.05); color: #fff; width: 220px; }
                .v4-glass-card-mini.dark.neon { border-color: #22c55e44; background: linear-gradient(135deg, rgba(34,197,94,0.05) 0%, transparent 100%); }
                .v4-glass-card-mini.dark label { opacity: 0.5; color: #fff; }
                .v4-tabs-v5 { display: flex; gap: 32px; border-bottom: 1.5px solid var(--v4-border); }
                .v4-tabs-v5 button { background: none; border: none; padding: 0 0 16px 0; color: var(--v4-text-dim); font-weight: 900; font-size: 15px; cursor: pointer; position: relative; }
                .v4-tabs-v5 button.active { color: var(--v4-text-main); }
                .v4-tabs-v5 button.active::after { content: ''; position: absolute; bottom: -1.5px; left: 0; right: 0; height: 3px; background: #22c55e; border-top-left-radius: 3px; border-top-right-radius: 3px; }
                .f-card { background: var(--v4-surface); padding: 32px; borderRadius: 24px; border: 1.5px solid var(--v4-border); display: flex; gap: 20px; align-items: flex-start; }
                .f-icon { width: 48px; height: 48px; borderRadius: 14px; background: #fff; display: grid; placeItems: center; color: #22c55e; font-size: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
                .f-info label { display: block; font-size: 10px; fontWeight: 900; color: var(--v4-text-dim); marginBottom: 4px; text-transform: uppercase; }
                .f-info strong { display: block; font-size: 16px; fontWeight: 950; marginBottom: 8px; }
            `}</style>
        </div>
    );
}
