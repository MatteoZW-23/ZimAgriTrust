import React, { useState, useEffect } from 'react';
import { useAuthStore, Card, Button, Input } from '@agritrust/shared';
import { getProfile, getVerificationStatus, updateProfile as apiUpdateProfile } from '../api';
import { User, Phone, MapPin, Star, ShieldCheck, Mail, Edit3, Shield, Save, X, Loader2, Calendar } from 'lucide-react';

export const ProfilePanel: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const [profile, setProfile] = useState<any>(null);
  const [verification, setVerification] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editData, setEditData] = useState({ full_name: '', email: '', region: '' });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
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
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await apiUpdateProfile(editData);
      setProfile((p: any) => ({ ...p, ...updated }));
      updateUser(updated);
      setEditing(false);
    } catch { /* silent */ }
    setSaving(false);
  };

  const displayName = profile?.full_name || user?.full_name || 'User';
  const displayPhone = profile?.phone_number || user?.phone || '—';
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
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-black text-earth-800 dark:text-white">Account Profile</h1>
        {editing ? (
          <div className="flex gap-3">
            <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
              <X size={16} className="mr-2" /> Cancel
            </Button>
            <Button size="sm" loading={saving} onClick={handleSave}>
              <Save size={16} className="mr-2" /> Save
            </Button>
          </div>
        ) : (
          <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
            <Edit3 size={16} className="mr-2" /> Edit Profile
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Profile Card */}
        <Card className="md:col-span-1 text-center">
          <div className="relative inline-block mx-auto mb-6">
            <div className="w-32 h-32 rounded-[2.5rem] bg-earth-100 dark:bg-earth-700 border-4 border-white dark:border-earth-800 shadow-xl flex items-center justify-center text-4xl font-black text-earth-400 dark:text-earth-200">
              {displayName.charAt(0)}
            </div>
            <div className="absolute -bottom-2 -right-2 w-10 h-10 rounded-2xl bg-primary-600 border-4 border-white dark:border-earth-800 flex items-center justify-center text-white shadow-lg">
              <ShieldCheck size={20} />
            </div>
          </div>
          <h2 className="text-2xl font-black text-earth-800 dark:text-white">{displayName}</h2>
          <p className="text-sm font-black text-primary-600 uppercase tracking-widest mt-1">{displayRole} NODE</p>
          
          <div className="mt-8 flex justify-center gap-8 border-t-2 border-earth-50 dark:border-earth-700 pt-8">
            <div>
              <p className="text-2xl font-black text-earth-800 dark:text-white">{displayScore}%</p>
              <p className="text-[10px] font-black text-earth-400 uppercase tracking-tighter">Trust Score</p>
            </div>
            <div>
              <p className="text-2xl font-black text-earth-800 dark:text-white">{dealsCount}</p>
              <p className="text-[10px] font-black text-earth-400 uppercase tracking-tighter">Deals Closed</p>
            </div>
          </div>
        </Card>

        {/* Details */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <h3 className="text-lg font-black text-earth-800 dark:text-white mb-6">Personal Information</h3>
            {editing ? (
              <div className="space-y-5">
                <Input label="Full Name" value={editData.full_name} onChange={(e) => setEditData({ ...editData, full_name: e.target.value })} />
                <Input label="Email Address" type="email" value={editData.email} onChange={(e) => setEditData({ ...editData, email: e.target.value })} placeholder="Enter your email" />
                <Input label="Primary Region" value={editData.region} onChange={(e) => setEditData({ ...editData, region: e.target.value })} placeholder="e.g. Harare" />
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-8">
                <div className="space-y-1">
                  <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest flex items-center gap-2">
                    <Phone size={12} /> Phone Number
                  </p>
                  <p className="font-bold text-earth-800 dark:text-earth-200">{displayPhone}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest flex items-center gap-2">
                    <Mail size={12} /> Email Address
                  </p>
                  <p className="font-bold text-earth-800 dark:text-earth-200">{displayEmail}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest flex items-center gap-2">
                    <MapPin size={12} /> Primary Region
                  </p>
                  <p className="font-bold text-earth-800 dark:text-earth-200">{displayRegion}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-black text-earth-400 uppercase tracking-widest flex items-center gap-2">
                    <Calendar size={12} /> Member Since
                  </p>
                  <p className="font-bold text-earth-800 dark:text-earth-200">{memberSince}</p>
                </div>
              </div>
            )}
          </Card>

          <Card className="bg-earth-900 dark:bg-earth-800 text-white border-none">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center text-primary-400">
                <Shield size={24} />
              </div>
              <div>
                <h3 className="text-lg font-black">Identity Verification</h3>
                <p className="text-sm font-medium text-earth-400">
                  {verificationSteps.every(s => s.done) ? 'Your account is fully verified and secure.' : 'Complete all steps to verify your account.'}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              {verificationSteps.map((step) => (
                <div key={step.label} className={`px-4 py-2 rounded-xl border flex items-center gap-2 ${step.done ? 'bg-white/5 border-white/10' : 'bg-white/[0.02] border-white/5 opacity-50'}`}>
                  <ShieldCheck size={14} className={step.done ? 'text-primary-500' : 'text-earth-500'} />
                  <span className="text-xs font-black uppercase tracking-wider">{step.label}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
