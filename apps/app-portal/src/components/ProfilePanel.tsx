import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuthStore, Button, Input } from '@agritrust/shared';
import { getProfile, getVerificationStatus, updateProfile as apiUpdateProfile } from '../api';
import { Phone, MapPin, ShieldCheck, Mail, Edit3, Shield, Save, X, Loader2, Calendar } from 'lucide-react';

export const ProfilePanel: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const [profile, setProfile] = useState<any>(null);
  const [verification, setVerification] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editData, setEditData] = useState({ full_name: '', email: '', region: '' });
  const hasLoaded = useRef(false);

  const loadProfile = useCallback(async () => {
    if (hasLoaded.current) return; // Prevent repeated calls
    hasLoaded.current = true;
    setLoading(true);
    try {
      const [prof, verif] = await Promise.allSettled([
        getProfile(),
        getVerificationStatus(),
      ]);
      if (prof.status === 'fulfilled' && prof.value) {
        setProfile(prof.value);
        updateUser(prof.value);
        setEditData({
          full_name: prof.value.full_name || user?.full_name || '',
          email: prof.value.email || '',
          region: prof.value.region || prof.value.province || '',
        });
      }
      if (verif.status === 'fulfilled' && verif.value) {
        setVerification(verif.value);
      }
    } catch { /* fallback to store data */ }
    setLoading(false);
  }, [updateUser, user?.full_name]);

  useEffect(() => {
    loadProfile();
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const updated = await apiUpdateProfile(editData);
      setProfile((p: any) => ({ ...p, ...updated }));
      updateUser(updated);
      setEditing(false);
    } catch { /* silent */ }
    setSaving(false);
  }, [editData, updateUser]);

  const displayName = profile?.full_name || user?.full_name || 'User';
  const displayPhone = profile?.phone_number || profile?.phone || user?.phone || '—';
  const displayEmail = profile?.email || 'Not linked';
  const displayRegion = profile?.region || profile?.province || 'Zimbabwe';
  const displayScore = profile?.trust_score ?? user?.trust_score ?? 0;
  const displayRole = profile?.role || user?.role || 'user';
  const memberSince = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : 'May 2026';
  const dealsCount = profile?.deals_closed ?? profile?.completed_orders ?? 0;

  const verificationSteps = [
    { label: 'Phone Verified', done: true },
    { label: 'ID Document', done: verification?.id_verified ?? false },
    { label: 'Biometrics Set', done: verification?.biometrics_set ?? false },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={32} className="animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="p-4 lg:p-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Account Profile</h1>
            {editing ? (
              <div className="flex gap-3">
                <Button variant="ghost" size="sm" onClick={() => setEditing(false)} className="text-gray-600 dark:text-gray-400">
                  <X size={16} className="mr-2" /> Cancel
                </Button>
                <Button size="sm" loading={saving} onClick={handleSave} className="bg-emerald-600 hover:bg-emerald-700">
                  <Save size={16} className="mr-2" /> Save
                </Button>
              </div>
            ) : (
              <Button variant="outline" size="sm" onClick={() => setEditing(true)} className="border-gray-300 dark:border-gray-600">
                <Edit3 size={16} className="mr-2" /> Edit Profile
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Profile Card */}
          <div className="md:col-span-1">
            <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden text-center">
              <div className="p-6">
                <div className="relative inline-block mx-auto mb-6">
                  <div className="w-32 h-32 rounded-2xl bg-gray-100 dark:bg-gray-700 border-4 border-white dark:border-gray-800 shadow-lg flex items-center justify-center text-4xl font-bold text-gray-400 dark:text-gray-500">
                    {displayName.charAt(0)}
                  </div>
                  <div className="absolute -bottom-2 -right-2 w-10 h-10 rounded-xl bg-emerald-600 border-4 border-white dark:border-gray-800 flex items-center justify-center text-white shadow-md">
                    <ShieldCheck size={20} />
                  </div>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{displayName}</h2>
                <p className="text-sm font-bold text-emerald-600 uppercase tracking-wider mt-1">{displayRole} NODE</p>
                
                <div className="mt-8 flex justify-center gap-8 border-t border-gray-200 dark:border-gray-700 pt-8">
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{displayScore}%</p>
                    <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Trust Score</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{dealsCount}</p>
                    <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Deals Closed</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Details */}
          <div className="md:col-span-2 space-y-6">
            <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Personal Information</h3>
              </div>
              <div className="p-6">
                {editing ? (
                  <div className="space-y-5">
                    <Input label="Full Name" value={editData.full_name} onChange={(e) => setEditData({ ...editData, full_name: e.target.value })} />
                    <Input label="Email Address" type="email" value={editData.email} onChange={(e) => setEditData({ ...editData, email: e.target.value })} placeholder="Enter your email" />
                    <Input label="Primary Region" value={editData.region} onChange={(e) => setEditData({ ...editData, region: e.target.value })} placeholder="e.g. Harare" />
                  </div>
                ) : (
                  <div className="grid sm:grid-cols-2 gap-8">
                    <div className="space-y-2">
                      <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                        <Phone size={12} /> Phone Number
                      </p>
                      <p className="font-semibold text-gray-900 dark:text-white">{displayPhone}</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                        <Mail size={12} /> Email Address
                      </p>
                      <p className="font-semibold text-gray-900 dark:text-white">{displayEmail}</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                        <MapPin size={12} /> Primary Region
                      </p>
                      <p className="font-semibold text-gray-900 dark:text-white">{displayRegion}</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                        <Calendar size={12} /> Member Since
                      </p>
                      <p className="font-semibold text-gray-900 dark:text-white">{memberSince}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-900 dark:bg-gray-800 text-white overflow-hidden">
              <div className="p-6">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center text-emerald-400">
                    <Shield size={24} />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Identity Verification</h3>
                    <p className="text-sm font-medium text-gray-400">
                      {verificationSteps.every(s => s.done) ? 'Your account is fully verified and secure.' : 'Complete all steps to verify your account.'}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-3">
                  {verificationSteps.map((step) => (
                    <div key={step.label} className={`px-4 py-2 rounded-xl border flex items-center gap-2 ${step.done ? 'bg-white/5 border-white/10' : 'bg-white/[0.02] border-white/5 opacity-50'}`}>
                      <ShieldCheck size={14} className={step.done ? 'text-emerald-400' : 'text-gray-500'} />
                      <span className="text-xs font-bold uppercase tracking-wider">{step.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
