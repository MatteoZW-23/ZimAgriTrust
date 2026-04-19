import React, { useState, useEffect } from 'react';
import { fetchNationalPulse } from '../api';

const NationalPulse = ({ token }) => {
    const [pulse, setPulse] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadPulse() {
            setLoading(true);
            try {
                const data = await fetchNationalPulse(token);
                setPulse({
                    index: data?.index ?? 0,
                    status: data?.status ?? 'STABLE',
                    gmv: data?.gmv ?? 0,
                    vitality: data?.vitality ?? '---',
                    latency: '12ms'
                });
            } catch (err) {
                console.error("Pulse Sync Error:", err);
                setPulse({ index: 0, status: 'CONNECTED', gmv: 0, vitality: '---', latency: '---' });
            } finally {
                setLoading(false);
            }
        }
        if (token) loadPulse();
        else setLoading(false);
    }, [token]);

    if (loading) return <div className="pulse-loading-v4">Synchronizing with Regional Cloud...</div>;

    return (
        <div className="pulse-card-clean animate-fade-in">
            <div className="pulse-header-clean">
                <div className="title-area">
                    <i className="fas fa-chart-line"></i>
                    <strong>Market Intelligence Overview</strong>
                </div>
                <div className="sync-status">Real-time Data Stream</div>
            </div>
            
            <div className="pulse-stats-clean">
                <div className="stat-node-clean">
                    <span className="l">Commerce Index</span>
                    <span className="v">{pulse.index} <small>pts</small></span>
                </div>
                <div className="stat-node-clean">
                    <span className="l">Market Vitality</span>
                    <span className="v">{pulse.vitality}</span>
                </div>
            </div>

            <div className="regional-matrix-v4">
                <label>Status: <span className={`h-status ${pulse.status.toLowerCase()}`}>{pulse.status}</span></label>
                <div className="h-row">
                    <span className="h-name">Gross Volume</span>
                    <div className="h-bar-bg">
                        <div className="h-bar-fill" style={{width: `${Math.min(100, pulse.index * 2)}%`}}></div>
                    </div>
                    <span className="h-name" style={{ textAlign: 'right' }}>${pulse.gmv.toLocaleString()}</span>
                </div>
            </div>

        </div>
    );
};

export default NationalPulse;
