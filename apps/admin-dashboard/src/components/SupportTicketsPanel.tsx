import React, { useEffect, useMemo, useState } from 'react';
import { assignTicket, fetchTickets, fetchUsers, replyToTicket, updateTicket } from '../api';

export default function SupportTicketsPanel({ token, profile }) {
  const [tickets, setTickets] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [replyDraft, setReplyDraft] = useState('');
  const [resolutionNote, setResolutionNote] = useState('');
  const [assignTo, setAssignTo] = useState('');
  const [busy, setBusy] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ticketData, userData] = await Promise.all([
        fetchTickets(token),
        fetchUsers(token),
      ]);
      setTickets(Array.isArray(ticketData) ? ticketData : []);
      setUsers(Array.isArray(userData) ? userData : []);
    } catch (err) {
      console.error('Failed to load support tickets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadData();
  }, [token]);

  const selectedTicket = useMemo(
    () => tickets.find((ticket) => ticket.id === selectedTicketId) || tickets[0] || null,
    [tickets, selectedTicketId],
  );

  useEffect(() => {
    if (selectedTicket) {
      setSelectedTicketId(selectedTicket.id);
      setResolutionNote(selectedTicket.resolution_note || '');
      setAssignTo(selectedTicket.assigned_to || '');
    }
  }, [selectedTicket?.id]);

  const supportUsers = users.filter((user) => ['SUPER_ADMIN', 'SUPPORT_ADMIN', 'ADMIN'].includes(String(user.role).toUpperCase()));

  const handleAssign = async () => {
    if (!selectedTicket || !assignTo) return;
    setBusy(true);
    try {
      await assignTicket(token, selectedTicket.id, assignTo);
      await loadData();
      alert('Ticket assigned successfully.');
    } catch (err) {
      alert(`Assignment failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleReply = async () => {
    if (!selectedTicket || !replyDraft.trim()) return;
    setBusy(true);
    try {
      await replyToTicket(token, selectedTicket.id, replyDraft.trim());
      setReplyDraft('');
      await loadData();
      alert('Reply sent.');
    } catch (err) {
      alert(`Reply failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleStatusUpdate = async (status) => {
    if (!selectedTicket) return;
    setBusy(true);
    try {
      await updateTicket(token, selectedTicket.id, {
        status,
        resolution_note: resolutionNote || undefined,
      });
      await loadData();
      alert(`Ticket marked ${status.replace('_', ' ')}.`);
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ padding: 24 }}>
      <section style={{
        borderRadius: 28, padding: 24, marginBottom: 22,
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 48%, #1d4ed8 100%)',
        color: '#fff', boxShadow: '0 22px 60px rgba(15,23,42,.16)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 900, letterSpacing: '.14em', textTransform: 'uppercase', color: '#bfdbfe', marginBottom: 10 }}>
              <i className="fas fa-headset" style={{ marginRight: 8 }} /> Support Operations
            </div>
            <h1 style={{ margin: 0, fontSize: 30, fontWeight: 950, letterSpacing: '-.04em' }}>Support Tickets</h1>
            <p style={{ margin: '10px 0 0', color: '#dbeafe', maxWidth: 680 }}>
              Assign, respond to, resolve, and close support tickets from one operational desk.
            </p>
          </div>
          <button onClick={loadData} style={{
            border: '1px solid rgba(255,255,255,.24)', background: 'rgba(255,255,255,.12)', color: '#fff',
            borderRadius: 16, padding: '12px 16px', fontWeight: 900, cursor: 'pointer',
          }}>
            <i className="fas fa-rotate" style={{ marginRight: 8 }} /> Refresh
          </button>
        </div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: '360px minmax(0, 1fr)', gap: 20 }}>
        <section style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 24, overflow: 'hidden' }}>
          <div style={{ padding: '18px 22px', borderBottom: '1px solid #e2e8f0' }}>
            <h2 style={{ margin: 0, color: '#0f172a', fontSize: 16, fontWeight: 950 }}>Ticket Queue</h2>
          </div>
          {loading ? (
            <div style={{ padding: 48, textAlign: 'center', color: '#64748b' }}>Loading tickets...</div>
          ) : tickets.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center', color: '#64748b' }}>No tickets available.</div>
          ) : (
            <div style={{ display: 'grid', gap: 10, padding: 12, maxHeight: '70vh', overflowY: 'auto' }}>
              {tickets.map((ticket) => (
                <button
                  key={ticket.id}
                  onClick={() => setSelectedTicketId(ticket.id)}
                  style={{
                    textAlign: 'left',
                    background: selectedTicket?.id === ticket.id ? '#eff6ff' : '#fff',
                    border: selectedTicket?.id === ticket.id ? '1px solid #93c5fd' : '1px solid #e2e8f0',
                    borderRadius: 18,
                    padding: 16,
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                    <strong style={{ color: '#0f172a' }}>{ticket.subject}</strong>
                    <span style={{ fontSize: 11, fontWeight: 900, textTransform: 'uppercase', color: '#2563eb' }}>{ticket.status}</span>
                  </div>
                  <p style={{ margin: '8px 0 0', color: '#64748b', fontSize: 13, lineHeight: 1.5 }}>
                    {ticket.description}
                  </p>
                </button>
              ))}
            </div>
          )}
        </section>

        <section style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 24, overflow: 'hidden' }}>
          <div style={{ padding: '18px 22px', borderBottom: '1px solid #e2e8f0' }}>
            <h2 style={{ margin: 0, color: '#0f172a', fontSize: 16, fontWeight: 950 }}>
              {selectedTicket ? selectedTicket.subject : 'Ticket Detail'}
            </h2>
          </div>
          {!selectedTicket ? (
            <div style={{ padding: 48, color: '#64748b' }}>Select a ticket to review its details.</div>
          ) : (
            <div style={{ padding: 24, display: 'grid', gap: 18 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
                <InfoCard label="Status" value={selectedTicket.status} />
                <InfoCard label="Assigned To" value={selectedTicket.assigned_to || 'Unassigned'} />
                <InfoCard label="Satisfaction" value={selectedTicket.satisfaction_rating ? `${selectedTicket.satisfaction_rating}/5` : 'Not rated'} />
              </div>

              <div style={{ background: '#f8fafc', borderRadius: 18, border: '1px solid #e2e8f0', padding: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 900, color: '#64748b', textTransform: 'uppercase', marginBottom: 8 }}>Description</div>
                <div style={{ color: '#0f172a', lineHeight: 1.6 }}>{selectedTicket.description}</div>
              </div>

              <div style={{ background: '#f8fafc', borderRadius: 18, border: '1px solid #e2e8f0', padding: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 900, color: '#64748b', textTransform: 'uppercase', marginBottom: 8 }}>Conversation / Notes</div>
                <div style={{ color: '#0f172a', lineHeight: 1.6, whiteSpace: 'pre-wrap', minHeight: 90 }}>
                  {selectedTicket.resolution_note || 'No replies or resolution notes yet.'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: 16 }}>
                <div>
                  <label style={labelStyle}>Reply</label>
                  <textarea
                    value={replyDraft}
                    onChange={(e) => setReplyDraft(e.target.value)}
                    placeholder="Send an update to the ticket owner..."
                    style={textareaStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Assign To</label>
                  <select value={assignTo} onChange={(e) => setAssignTo(e.target.value)} style={inputStyle}>
                    <option value="">Choose support user</option>
                    {supportUsers.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.full_name || user.phone_number} ({user.role})
                      </option>
                    ))}
                  </select>
                  <button onClick={handleAssign} disabled={busy || !assignTo} style={primaryButtonStyle('#1d4ed8', busy || !assignTo)}>
                    Assign Ticket
                  </button>
                </div>
              </div>

              <div>
                <label style={labelStyle}>Resolution Note</label>
                <textarea
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  placeholder="Document the final resolution..."
                  style={textareaStyle}
                />
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                <button onClick={handleReply} disabled={busy || !replyDraft.trim()} style={primaryButtonStyle('#0f766e', busy || !replyDraft.trim())}>
                  Send Reply
                </button>
                <button onClick={() => handleStatusUpdate('in_progress')} disabled={busy} style={secondaryButtonStyle}>
                  Mark In Progress
                </button>
                <button onClick={() => handleStatusUpdate('resolved')} disabled={busy} style={secondaryButtonStyle}>
                  Resolve Ticket
                </button>
                <button onClick={() => handleStatusUpdate('closed')} disabled={busy} style={secondaryButtonStyle}>
                  Close Ticket
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function InfoCard({ label, value }) {
  return (
    <div style={{ padding: 16, borderRadius: 18, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
      <div style={{ fontSize: 11, fontWeight: 900, color: '#64748b', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ marginTop: 8, fontWeight: 800, color: '#0f172a', wordBreak: 'break-word' }}>{value}</div>
    </div>
  );
}

const labelStyle = {
  display: 'block',
  fontSize: 11,
  fontWeight: 900,
  color: '#64748b',
  textTransform: 'uppercase',
  marginBottom: 8,
  letterSpacing: '.08em',
};

const inputStyle = {
  width: '100%',
  padding: '12px 14px',
  borderRadius: 14,
  border: '1px solid #cbd5e1',
  background: '#fff',
  color: '#0f172a',
  outline: 'none',
  marginBottom: 12,
};

const textareaStyle = {
  width: '100%',
  minHeight: 110,
  padding: '12px 14px',
  borderRadius: 14,
  border: '1px solid #cbd5e1',
  background: '#fff',
  color: '#0f172a',
  outline: 'none',
  resize: 'vertical',
};

const primaryButtonStyle = (bg, disabled) => ({
  width: '100%',
  padding: '12px 16px',
  borderRadius: 14,
  border: 'none',
  background: disabled ? '#94a3b8' : bg,
  color: '#fff',
  fontWeight: 900,
  cursor: disabled ? 'not-allowed' : 'pointer',
});

const secondaryButtonStyle = {
  padding: '12px 16px',
  borderRadius: 14,
  border: '1px solid #cbd5e1',
  background: '#fff',
  color: '#0f172a',
  fontWeight: 800,
  cursor: 'pointer',
};
