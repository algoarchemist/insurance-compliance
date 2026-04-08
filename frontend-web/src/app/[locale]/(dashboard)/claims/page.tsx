'use client';

import { useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { claimsApi } from '@/lib/api';

const statusColors: Record<string, string> = {
  draft: 'badge-info',
  pre_auth_pending: 'badge-warning',
  pre_auth_approved: 'badge-success',
  submitted: 'badge-warning',
  processing: 'badge-warning',
  settled: 'badge-success',
  rejected: 'badge-danger',
  partial_settled: 'badge-warning',
  query_raised: 'badge-danger',
};

export default function ClaimsPage() {
  const t = useTranslations();
  const router = useRouter();

  const { data, isLoading } = useQuery({
    queryKey: ['claims'],
    queryFn: () => claimsApi.list().then((r) => r.data),
  });

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <h1 className="section-title">{t('claims.title')}</h1>
        <button onClick={() => router.push('/en/claims/new')} className="btn-primary">
          + {t('claims.fileClaim')}
        </button>
      </div>

      {/* Status Tabs */}
      <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-2">
        {['All', 'Draft', 'Submitted', 'Processing', 'Settled', 'Rejected'].map((s) => (
          <button key={s} className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
            s === 'All' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}>
            {s}
          </button>
        ))}
      </div>

      {/* Claims List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => <div key={i} className="shimmer h-24 rounded-2xl" />)}
        </div>
      ) : (
        <div className="space-y-4">
          {data?.claims?.map((claim: any) => (
            <div
              key={claim.id}
              onClick={() => router.push(`/en/claims/${claim.id}`)}
              className="card hover:border-blue-200 cursor-pointer group transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-2xl">
                    {claim.claim_type === 'cashless' ? '💳' : '💰'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold group-hover:text-blue-600 transition-colors">
                        {claim.hospital_name || `${claim.claim_type} Claim`}
                      </h3>
                      <span className={statusColors[claim.status] || 'badge-info'}>
                        {claim.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">
                      {new Date(claim.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold text-gray-900">₹{(claim.claim_amount || 0).toLocaleString()}</p>
                  {claim.approved_amount && (
                    <p className="text-sm text-emerald-600">Approved: ₹{claim.approved_amount.toLocaleString()}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
          {(!data?.claims || data.claims.length === 0) && (
            <div className="card text-center py-16 text-gray-400">
              <span className="text-6xl block mb-4">📄</span>
              <p className="text-lg mb-4">{t('common.noResults')}</p>
              <button onClick={() => router.push('/en/claims/new')} className="btn-primary">
                {t('claims.fileClaim')}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
