import React from 'react';

export default function ActivityHistoryPanel({ activities = [] }) {
  return (
    <div className="v4-activity-history animate-fade">
      <div className="v4-history-hero">
          <div className="hero-content">
             <div className="kicker">Operational Ledger</div>
             <h1>Transaction Audit Trail</h1>
             <p>A cryptographically-signed record of all platform activities, escrow settlements, and marketplace engagements.</p>
          </div>
          <div className="hero-stats">
              <div className="v-stat">
                  <span className="l">Journal Entries</span>
                  <span className="v">{activities.length}</span>
              </div>
          </div>
      </div>

      <div className="v4-table-shell mt-40">
         {activities.length > 0 ? (
            <table className="v4-data-table">
               <thead>
                  <tr>
                     <th>ENTRY DATE</th>
                     <th>LOG EVENT</th>
                     <th>DEAL REFERENCE</th>
                     <th>PARTNER ENTITY</th>
                     <th>FISCAL SUM</th>
                     <th>LIFECYCLE STATUS</th>
                  </tr>
               </thead>
               <tbody>
                  {activities.map((a, i) => (
                     <tr key={i}>
                        <td className="date-cell">{a.timestamp ? new Date(a.timestamp).toLocaleDateString() : 'AWAITING LOG'}</td>

                        <td>
                           <span className={`v4-event-tag ${String(a.type || 'LOG').toLowerCase()}`}>
                               {a.type || 'LOG'}
                           </span>
                        </td>
                        <td className="v4-ref-cell">#AG-TR-{i + 1042}</td>
                        <td className="partner-cell">{a.partner || 'SYSTEM CORE'}</td>
                        <td className="amount-cell">{a.amount ? `$${a.amount.toLocaleString()}` : '—'}</td>
                        <td>
                           <div className="v4-status-group">
                              <span className={`v4-status-dot ${String(a.status || 'pending').toLowerCase()}`}></span> 
                              <span>{a.status || 'Pending'}</span>
                           </div>
                        </td>
                     </tr>
                  ))}
               </tbody>
            </table>
         ) : (
            <div className="v4-empty-v2">
               <div className="empty-icon"><i className="fas fa-history"></i></div>
               <h3>Journal Ledger Empty</h3>
               <p>Historical operational records will materialize here as platform engagement scales.</p>
            </div>
         )}
      </div>

      <style>{`
        .v4-activity-history { display: flex; flex-direction: column; }
        
        .v4-history-hero { 
            background: linear-gradient(135deg, #000E2B 0%, #1e293b 100%); 
            padding: 60px; 
            border-radius: 40px; 
            color: #fff; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            position: relative; 
            overflow: hidden; 
        }
        .v4-history-hero::after { 
            content: ""; 
            position: absolute; 
            top: -20%; 
            right: -10%; 
            width: 300px; 
            height: 300px; 
            background: radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 70%); 
        }

        .hero-content .kicker { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em; color: #3b82f6; margin-bottom: 20px; }
        .hero-content h1 { font-size: 42px; font-weight: 950; letter-spacing: -0.02em; margin-bottom: 16px; }
        .hero-content p { font-size: 17px; opacity: 0.7; line-height: 1.6; max-width: 500px; }

        .v-stat { background: rgba(255,255,255,0.05); padding: 24px; border-radius: 24px; border: 1.5px solid rgba(255,255,255,0.1); min-width: 180px; text-align: center; }
        .v-stat .l { display: block; font-size: 11px; font-weight: 850; text-transform: uppercase; color: #64748b; margin-bottom: 8px; }
        .v-stat .v { font-size: 32px; font-weight: 950; color: #fff; }

        .v4-event-tag { 
            padding: 6px 12px; 
            border-radius: 50px; 
            font-size: 10px; 
            font-weight: 900; 
            text-transform: uppercase; 
            letter-spacing: 0.05em;
            background: #f1f5f9;
            color: #64748b;
        }
        .v4-event-tag.sale { background: #dcfce7; color: #166534; }
        .v4-event-tag.purchase { background: #dbeafe; color: #1e40af; }
        .v4-event-tag.deposit { background: #fefce8; color: #854d0e; }

        .date-cell { color: #94a3b8; font-size: 12px; font-weight: 850; }
        .v4-ref-cell { font-family: 'Outfit', monospace; color: #3b82f6; font-weight: 850; }
        .amount-cell { font-weight: 950; color: #1e293b; font-size: 16px; }

        .v4-status-group { display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 850; }
        .v4-status-dot { height: 8px; width: 8px; border-radius: 50%; display: block; }
        .v4-status-dot.completed { background: #22c55e; box-shadow: 0 0 10px rgba(34,197,94,0.4); }
        .v4-status-dot.pending { background: #f59e0b; }
        
        .mt-40 { margin-top: 40px; }
        .v4-empty-v2 { padding: 120px 40px; text-align: center; color: #64748b; background: #fff; border-radius: 32px; border: 1.5px solid #f1f5f9; }
        .empty-icon { width: 80px; height: 80px; background: #f0fdf4; color: #22c55e; border-radius: 50%; display: grid; place-items: center; font-size: 32px; margin: 0 auto 24px; }
        .v4-empty-v2 h3 { font-size: 20px; font-weight: 900; color: #1e293b; margin-bottom: 8px; }
      `}</style>
    </div>
  );
}
