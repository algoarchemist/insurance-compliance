'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/stores';

export default function LoginPage() {
  const t = useTranslations();
  const router = useRouter();
  const { login } = useAuthStore();
  const [step, setStep] = useState<'aadhaar' | 'otp'>('aadhaar');
  const [aadhaar, setAadhaar] = useState('');
  const [otp, setOtp] = useState('');
  const [txnId, setTxnId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendOtp = async () => {
    if (aadhaar.length !== 12) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await authApi.initiateAadhaar(aadhaar);
      setTxnId(data.txn_id);
      setStep('otp');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otp.length !== 6) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await authApi.verifyAadhaar(txnId, otp);
      login(data.user, data.access_token, data.refresh_token);
      router.push('/en/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail?.error?.message || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/10 backdrop-blur-xl mb-4">
            <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">{t('common.appName')}</h1>
          <p className="text-blue-100 text-lg">{t('common.tagline')}</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          {step === 'aadhaar' ? (
            <>
              <h2 className="text-xl font-semibold mb-6 text-gray-900">{t('auth.enterAadhaar')}</h2>
              <input
                id="aadhaar-input"
                type="text"
                maxLength={12}
                value={aadhaar}
                onChange={(e) => setAadhaar(e.target.value.replace(/\D/g, ''))}
                placeholder={t('auth.aadhaarPlaceholder')}
                className="input-field text-center text-2xl tracking-[0.3em] font-mono mb-6"
                autoFocus
              />
              {error && <p className="text-red-500 text-sm mb-4 text-center">{error}</p>}
              <button
                id="send-otp-btn"
                onClick={handleSendOtp}
                disabled={aadhaar.length !== 12 || loading}
                className="btn-primary w-full text-lg"
              >
                {loading ? t('common.loading') : t('auth.sendOtp')}
              </button>
            </>
          ) : (
            <>
              <h2 className="text-xl font-semibold mb-2 text-gray-900">{t('auth.enterOtp')}</h2>
              <p className="text-gray-500 mb-6 text-sm">{t('auth.otpSent')}</p>
              <input
                id="otp-input"
                type="text"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                placeholder="● ● ● ● ● ●"
                className="input-field text-center text-3xl tracking-[0.5em] font-mono mb-6"
                autoFocus
              />
              {error && <p className="text-red-500 text-sm mb-4 text-center">{error}</p>}
              <button
                id="verify-otp-btn"
                onClick={handleVerifyOtp}
                disabled={otp.length !== 6 || loading}
                className="btn-primary w-full text-lg mb-3"
              >
                {loading ? t('common.loading') : t('auth.verifyOtp')}
              </button>
              <button
                onClick={() => { setStep('aadhaar'); setOtp(''); setError(''); }}
                className="btn-secondary w-full"
              >
                {t('common.back')}
              </button>
            </>
          )}
        </div>

        {/* Language Selector */}
        <div className="flex justify-center gap-3 mt-6">
          {['en', 'ta', 'hi', 'bn', 'te'].map((lang) => (
            <button
              key={lang}
              className="px-3 py-1 rounded-lg text-sm text-white/70 hover:text-white hover:bg-white/10 transition"
            >
              {lang.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
