/**
 * ZimAgritrust - Transport Management Panel
 * Admin interface for managing transport requests, negotiations, driver assignments, and disputes.
 */
import React, { useState, useEffect } from 'react';
import {
  getTransportRequests, getTransportRequest, getNegotiations, resolveNegotiation,
  getDriverAssignments, manualAssignDriver, getTransportDisputes, resolveTransportDispute,
  getTransportStats,
} from '../api';

export function TransportManagementPanel({ token }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState([]);
  const [negotiations, setNegotiations] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    loadStats();
  }, [token]);

  useEffect(() => {
    if (activeTab === 'requests') loadRequests();
    if (activeTab === 'negotiations') loadNegotiations();
    if (activeTab === 'assignments') loadAssignments();
    if (activeTab === 'disputes') loadDisputes();
  }, [activeTab, token]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await getTransportStats(token);
      setStats(data);
    } catch (err) {
      console.error('Failed to load transport stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadRequests = async () => {
    setLoading(true);
    try {
      const data = await getTransportRequests(token);
      setRequests(data.requests || []);
    } catch (err) {
      console.error('Failed to load transport requests:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadNegotiations = async () => {
    setLoading(true);
    try {
      const data = await getNegotiations(token);
      setNegotiations(data.negotiations || []);
    } catch (err) {
      console.error('Failed to load negotiations:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAssignments = async () => {
    setLoading(true);
    try {
      const data = await getDriverAssignments(token);
      setAssignments(data.assignments || []);
    } catch (err) {
      console.error('Failed to load driver assignments:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDisputes = async () => {
    setLoading(true);
    try {
      const data = await getTransportDisputes(token);
      setDisputes(data.disputes || []);
    } catch (err) {
      console.error('Failed to load transport disputes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolveNegotiation = async (negotiationId, resolution) => {
    try {
      await resolveNegotiation(token, negotiationId, resolution);
      alert('Negotiation resolved successfully');
      loadNegotiations();
    } catch (err) {
      alert('Failed to resolve negotiation: ' + err.message);
    }
  };

  const handleResolveDispute = async (disputeId, resolution) => {
    try {
      await resolveTransportDispute(token, disputeId, resolution);
      alert('Dispute resolved successfully');
      loadDisputes();
    } catch (err) {
      alert('Failed to resolve dispute: ' + err.message);
    }
  };

  const TABS = [
    { id: 'overview', label: 'Overview', icon: 'fa-chart-line' },
    { id: 'requests', label: 'Transport Requests', icon: 'fa-truck' },
    { id: 'negotiations', label: 'Negotiations', icon: 'fa-comments' },
    { id: 'assignments', label: 'Driver Assignments', icon: 'fa-user-tag' },
    { id: 'disputes', label: 'Disputes', icon: 'fa-exclamation-triangle' },
  ];

  return (
    <div style={{ padding: '24px', background: '#0f172a', minHeight: '100vh', color: '#fff' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 900, marginBottom: '8px' }}>Transport Management</h1>
        <p style={{ color: '#94a3b8', fontSize: '14px' }}>Manage transport requests, negotiations, driver assignments, and disputes</p>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid #1e293b', paddingBottom: '16px' }}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 20px',
              background: activeTab === tab.id ? '#3b82f6' : 'transparent',
              color: activeTab === tab.id ? '#fff' : '#94a3b8',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <i className={`fas ${tab.icon}`}></i>
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '40px' }}><i className="fas fa-spinner fa-spin" style={{ fontSize: '24px' }}></i></div>}

      {activeTab === 'overview' && stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
          <div style={{ background: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>Total Requests</div>
            <div style={{ fontSize: '32px', fontWeight: 900, color: '#3b82f6' }}>{stats.total_requests || 0}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>Active Negotiations</div>
            <div style={{ fontSize: '32px', fontWeight: 900, color: '#f59e0b' }}>{stats.active_negotiations || 0}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>Active Assignments</div>
            <div style={{ fontSize: '32px', fontWeight: 900, color: '#10b981' }}>{stats.active_assignments || 0}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>Open Disputes</div>
            <div style={{ fontSize: '32px', fontWeight: 900, color: '#ef4444' }}>{stats.open_disputes || 0}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>Total Revenue</div>
            <div style={{ fontSize: '32px', fontWeight: 900, color: '#8b5cf6' }}>${(stats.total_revenue || 0).toFixed(2)}</div>
          </div>
          <div style={{ background: '#1e293b', padding: '20px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>Avg Delivery Time</div>
            <div style={{ fontSize: '32px', fontWeight: 900, color: '#06b6d4' }}>{stats.avg_delivery_time || 0} min</div>
          </div>
        </div>
      )}

      {activeTab === 'requests' && (
        <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#0f172a' }}>
              <tr>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Order ID</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Mode</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Requested By</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Transport Fee</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Created</th>
              </tr>
            </thead>
            <tbody>
              {requests.map(req => (
                <tr key={req.id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{req.order_id?.slice(0, 8)}...</td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{req.mode}</td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{req.requested_by}</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 600,
                      background: req.status === 'COMPLETED' ? '#065f46' : req.status === 'PENDING' ? '#92400e' : '#1e293b',
                      color: req.status === 'COMPLETED' ? '#6ee7b7' : req.status === 'PENDING' ? '#fcd34d' : '#94a3b8',
                    }}>{req.status}</span>
                  </td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>${req.transport_fee?.toFixed(2) || '0.00'}</td>
                  <td style={{ padding: '16px', fontSize: '14px', color: '#94a3b8' }}>{new Date(req.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {requests.length === 0 && <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>No transport requests found</div>}
        </div>
      )}

      {activeTab === 'negotiations' && (
        <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#0f172a' }}>
              <tr>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Negotiation ID</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Order ID</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Current Offer</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Expires</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {negotiations.map(neg => (
                <tr key={neg.id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{neg.id?.slice(0, 8)}...</td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{neg.order_id?.slice(0, 8)}...</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 600,
                      background: neg.status === 'RESOLVED' ? '#065f46' : neg.status === 'EXPIRED' ? '#7f1d1d' : '#92400e',
                      color: neg.status === 'RESOLVED' ? '#6ee7b7' : neg.status === 'EXPIRED' ? '#fca5a5' : '#fcd34d',
                    }}>{neg.status}</span>
                  </td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>${neg.current_offer?.amount?.toFixed(2) || '—'}</td>
                  <td style={{ padding: '16px', fontSize: '14px', color: '#94a3b8' }}>{new Date(neg.expires_at).toLocaleString()}</td>
                  <td style={{ padding: '16px' }}>
                    {neg.status === 'UNDER_REVIEW' && (
                      <button
                        onClick={() => handleResolveNegotiation(neg.id, { resolution_type: 'ADMIN_ASSIGNED', amount: neg.current_offer?.amount })}
                        style={{ padding: '6px 12px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}
                      >
                        Resolve
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {negotiations.length === 0 && <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>No negotiations found</div>}
        </div>
      )}

      {activeTab === 'assignments' && (
        <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#0f172a' }}>
              <tr>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Assignment ID</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Driver</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Vehicle</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Earnings</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Assigned</th>
              </tr>
            </thead>
            <tbody>
              {assignments.map(assignment => (
                <tr key={assignment.id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{assignment.id?.slice(0, 8)}...</td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{assignment.driver_name || '—'}</td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{assignment.vehicle_type || '—'}</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 600,
                      background: assignment.status === 'COMPLETED' ? '#065f46' : assignment.status === 'ACCEPTED' ? '#065f46' : '#92400e',
                      color: assignment.status === 'COMPLETED' ? '#6ee7b7' : assignment.status === 'ACCEPTED' ? '#6ee7b7' : '#fcd34d',
                    }}>{assignment.status}</span>
                  </td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>${assignment.earnings?.toFixed(2) || '0.00'}</td>
                  <td style={{ padding: '16px', fontSize: '14px', color: '#94a3b8' }}>{new Date(assignment.assigned_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {assignments.length === 0 && <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>No driver assignments found</div>}
        </div>
      )}

      {activeTab === 'disputes' && (
        <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#0f172a' }}>
              <tr>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Dispute ID</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Type</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Priority</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Amount</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Created</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {disputes.map(dispute => (
                <tr key={dispute.id} style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{dispute.id?.slice(0, 8)}...</td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>{dispute.dispute_type}</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 600,
                      background: dispute.priority === 'URGENT' ? '#7f1d1d' : dispute.priority === 'HIGH' ? '#92400e' : '#1e293b',
                      color: dispute.priority === 'URGENT' ? '#fca5a5' : dispute.priority === 'HIGH' ? '#fcd34d' : '#94a3b8',
                    }}>{dispute.priority}</span>
                  </td>
                  <td style={{ padding: '16px' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 600,
                      background: dispute.status === 'RESOLVED' ? '#065f46' : dispute.status === 'UNDER_REVIEW' ? '#065f46' : '#92400e',
                      color: dispute.status === 'RESOLVED' ? '#6ee7b7' : dispute.status === 'UNDER_REVIEW' ? '#6ee7b7' : '#fcd34d',
                    }}>{dispute.status}</span>
                  </td>
                  <td style={{ padding: '16px', fontSize: '14px' }}>${dispute.disputed_amount?.toFixed(2) || '0.00'}</td>
                  <td style={{ padding: '16px', fontSize: '14px', color: '#94a3b8' }}>{new Date(dispute.created_at).toLocaleString()}</td>
                  <td style={{ padding: '16px' }}>
                    {dispute.status === 'OPEN' && (
                      <button
                        onClick={() => handleResolveDispute(dispute.id, { resolution_type: 'NO_REFUND', notes: 'Admin reviewed' })}
                        style={{ padding: '6px 12px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}
                      >
                        Resolve
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {disputes.length === 0 && <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>No disputes found</div>}
        </div>
      )}
    </div>
  );
}
