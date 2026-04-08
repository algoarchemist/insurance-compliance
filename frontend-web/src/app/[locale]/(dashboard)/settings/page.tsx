'use client';

import { useTranslations } from 'next-intl';
import { useAccessibilityStore, useAuthStore } from '@/stores';

export default function SettingsPage() {
  const t = useTranslations();
  const { user } = useAuthStore();
  const { largeText, highContrast, voiceNavigation, toggleLargeText, toggleHighContrast, toggleVoiceNavigation } = useAccessibilityStore();

  return (
    <div className="space-y-8 animate-slide-up">
      <h1 className="section-title">{t('common.settings')}</h1>

      {/* Profile */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">{t('common.profile')}</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Name:</span> <span className="font-medium">{user?.full_name}</span></div>
          <div><span className="text-gray-500">Phone:</span> <span className="font-medium">{user?.phone}</span></div>
          <div><span className="text-gray-500">SwasthID:</span> <span className="font-mono text-blue-600">{user?.swasth_id}</span></div>
          <div><span className="text-gray-500">ABHA:</span> <span className="font-mono">{user?.abha_number || '—'}</span></div>
          <div><span className="text-gray-500">Role:</span> <span className="badge-info">{user?.role}</span></div>
        </div>
      </div>

      {/* Accessibility */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">{t('accessibility.title')}</h2>
        <div className="space-y-4">
          {[
            { label: t('accessibility.largeText'), active: largeText, toggle: toggleLargeText, icon: '🔤' },
            { label: t('accessibility.highContrast'), active: highContrast, toggle: toggleHighContrast, icon: '🌗' },
            { label: t('accessibility.voiceNavigation'), active: voiceNavigation, toggle: toggleVoiceNavigation, icon: '🎤' },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between p-3 rounded-xl hover:bg-gray-50">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </div>
              <button
                onClick={item.toggle}
                className={`w-14 h-8 rounded-full transition-all duration-300 ${
                  item.active ? 'bg-blue-500' : 'bg-gray-200'
                }`}
              >
                <div className={`w-6 h-6 rounded-full bg-white shadow-md transform transition-transform ${
                  item.active ? 'translate-x-7' : 'translate-x-1'
                }`} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Language */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">{t('accessibility.language')}</h2>
        <div className="grid grid-cols-5 gap-3">
          {[
            { code: 'en', name: 'English' },
            { code: 'ta', name: 'தமிழ்' },
            { code: 'hi', name: 'हिन्दी' },
            { code: 'bn', name: 'বাংলা' },
            { code: 'te', name: 'తెలుగు' },
          ].map((lang) => (
            <button
              key={lang.code}
              className="p-3 rounded-xl border-2 border-gray-200 hover:border-blue-400 transition-colors text-center"
            >
              <p className="font-semibold">{lang.name}</p>
              <p className="text-xs text-gray-400">{lang.code.toUpperCase()}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
