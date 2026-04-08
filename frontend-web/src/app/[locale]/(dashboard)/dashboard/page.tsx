'use client';

import { useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { policiesApi, claimsApi } from '@/lib/api';
import { useAuthStore } from '@/stores';

export default function DashboardPage() {
  const t = useTranslations();
  const router = useRouter();
  const { user } = useAuthStore();

  const { data: policiesData } = useQuery({
    queryKey: ['policies'],
    queryFn: () => policiesApi.list().then((r) => r.data),
  });

  const { data: claimsData } = useQuery({
    queryKey: ['claims'],
    queryFn: () => claimsApi.list().then((r) => r.data),
  });

  const stats = [
    {
      label: t('dashboard.totalCoverage'),
      value: `₹${((policiesData?.total_coverage || 0) / 100000).toFixed(1)}L`,
      icon: '🛡️',
      color: 'from-blue-500 to-cyan-400',
    },
    {
      label: t('dashboard.activePolicies'),
      value: policiesData?.active_count || 0,
      icon: '📋',
      color: 'from-emerald-500 to-teal-400',
    },
    {
      label: t('dashboard.pendingClaims'),
      value: claimsData?.claims?.filter((c: any) => !['settled', 'rejected'].includes(c.status)).length || 0,
      icon: '⏳',
      color: 'from-amber-500 to-orange-400',
    },
  ];

  const quickActions = [
    { label: t('dashboard.checkEligibility'), icon: '🔍', href: '/en/policies?check=true', color: 'bg-blue-50 text-blue-600 hover:bg-blue-100' },
    { label: t('dashboard.fileClaim'), icon: '📝', href: '/en/claims/new', color: 'bg-orange-50 text-orange-600 hover:bg-orange-100' },
    { label: t('dashboard.findHospital'), icon: '🏥', href: '/en/hospitals', color: 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100' },
    { label: t('dashboard.viewPolicies'), icon: '📋', href: '/en/policies', color: 'bg-purple-50 text-purple-600 hover:bg-purple-100' },
  ];

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Greeting */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {t('dashboard.greeting', { name: user?.full_name || 'User' })}
          </h1>
          <p className="text-gray-500 mt-1">
            {t('dashboard.swasthId')}: <span className="font-mono text-blue-600">{user?.swasth_id || '—'}</span>
          </p>
        </div>
        {user?.is_elder && (
          <span className="badge-info text-sm">👵 Elder</span>
        )}
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="card relative overflow-hidden group">
            <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-5 group-hover:opacity-10 transition-opacity`} />
            <div className="relative flex items-center gap-4">
              <div className="text-4xl">{stat.icon}</div>
              <div>
                <p className="text-sm text-gray-500 font-medium">{stat.label}</p>
                <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('dashboard.quickActions')}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((action, i) => (
            <button
              key={i}
              onClick={() => router.push(action.href)}
              className={`${action.color} p-5 rounded-2xl text-left transition-all duration-300 hover:shadow-md hover:scale-[1.02] active:scale-[0.98]`}
            >
              <span className="text-3xl block mb-3">{action.icon}</span>
              <span className="font-semibold text-sm">{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Claims */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('dashboard.recentClaims')}</h2>
        {claimsData?.claims?.length > 0 ? (
          <div className="space-y-3">
            {claimsData.claims.slice(0, 5).map((claim: any) => (
              <div key={claim.id} className="card flex items-center justify-between hover:border-blue-200 cursor-pointer" onClick={() => router.push(`/en/claims/${claim.id}`)}>
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                    {claim.claim_type === 'cashless' ? '💳' : '💰'}
                  </div>
                  <div>
                    <p className="font-medium">{claim.hospital_name || 'Claim'}</p>
                    <p className="text-sm text-gray-400">{new Date(claim.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold">₹{((claim.claim_amount || 0)).toLocaleString()}</p>
                  <span className={`badge ${claim.status === 'settled' ? 'badge-success' : claim.status === 'rejected' ? 'badge-danger' : 'badge-warning'}`}>
                    {claim.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card text-center py-12 text-gray-400">
            <span className="text-5xl block mb-3">📄</span>
            <p>{t('common.noResults')}</p>
          </div>
        )}
      </div>
    </div>
  );
}
