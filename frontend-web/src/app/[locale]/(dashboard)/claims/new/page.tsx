'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { policiesApi, hospitalsApi, claimsApi } from '@/lib/api';

export default function NewClaimPage() {
  const t = useTranslations();
  const router = useRouter();
  const [policyId, setPolicyId] = useState('');
  const [hospitalId, setHospitalId] = useState('');
  const [admissionDate, setAdmissionDate] = useState('');
  const [dischargeDate, setDischargeDate] = useState('');
  const [amount, setAmount] = useState('');
  const [error, setError] = useState('');

  const { data: policiesData } = useQuery({
    queryKey: ['policies'],
    queryFn: () => policiesApi.list().then((r) => r.data),
  });

  const { data: hospitalsData } = useQuery({
    queryKey: ['hospitals'],
    queryFn: () => hospitalsApi.list().then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      claimsApi.reimbursement({
        policy_id: policyId,
        hospital_id: hospitalId || undefined,
        admission_date: admissionDate,
        discharge_date: dischargeDate,
        claim_amount: amount,
      }).then((r) => r.data),
    onSuccess: (data) => router.push(`/en/claims/${data.claim_id}`),
    onError: (err: any) => setError(err.response?.data?.detail || 'Failed to create claim'),
  });

  const canSubmit = policyId && admissionDate && dischargeDate && Number(amount) > 0;

  return (
    <div className="space-y-6 animate-slide-up max-w-2xl">
      <h1 className="section-title">{t('claims.reimbursementClaim')}</h1>

      <div className="card space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">{t('policies.title')}</label>
          <select value={policyId} onChange={(e) => setPolicyId(e.target.value)} className="input-field">
            <option value="">Select a policy</option>
            {policiesData?.policies?.map((p: any) => (
              <option key={p.id} value={p.id}>{p.insurer_name} — {p.scheme_name || p.policy_number}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">{t('hospitals.title')} (optional)</label>
          <select value={hospitalId} onChange={(e) => setHospitalId(e.target.value)} className="input-field">
            <option value="">Select a hospital</option>
            {hospitalsData?.hospitals?.map((h: any) => (
              <option key={h.id} value={h.id}>{h.name} — {h.city}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">Admission Date</label>
            <input type="date" value={admissionDate} onChange={(e) => setAdmissionDate(e.target.value)} className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">Discharge Date</label>
            <input type="date" value={dischargeDate} onChange={(e) => setDischargeDate(e.target.value)} className="input-field" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-2">{t('claims.amount')} (₹)</label>
          <input type="number" min="1" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="e.g. 45000" className="input-field" />
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <div className="flex gap-3 pt-2">
          <button
            onClick={() => createMutation.mutate()}
            disabled={!canSubmit || createMutation.isPending}
            className="btn-primary flex-1"
          >
            {createMutation.isPending ? t('common.loading') : t('common.next')}
          </button>
          <button onClick={() => router.push('/en/claims')} className="btn-secondary">
            {t('common.cancel')}
          </button>
        </div>
      </div>
    </div>
  );
}
