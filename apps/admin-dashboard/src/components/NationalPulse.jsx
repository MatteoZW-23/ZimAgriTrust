import React, { useState, useEffect } from 'react';
import { fetchNationalPulse } from '../api';

const NationalPulse = ({ token }) => {
    const [pulse, setPulse] = useState(null);

    useEffect(() => {
        if (!token) return;
        fetchNationalPulse(token)
            .then(data => setPulse({
                index: data?.index ?? 0,
                status: data?.status ?? 'STABLE',
                gmv: data?.gmv ?? 0,
                vitality: data?.vitality ?? '0.0%',
            }))
            .catch(() => setPulse({ index: 0, status: 'STABLE', gmv: 0, vitality: '0.0%' }));
    }, [token]);

    if (!pulse) return null;

    const statusColor = pulse.status === 'HIGH_LIQUIDITY' ? '#16a34a' : pulse.status === 'EMERGING' ? '#f59e0b' : '#3b82f6';

    return (
        <div className="np-bar">
            <span className="np-brand"><i className="fas fa-chart-line"></i> Market Pulse</span>
            <div className="np-divider" />
            <span className="np-item"><span className="np-label">Index</span><strong>{pulse.index} pts</strong></span>
            <div className="np-divider" />
            <span className="np-item"><span className="np-label">Vitality</span><strong>{pulse.vitality}</strong></span>
            <div className="np-divider" />
            <span className="np-item"><span className="np-label">GMV</span><strong>${Number(pulse.gmv).toLocaleString()}</strong></span>
            <div className="np-divider" />
            <span className="np-status-dot" style={{ background: statusColor }} />
            <span className="np-status-text" style={{ color: statusColor }}>{pulse.status.replace('_', ' ')}</span>
        </div>
    );
};

export default NationalPulse;
