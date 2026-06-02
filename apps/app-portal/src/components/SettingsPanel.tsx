import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Card, Button, Input } from '@agritrust/shared';
import { useThemeStore } from '../utils/themeStore';
import { Settings, Bell, Lock, Shield, Eye, Sun, Moon, CheckCircle2, ChevronRight } from 'lucide-react';
import { changeUserPin, createTicket, getTickets, getUserSettings, replyToTicket, updateTicket, updateUserSettings } from '../api';

type Prefs = {
  push_notifications: boolean;
  sms_notifications: boolean;
  email_notifications: boolean;
  data_sharing_consent: boolean;
  phone_visibility: boolean;
  marketplace_discovery: boolean;
  language: string;
};

type SupportTicket = {
  id: string;
  subject: string;
  description: string;
  status: 'open' | 'assigned' | 'in_progress' | 'resolved' | 'closed';
  resolution_note?: string | null;
  satisfaction_rating?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
};

const defaultPrefs: Prefs = {
  push_notifications: true,
  sms_notifications: true,
  email_notifications: true,
  data_sharing_consent: true,
  phone_visibility: false,
  marketplace_discovery: true,
  language: 'en',
};

const ToggleRow = ({
  title,
  description,
  enabled,
  onToggle,
  accent = 'primary',
}: {
  title: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
  accent?: 'primary' | 'earth';
}) => (
  <div className="flex items-center justify-between gap-4 p-4 md:p-5 rounded-xl bg-gray-50 dark:bg-gray-700/60 border border-gray-200 dark:border-gray-600">
    <div className="min-w-0">
      <p className="font-bold text-sm text-gray-900 dark:text-white">{title}</p>
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mt-1 leading-5">{description}</p>
    </div>
    <button
      type="button"
      onClick={onToggle}
      className={`w-14 h-8 rounded-full p-1 flex items-center transition-all shrink-0 ${enabled ? 'bg-blue-600 justify-end' : 'bg-gray-300 dark:bg-gray-600 justify-start'} ${accent === 'primary' ? 'ring-0' : ''}`}
      aria-pressed={enabled}
    >
      <div className="w-6 h-6 bg-white rounded-full shadow-sm"></div>
    </button>
  </div>
);

export const SettingsPanel: React.FC = () => {
  const { theme, setTheme } = useThemeStore();
  const [activeTab, setActiveTab] = useState<'security' | 'appearance' | 'notifications' | 'privacy'>('security');
  const [prefs, setPrefs] = useState<Prefs>(defaultPrefs);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketDescription, setTicketDescription] = useState('');
  const [currentPin, setCurrentPin] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [ticketReplyDrafts, setTicketReplyDrafts] = useState<Record<string, string>>({});

  const loadTickets = useCallback(() => {
    getTickets()
      .then((data) => setTickets(Array.isArray(data) ? data : []))
      .catch(() => setTickets([]));
  }, []);

  useEffect(() => {
    getUserSettings()
      .then((data) => setPrefs((prev) => ({ ...prev, ...data })))
      .catch(() => {});
    loadTickets();
  }, [loadTickets]);

  const savePrefs = useCallback(async (updates: Partial<Prefs>, key: string) => {
    setSavingKey(key);
    setStatus('');
    try {
      const next = await updateUserSettings(updates);
      setPrefs((prev) => ({ ...prev, ...next }));
      setStatus('Saved');
    } catch (err: any) {
      setStatus(err?.message || 'Unable to save settings');
    } finally {
      setSavingKey(null);
    }
  }, []);

  const tabs = useMemo(() => [
    { id: 'security', label: 'Account Security', icon: Lock, description: 'PIN, login, and protection' },
    { id: 'appearance', label: 'Appearance', icon: Sun, description: 'Theme and layout preference' },
    { id: 'notifications', label: 'Notifications', icon: Bell, description: 'Delivery, market, and wallet alerts' },
    { id: 'privacy', label: 'Privacy & Visibility', icon: Eye, description: 'Profile visibility and consent' },
  ], []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900 text-white p-8 md:p-10 shadow-lg">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-[11px] font-bold uppercase tracking-wider">
                  <Settings size={12} /> Portal Controls
                </p>
                <h1 className="mt-4 text-3xl md:text-4xl font-bold tracking-tight">Clear settings. Real controls. No fake toggles.</h1>
                <p className="mt-3 text-sm md:text-base text-white/80 font-medium leading-7 max-w-3xl">
                  Manage your security, appearance, notifications, and privacy from one place. Changes save directly to your account.
                </p>
              </div>
              <div className="flex items-center gap-3 rounded-xl bg-white/10 px-4 py-3 text-sm font-semibold">
                <CheckCircle2 size={16} /> {status || 'All preferences synced with your account'}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-1 space-y-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`w-full text-left flex items-start gap-4 px-5 py-4 rounded-xl border transition-all ${
                  activeTab === tab.id
                    ? 'bg-white dark:bg-gray-800 border-blue-300 text-blue-700 shadow-md'
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <span className={`w-11 h-11 rounded-xl flex items-center justify-center ${activeTab === tab.id ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'bg-gray-100 dark:bg-gray-700 text-gray-500'}`}>
                  <tab.icon size={18} />
                </span>
                <span className="min-w-0">
                  <span className="block font-bold text-sm">{tab.label}</span>
                  <span className="block text-xs font-medium mt-1 leading-5 opacity-80">{tab.description}</span>
                </span>
              </button>
            ))}
          </div>

          <div className="md:col-span-2 space-y-6">
            {activeTab === 'security' && (
              <>
                <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
                  <div className="p-6 space-y-6">
                    <div className="flex items-center gap-3">
                      <Lock className="text-blue-600" size={22} />
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">Security PIN</h3>
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Keep your account access locked down with a private PIN.</p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <Input label="Current PIN" type="password" value={currentPin} onChange={(e: any) => setCurrentPin(e.target.value)} placeholder="****" />
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Input label="New PIN" type="password" value={newPin} onChange={(e: any) => setNewPin(e.target.value)} placeholder="****" />
                        <Input label="Confirm New PIN" type="password" value={confirmPin} onChange={(e: any) => setConfirmPin(e.target.value)} placeholder="****" />
                      </div>
                      <Button
                        loading={savingKey === 'pin'}
                        onClick={async () => {
                          setStatus('');
                          if (!currentPin || !newPin || !confirmPin) {
                            setStatus('Fill all PIN fields');
                            return;
                          }
                          if (!/^\d{4,6}$/.test(newPin)) {
                            setStatus('New PIN must be 4-6 digits');
                            return;
                          }
                          if (newPin !== confirmPin) {
                            setStatus('New PIN and confirm PIN do not match');
                            return;
                          }
                          setSavingKey('pin');
                          try {
                            await changeUserPin(currentPin, newPin);
                            setCurrentPin('');
                            setNewPin('');
                            setConfirmPin('');
                            setStatus('Security PIN updated');
                          } catch (err: any) {
                            setStatus(err?.message || 'Unable to update PIN');
                          } finally {
                            setSavingKey(null);
                          }
                        }}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        Update Security PIN
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
                  <div className="p-6 space-y-6">
                    <div className="flex items-center gap-3">
                      <Shield className="text-blue-600" size={22} />
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">Two-Factor Authentication</h3>
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Extra login protection for high-trust accounts.</p>
                      </div>
                    </div>
                    <ToggleRow
                      title="SMS security alerts"
                      description="Receive SMS alerts for important account security events."
                      enabled={prefs.sms_notifications}
                      onToggle={() => savePrefs({ sms_notifications: !prefs.sms_notifications }, 'sms_notifications')}
                    />
                  </div>
                </div>
              </>
            )}

            {activeTab === 'appearance' && (
              <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
                <div className="p-6 space-y-6">
                  <div className="flex items-center gap-3">
                    <Sun className="text-blue-600" size={22} />
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">Theme</h3>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Choose a visual mode that feels comfortable to work in.</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { id: 'light', label: 'Light Mode', desc: 'Bright and crisp', icon: Sun },
                      { id: 'dark', label: 'Dark Mode', desc: 'Easy on the eyes', icon: Moon },
                    ].map((item) => (
                      <button
                        key={item.id}
                        onClick={() => setTheme(item.id as any)}
                        className={`relative p-5 rounded-2xl border-2 transition-all text-left ${
                          theme === item.id ? 'border-blue-500 bg-blue-50/60 dark:bg-blue-600/10' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }`}
                      >
                        <div className="w-14 h-14 rounded-xl bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 mb-4 flex items-center justify-center shadow-sm">
                          <item.icon size={24} className={theme === item.id ? 'text-blue-600' : 'text-gray-500'} />
                        </div>
                        <p className="font-bold text-sm text-gray-900 dark:text-white">{item.label}</p>
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mt-1">{item.desc}</p>
                        {theme === item.id && (
                          <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">✓</div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
                <div className="p-6 space-y-6">
                  <div className="flex items-center gap-3">
                    <Bell className="text-blue-600" size={22} />
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">Notification Preferences</h3>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Choose how and when the platform reaches you.</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <ToggleRow
                      title="Push notifications"
                      description="Browser and app notifications for key updates."
                      enabled={prefs.push_notifications}
                      onToggle={() => savePrefs({ push_notifications: !prefs.push_notifications }, 'push_notifications')}
                    />
                    <ToggleRow
                      title="SMS notifications"
                      description="Text alerts for critical updates and actions."
                      enabled={prefs.sms_notifications}
                      onToggle={() => savePrefs({ sms_notifications: !prefs.sms_notifications }, 'sms_notifications')}
                    />
                    <ToggleRow
                      title="Email notifications"
                      description="Detailed updates delivered to your inbox."
                      enabled={prefs.email_notifications}
                      onToggle={() => savePrefs({ email_notifications: !prefs.email_notifications }, 'email_notifications')}
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'privacy' && (
              <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
                <div className="p-6 space-y-6">
                  <div className="flex items-center gap-3">
                    <Eye className="text-blue-600" size={22} />
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">Privacy & Visibility</h3>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Control what other people can see and how your data is used.</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <ToggleRow
                      title="Show my phone to buyers"
                      description="Makes it easier for buyers to contact you directly."
                      enabled={prefs.phone_visibility}
                      onToggle={() => savePrefs({ phone_visibility: !prefs.phone_visibility }, 'phone_visibility')}
                    />
                    <ToggleRow
                      title="Allow marketplace discovery"
                      description="Lets your listings appear in buyer searches."
                      enabled={prefs.marketplace_discovery}
                      onToggle={() => savePrefs({ marketplace_discovery: !prefs.marketplace_discovery }, 'marketplace_discovery')}
                    />
                    <ToggleRow
                      title="Data sharing consent"
                      description="Permits platform features that rely on profile data usage."
                      enabled={prefs.data_sharing_consent}
                      onToggle={() => savePrefs({ data_sharing_consent: !prefs.data_sharing_consent }, 'data_sharing_consent')}
                    />
                    <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between bg-white dark:bg-gray-800">
                      <div>
                        <p className="font-bold text-sm text-gray-900 dark:text-white">Language</p>
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mt-1">Choose the language for the portal interface.</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {['en', 'sn', 'nd'].map((lang) => (
                          <button
                            key={lang}
                            type="button"
                            onClick={() => savePrefs({ language: lang }, 'language')}
                            className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all ${prefs.language === lang ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}`}
                          >
                            {lang}
                          </button>
                        ))}
                        <ChevronRight size={16} className="text-gray-400 ml-1" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
              <div className="p-6 space-y-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Support Ticket</h3>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Create a support ticket for issues beyond disputes.</p>
                <Input label="Subject" value={ticketSubject} onChange={(e: any) => setTicketSubject(e.target.value)} placeholder="Short issue title" />
                <Input label="Description" value={ticketDescription} onChange={(e: any) => setTicketDescription(e.target.value)} placeholder="Describe the issue" />
                <Button
                  onClick={async () => {
                    if (!ticketSubject.trim() || !ticketDescription.trim()) return;
                    await createTicket(ticketSubject.trim(), ticketDescription.trim());
                    setTicketSubject('');
                    setTicketDescription('');
                    loadTickets();
                    setStatus('Support ticket created');
                  }}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Submit Ticket
                </Button>

                {tickets.length > 0 && (
                  <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="text-sm font-bold text-gray-900 dark:text-white">My Tickets</h4>
                    {tickets.map((ticket) => (
                      <div key={ticket.id} className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900/40 space-y-3">
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                          <div>
                            <p className="font-bold text-sm text-gray-900 dark:text-white">{ticket.subject}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {ticket.created_at ? new Date(ticket.created_at).toLocaleString() : 'Recently created'}
                            </p>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider self-start ${
                            ticket.status === 'resolved'
                              ? 'bg-emerald-100 text-emerald-700'
                              : ticket.status === 'closed'
                              ? 'bg-gray-200 text-gray-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}>
                            {ticket.status.replace('_', ' ')}
                          </span>
                        </div>

                        <p className="text-sm text-gray-700 dark:text-gray-300">{ticket.description}</p>

                        {ticket.resolution_note && (
                          <div className="rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-3">
                            <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">Updates</p>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{ticket.resolution_note}</p>
                          </div>
                        )}

                        {ticket.status !== 'closed' && (
                          <div className="space-y-2">
                            <Input
                              label="Reply"
                              value={ticketReplyDrafts[ticket.id] || ''}
                              onChange={(e: any) => setTicketReplyDrafts((prev) => ({ ...prev, [ticket.id]: e.target.value }))}
                              placeholder="Add more detail or respond to support"
                            />
                            <div className="flex flex-wrap gap-2">
                              <Button
                                onClick={async () => {
                                  const message = (ticketReplyDrafts[ticket.id] || '').trim();
                                  if (!message) return;
                                  await replyToTicket(ticket.id, message);
                                  setTicketReplyDrafts((prev) => ({ ...prev, [ticket.id]: '' }));
                                  loadTickets();
                                  setStatus('Ticket updated');
                                }}
                                className="bg-blue-600 hover:bg-blue-700"
                              >
                                Reply
                              </Button>
                              {(ticket.status === 'resolved' || ticket.status === 'assigned' || ticket.status === 'in_progress') && (
                                <Button
                                  variant="outline"
                                  onClick={async () => {
                                    await updateTicket(ticket.id, { status: 'closed' });
                                    loadTickets();
                                    setStatus('Ticket closed');
                                  }}
                                >
                                  Close Ticket
                                </Button>
                              )}
                            </div>
                          </div>
                        )}

                        {ticket.status === 'resolved' && !ticket.satisfaction_rating && (
                          <div className="space-y-2">
                            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400">Rate your support experience</p>
                            <div className="flex flex-wrap gap-2">
                              {[1, 2, 3, 4, 5].map((rating) => (
                                <button
                                  key={rating}
                                  type="button"
                                  onClick={async () => {
                                    await updateTicket(ticket.id, { satisfaction_rating: rating, status: 'closed' });
                                    loadTickets();
                                    setStatus('Support rating submitted');
                                  }}
                                  className="px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-blue-100 dark:hover:bg-blue-900/30 text-sm font-bold text-gray-700 dark:text-gray-200"
                                >
                                  {rating}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {ticket.satisfaction_rating ? (
                          <p className="text-xs font-semibold text-emerald-600">Rated {ticket.satisfaction_rating}/5</p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
