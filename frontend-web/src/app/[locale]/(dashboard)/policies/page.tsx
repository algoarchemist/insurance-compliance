'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { policiesApi } from '@/lib/api';

export default function PoliciesPage() {
  const t = useTranslations();
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: () => policiesApi.list().then((r) => r.data),
  });

  const pmjayMutation = useMutation({
    mutationFn: () => policiesApi.checkPmjay().then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['policies'] }),
  });

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center justify-between">
        <h1 className="section-title">{t('policies.title')}</h1>
        <div className="flex gap-3">
          <button onClick={() => pmjayMutation.mutate()} className="btn-accent" disabled={pmjayMutation.isPending}>
            {pmjayMutation.isPending ? '🔄' : '🔍'} {t('policies.checkPmjay')}
          </button>
          <button onClick={() => setShowAdd(!showAdd)} className="btn-primary">
            + {t('policies.addPolicy')}
          </button>
        </div>
      </div>

      {/* PMJAY Result */}
      {pmjayMutation.data && (
        <div className={`card border-2 ${pmjayMutation.data.eligible ? 'border-green-300 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <div className="flex items-center gap-4">
            <span className="text-4xl">{pmjayMutation.data.eligible ? '✅' : '❌'}</span>
            <div>
              <p className="font-bold text-lg">{pmjayMutation.data.eligible ? 'You are eligible for PMJAY!' : 'Not eligible for PMJAY'}</p>
              {pmjayMutation.data.eligible && <p className="text-gray-600">Coverage: ₹{(pmjayMutation.data.coverage_amount || 0).toLocaleString()}</p>}
            </div>
          </div>
        </div>
      )}

      {/* Summary */}
      {data && (
        <div className="grid grid-cols-2 gap-4">
          <div className="stat-card">
            <p className="text-sm text-gray-500">{t('policies.coverage')}</p>
            <p className="text-2xl font-bold text-blue-600">₹{((data.total_coverage || 0) / 100000).toFixed(1)}L</p>
          </div>
          <div className="stat-card">
            <p className="text-sm text-gray-500">{t('dashboard.activePolicies')}</p>
            <p className="text-2xl font-bold text-emerald-600">{data.active_count}</p>
          </div>
        </div>
      )}

      {/* Policies List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => <div key={i} className="shimmer h-24" />)}
        </div>
      ) : (
        <div className="space-y-4">
          {data?.policies?.map((policy: any) => (
            <div key={policy.id} className="card hover:border-blue-200 transition-all group">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${
                    policy.policy_type === 'pmjay' ? 'bg-green-100' : policy.policy_type === 'private' ? 'bg-blue-100' : 'bg-purple-100'
                  }`}>
                    {policy.policy_type === 'pmjay' ? '🏛️' : policy.policy_type === 'private' ? '🏢' : '💼'}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{policy.insurer_name}</h3>
                    <p className="text-gray-500 text-sm">{policy.scheme_name || policy.policy_number}</p>
                    <div className="flex gap-3 mt-2">
                      <span className="badge-info">{policy.policy_type}</span>
                      {policy.tpa_name && <span className="badge-warning">TPA: {policy.tpa_name}</span>}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-blue-600">₹{((policy.coverage_amount || 0) / 100000).toFixed(1)}L</p>
                  <p className="text-sm text-gray-400">
                    Remaining: ₹{((policy.sum_insured_remaining || 0) / 100000).toFixed(1)}L
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Valid till: {policy.valid_until ? new Date(policy.valid_until).toLocaleDateString() : '—'}
                  </p>
                </div>
              </div>
            </div>
          ))}
          {(!data?.policies || data.policies.length === 0) && (
            <div className="card text-center py-12 text-gray-400">
              <span className="text-5xl block mb-3">📋</span>
              <p>No policies yet. Check PMJAY or add a private policy.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
