import React, { useEffect, useState } from 'react';
import { createAdminInvitation, listAdminInvitations, revokeAdminInvitation } from '../api';

const ROLE_OPTIONS = [
  'SYSTEM_ADMIN',
  'FINANCE_ADMIN',
  'REGIONAL_ADMIN',
  'SUPPORT_ADMIN',
  'BRANCH_ADMIN',
  'AGENT',
  'STAFF',
];

export default function AdminInvitationsPanel() {
  const [form, setForm] = useState({
    email: '',
    phone: '',
    role_name: 'SYSTEM_ADMIN',
    region: '',
    branch_id: '',
    expires_hours: 72,
  });
  const [invitations, setInvitations] = useState([]);
  const [createdLink, setCreatedLink] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function loadInvitations() {
    setLoading(true);
    setError('');
    try {
      const rows = await listAdminInvitations({ limit: 100 });
      setInvitations(Array.isArray(rows) ? rows : []);
    } catch (err) {
      setError(err.message || 'Failed to load invitations.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInvitations();
  }, []);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleCreate(e) {
    e.preventDefault();
    setSubmitting(true);
    setCreatedLink('');
    setError('');
    try {
      const payload = {
        email: form.email.trim(),
        phone: form.phone.trim() || undefined,
        role_name: form.role_name,
        region: form.region.trim() || undefined,
        branch_id: form.branch_id ? Number(form.branch_id) : undefined,
        expires_hours: Number(form.expires_hours) || 72,
      };
      const result = await createAdminInvitation(payload);
      setCreatedLink(result?.acceptance_link || '');
      setForm((current) => ({ ...current, email: '', phone: '', region: '', branch_id: '' }));
      await loadInvitations();
    } catch (err) {
      setError(err.message || 'Failed to create invitation.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRevoke(id) {
    if (!window.confirm('Revoke this pending invitation?')) return;
    setError('');
    try {
      await revokeAdminInvitation(id);
      await loadInvitations();
    } catch (err) {
      setError(err.message || 'Failed to revoke invitation.');
    }
  }

  async function copyLink() {
    if (!createdLink) return;
    await navigator.clipboard.writeText(createdLink);
    alert('Invitation link copied.');
  }

  return (
    <div className="reality-stack-v4 animate-fade-in">
      <div className="v4-glass-card-premium" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start', marginBottom: 20 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 24, fontWeight: 900 }}>Admin Invitations</h2>
            <p style={{ margin: '6px 0 0', color: 'var(--v4-text-dim)' }}>
              Invite platform administrators. Only super-admins can create or revoke these invitations.
            </p>
          </div>
          <button className="v4-action-btn" onClick={loadInvitations} disabled={loading}>
            <i className="fas fa-rotate"></i> Refresh
          </button>
        </div>

        {error && (
          <div style={{ background: 'rgba(239,68,68,.12)', border: '1px solid rgba(239,68,68,.35)', color: '#ef4444', padding: 12, borderRadius: 12, marginBottom: 16 }}>
            {error}
          </div>
        )}

        <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 18 }}>
          <Field label="Email" type="email" value={form.email} onChange={(v) => update('email', v)} required />
          <Field label="Phone / WhatsApp" value={form.phone} onChange={(v) => update('phone', v)} placeholder="+263..." />
          <div>
            <label style={labelStyle}>Role</label>
            <select value={form.role_name} onChange={(e) => update('role_name', e.target.value)} style={inputStyle}>
              {ROLE_OPTIONS.map((role) => <option key={role} value={role}>{role}</option>)}
            </select>
          </div>
          {form.role_name === 'REGIONAL_ADMIN' && (
            <Field label="Region" value={form.region} onChange={(v) => update('region', v)} required />
          )}
          {form.role_name === 'BRANCH_ADMIN' && (
            <Field label="Branch ID" type="number" value={form.branch_id} onChange={(v) => update('branch_id', v)} required />
          )}
          <Field label="Expires after hours" type="number" value={form.expires_hours} onChange={(v) => update('expires_hours', v)} required />
          <div style={{ display: 'flex', alignItems: 'end' }}>
            <button className="v4-action-btn primary" type="submit" disabled={submitting} style={{ width: '100%' }}>
              <i className="fas fa-paper-plane"></i> {submitting ? 'Sending…' : 'Send Invitation'}
            </button>
          </div>
        </form>

        {createdLink && (
          <div style={{ background: 'rgba(34,197,94,.12)', border: '1px solid rgba(34,197,94,.35)', padding: 14, borderRadius: 14, marginBottom: 20 }}>
            <strong>Invitation created.</strong>
            <p style={{ margin: '8px 0', wordBreak: 'break-all', color: 'var(--v4-text-dim)' }}>{createdLink}</p>
            <button className="v4-action-btn" onClick={copyLink}><i className="fas fa-copy"></i> Copy Link</button>
          </div>
        )}
      </div>

      <div className="v4-glass-card-premium" style={{ padding: 24 }}>
        <h3 style={{ marginTop: 0 }}>Recent Invitations</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--v4-text-dim)', fontSize: 12 }}>
                <th style={thStyle}>Email</th>
                <th style={thStyle}>Role</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Expires</th>
                <th style={thStyle}>Created</th>
                <th style={thStyle}>Action</th>
              </tr>
            </thead>
            <tbody>
              {invitations.map((inv) => (
                <tr key={inv.id} style={{ borderTop: '1px solid var(--v4-border)' }}>
                  <td style={tdStyle}>{inv.email}</td>
                  <td style={tdStyle}>{inv.role}</td>
                  <td style={tdStyle}><StatusBadge status={inv.status} /></td>
                  <td style={tdStyle}>{formatDate(inv.expires_at)}</td>
                  <td style={tdStyle}>{formatDate(inv.created_at)}</td>
                  <td style={tdStyle}>
                    {String(inv.status).toUpperCase() === 'PENDING' && (
                      <button className="v4-action-btn danger" onClick={() => handleRevoke(inv.id)}>Revoke</button>
                    )}
                  </td>
                </tr>
              ))}
              {!loading && invitations.length === 0 && (
                <tr><td colSpan="6" style={{ ...tdStyle, textAlign: 'center', color: 'var(--v4-text-dim)' }}>No invitations found.</td></tr>
              )}
              {loading && (
                <tr><td colSpan="6" style={{ ...tdStyle, textAlign: 'center', color: 'var(--v4-text-dim)' }}>Loading invitations…</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', required, placeholder }) {
  return (
    <div>
      <label style={labelStyle}>{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} required={required} placeholder={placeholder} style={inputStyle} />
    </div>
  );
}

function StatusBadge({ status }) {
  const normalized = String(status || '').toUpperCase();
  const color = normalized === 'PENDING' ? '#f59e0b' : normalized === 'ACCEPTED' ? '#22c55e' : '#94a3b8';
  return <span style={{ color, fontWeight: 900 }}>{normalized || 'UNKNOWN'}</span>;
}

function formatDate(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

const labelStyle = { display: 'block', marginBottom: 6, fontSize: 12, fontWeight: 900, color: 'var(--v4-text-dim)' };
const inputStyle = { width: '100%', padding: '11px 12px', borderRadius: 12, border: '1px solid var(--v4-border)', background: 'var(--v4-bg)', color: 'var(--v4-text)', outline: 'none' };
const thStyle = { padding: '10px 8px', borderBottom: '1px solid var(--v4-border)' };
const tdStyle = { padding: '12px 8px', fontSize: 13, verticalAlign: 'middle' };
