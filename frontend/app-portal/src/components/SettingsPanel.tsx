import React, { useState } from 'react';
import { Card, Button, Input } from '@agritrust/shared';
import { useThemeStore } from '../utils/themeStore';
import { Settings, Bell, Lock, Shield, Eye, Smartphone, Sun, Moon, Monitor } from 'lucide-react';

export const SettingsPanel: React.FC = () => {
  const { theme, toggleTheme, setTheme } = useThemeStore();
  const [activeTab, setActiveTab] = useState('security');

  const tabs = [
    { id: 'security', label: 'Account Security', icon: Lock },
    { id: 'appearance', label: 'Appearance', icon: Sun },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'privacy', label: 'Privacy & Visibility', icon: Eye },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <h1 className="text-3xl font-black text-earth-800 dark:text-white">System Settings</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-4 px-6 py-4 rounded-2xl font-black text-sm transition-all ${
                activeTab === tab.id
                  ? 'bg-white dark:bg-earth-700 border-2 border-primary-500 text-primary-600 shadow-lg shadow-primary-100 dark:shadow-none'
                  : 'bg-white dark:bg-earth-800 border-2 border-transparent text-earth-500 dark:text-earth-400 hover:bg-earth-50 dark:hover:bg-earth-700'
              }`}
            >
              <tab.icon size={18} /> {tab.label}
            </button>
          ))}
        </div>

        <div className="md:col-span-2 space-y-6">
          {activeTab === 'security' && (
            <>
              <Card>
                <div className="flex items-center gap-3 mb-8">
                  <Lock className="text-primary-600" size={24} />
                  <h3 className="text-lg font-black text-earth-800 dark:text-white">Security PIN</h3>
                </div>
                <div className="space-y-6">
                  <Input label="Current PIN" type="password" placeholder="••••" />
                  <div className="grid grid-cols-2 gap-4">
                    <Input label="New PIN" type="password" placeholder="••••" />
                    <Input label="Confirm New PIN" type="password" placeholder="••••" />
                  </div>
                  <Button>Update Security PIN</Button>
                </div>
              </Card>

              <Card>
                <div className="flex items-center gap-3 mb-8">
                  <Shield className="text-primary-600" size={24} />
                  <h3 className="text-lg font-black text-earth-800 dark:text-white">Two-Factor Authentication</h3>
                </div>
                <div className="flex items-center justify-between p-6 bg-earth-50 dark:bg-earth-700 rounded-2xl">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-white dark:bg-earth-600 flex items-center justify-center text-primary-600 shadow-sm">
                      <Smartphone size={24} />
                    </div>
                    <div>
                      <p className="font-black text-earth-800 dark:text-white">SMS Verification</p>
                      <p className="text-xs font-bold text-earth-400">Receive a code via SMS for every login.</p>
                    </div>
                  </div>
                  <div className="w-14 h-8 bg-primary-600 rounded-full p-1 flex items-center justify-end">
                    <div className="w-6 h-6 bg-white rounded-full shadow-sm"></div>
                  </div>
                </div>
              </Card>
            </>
          )}

          {activeTab === 'appearance' && (
            <Card>
              <div className="flex items-center gap-3 mb-8">
                <Sun className="text-primary-600" size={24} />
                <h3 className="text-lg font-black text-earth-800 dark:text-white">Theme</h3>
              </div>
              <p className="text-sm text-earth-500 dark:text-earth-400 font-bold mb-6">Choose how ZimAgriTrust looks for you. Select a theme below.</p>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setTheme('light')}
                  className={`relative p-6 rounded-2xl border-2 transition-all text-center group ${
                    theme === 'light' ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-600/10' : 'border-earth-100 dark:border-earth-600 hover:border-earth-200 dark:hover:border-earth-500'
                  }`}
                >
                  <div className="w-16 h-16 rounded-2xl bg-white border-2 border-earth-100 mx-auto mb-4 flex items-center justify-center shadow-sm">
                    <Sun size={28} className="text-yellow-500" />
                  </div>
                  <p className="font-black text-sm text-earth-800 dark:text-white">Light Mode</p>
                  <p className="text-[10px] font-bold text-earth-400 mt-1">Clean and bright</p>
                  {theme === 'light' && (
                    <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-primary-600 flex items-center justify-center">
                      <span className="text-white text-xs">✓</span>
                    </div>
                  )}
                </button>
                <button
                  onClick={() => setTheme('dark')}
                  className={`relative p-6 rounded-2xl border-2 transition-all text-center group ${
                    theme === 'dark' ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-600/10' : 'border-earth-100 dark:border-earth-600 hover:border-earth-200 dark:hover:border-earth-500'
                  }`}
                >
                  <div className="w-16 h-16 rounded-2xl bg-earth-800 border-2 border-earth-600 mx-auto mb-4 flex items-center justify-center shadow-sm">
                    <Moon size={28} className="text-blue-400" />
                  </div>
                  <p className="font-black text-sm text-earth-800 dark:text-white">Dark Mode</p>
                  <p className="text-[10px] font-bold text-earth-400 mt-1">Easy on the eyes</p>
                  {theme === 'dark' && (
                    <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-primary-600 flex items-center justify-center">
                      <span className="text-white text-xs">✓</span>
                    </div>
                  )}
                </button>
              </div>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <div className="flex items-center gap-3 mb-8">
                <Bell className="text-primary-600" size={24} />
                <h3 className="text-lg font-black text-earth-800 dark:text-white">Notification Preferences</h3>
              </div>
              <div className="space-y-4">
                {['Order Updates', 'New Offers', 'Price Alerts', 'Wallet Activity', 'System Announcements'].map((item) => (
                  <div key={item} className="flex items-center justify-between p-4 bg-earth-50 dark:bg-earth-700 rounded-2xl">
                    <span className="font-black text-sm text-earth-800 dark:text-white">{item}</span>
                    <div className="w-14 h-8 bg-primary-600 rounded-full p-1 flex items-center justify-end cursor-pointer">
                      <div className="w-6 h-6 bg-white rounded-full shadow-sm"></div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {activeTab === 'privacy' && (
            <Card>
              <div className="flex items-center gap-3 mb-8">
                <Eye className="text-primary-600" size={24} />
                <h3 className="text-lg font-black text-earth-800 dark:text-white">Privacy & Visibility</h3>
              </div>
              <div className="space-y-4">
                {[
                  { label: 'Show my phone to buyers', desc: 'Visible on your public profile' },
                  { label: 'Show region publicly', desc: 'Helps buyers find local sellers' },
                  { label: 'Allow marketplace discovery', desc: 'Your listings appear in search results' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between p-4 bg-earth-50 dark:bg-earth-700 rounded-2xl">
                    <div>
                      <p className="font-black text-sm text-earth-800 dark:text-white">{item.label}</p>
                      <p className="text-[10px] font-bold text-earth-400">{item.desc}</p>
                    </div>
                    <div className="w-14 h-8 bg-primary-600 rounded-full p-1 flex items-center justify-end cursor-pointer">
                      <div className="w-6 h-6 bg-white rounded-full shadow-sm"></div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
