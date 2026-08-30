'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { claimsApi, bankApi } from '@/lib/api';

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

export default function ClaimDetailPage() {
  const t = useTranslations();
  const router = useRouter();
  const params = useParams();
  const claimId = params.id as string;
  const queryClient = useQueryClient();
  const [gaps, setGaps] = useState<any[] | null>(null);
  const [ocrResult, setOcrResult] = useState<any | null>(null);
  const [bankAccountId, setBankAccountId] = useState('');
  const [newBank, setNewBank] = useState({ account_number: '', ifsc_code: '', account_holder: '' });
  const [showAddBank, setShowAddBank] = useState(false);

  const { data: claim, isLoading } = useQuery({
    queryKey: ['claim', claimId],
    queryFn: () => claimsApi.get(claimId).then((r) => r.data),
  });

  const { data: bankData } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankApi.list().then((r) => r.data),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['claim', claimId] });

  const uploadMutation = useMutation({
    mutationFn: ({ file, docType }: { file: File; docType: string }) =>
      claimsApi.uploadDoc(claimId, file, docType),
    onSuccess: invalidate,
  });

  const ocrMutation = useMutation({
    mutationFn: () => claimsApi.parseOcr(claimId).then((r) => r.data),
    onSuccess: (data) => { setOcrResult(data); invalidate(); },
  });

  const gapMutation = useMutation({
    mutationFn: () => claimsApi.gapCheck(claimId).then((r) => r.data),
    onSuccess: (data) => setGaps(data.gaps || []),
  });

  const addBankMutation = useMutation({
    mutationFn: () => bankApi.add(newBank).then((r) => r.data),
    onSuccess: (data) => {
      setBankAccountId(data.bank_account_id);
      setShowAddBank(false);
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] });
    },
  });

  const submitMutation = useMutation({
    mutationFn: () => claimsApi.submit(claimId, { bank_account_id: bankAccountId, confirmed_by_user: true }).then((r) => r.data),
    onSuccess: invalidate,
  });

  if (isLoading || !claim) {
    return <div className="shimmer h-64 rounded-2xl" />;
  }

  const hasBill = claim.documents?.some((d: any) => d.doc_type === 'hospital_bill');
  const hasDischargeSummary = claim.documents?.some((d: any) => d.doc_type === 'discharge_summary');
  const canSubmit = claim.status === 'draft' && gaps?.length === 0 && bankAccountId;

  return (
    <div className="space-y-6 animate-slide-up max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <button onClick={() => router.push('/en/claims')} className="text-sm text-gray-400 hover:text-gray-600 mb-2">← {t('common.back')}</button>
          <h1 className="section-title mb-0">{t('claims.trackClaim')}</h1>
        </div>
        <span className={statusColors[claim.status] || 'badge-info'}>{claim.status?.replace(/_/g, ' ')}</span>
      </div>

      {/* Summary */}
      <div className="card grid grid-cols-3 gap-4">
        <div>
          <p className="text-sm text-gray-500">{t('claims.amount')}</p>
          <p className="text-2xl font-bold text-gray-900">₹{(claim.claim_amount || 0).toLocaleString()}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Approved</p>
          <p className="text-2xl font-bold text-emerald-600">{claim.approved_amount ? `₹${claim.approved_amount.toLocaleString()}` : '—'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Settled</p>
          <p className="text-2xl font-bold text-blue-600">{claim.settled_amount ? `₹${claim.settled_amount.toLocaleString()}` : '—'}</p>
        </div>
      </div>

      {claim.rejection_reason && (
        <div className="card border-2 border-red-200 bg-red-50">
          <p className="font-semibold text-red-700">Rejected: {claim.rejection_reason}</p>
          {claim.ai_rejection_explanation && <p className="text-sm text-red-600 mt-2">{claim.ai_rejection_explanation}</p>}
        </div>
      )}

      {/* Document Upload */}
      <div className="card space-y-4">
        <h2 className="font-semibold text-lg">{t('claims.uploadBill')}</h2>
        <div className="flex flex-wrap gap-3">
          <label className={`btn-secondary cursor-pointer ${hasBill ? 'opacity-50' : ''}`}>
            {hasBill ? '✓ Hospital Bill Uploaded' : 'Upload Hospital Bill'}
            <input type="file" className="hidden" onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) uploadMutation.mutate({ file, docType: 'hospital_bill' });
            }} />
          </label>
          <label className={`btn-secondary cursor-pointer ${hasDischargeSummary ? 'opacity-50' : ''}`}>
            {hasDischargeSummary ? '✓ Discharge Summary Uploaded' : 'Upload Discharge Summary'}
            <input type="file" className="hidden" onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) uploadMutation.mutate({ file, docType: 'discharge_summary' });
            }} />
          </label>
        </div>

        <button onClick={() => ocrMutation.mutate()} disabled={ocrMutation.isPending} className="btn-accent">
          {ocrMutation.isPending ? t('common.loading') : `🤖 ${t('claims.parseWithAi')}`}
        </button>

        {(ocrResult || claim.ocr_extracted) && (
          <div className="bg-gray-50 rounded-xl p-4 space-y-2">
            <p className="text-sm font-semibold text-gray-600">Extracted Items:</p>
            {(ocrResult?.items || claim.ocr_extracted?.items || []).map((item: any, i: number) => (
              <div key={i} className="flex justify-between text-sm">
                <span>{item.description}</span>
                <span className="font-mono">₹{item.amount}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Gap Check */}
      <div className="card space-y-4">
        <h2 className="font-semibold text-lg">{t('claims.checkGaps')}</h2>
        <button onClick={() => gapMutation.mutate()} disabled={gapMutation.isPending} className="btn-secondary">
          {gapMutation.isPending ? t('common.loading') : t('claims.checkGaps')}
        </button>
        {gaps && (
          gaps.length === 0 ? (
            <p className="text-emerald-600 font-medium">✓ No gaps found. Ready to submit.</p>
          ) : (
            <div className="space-y-2">
              {gaps.map((g: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                  <span>⚠️</span>
                  <span>{g.message}</span>
                </div>
              ))}
            </div>
          )
        )}
      </div>

      {/* Submit */}
      {claim.status === 'draft' && (
        <div className="card space-y-4">
          <h2 className="font-semibold text-lg">{t('claims.submitClaim')}</h2>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-2">{t('claims.selectBank')}</label>
            <select value={bankAccountId} onChange={(e) => setBankAccountId(e.target.value)} className="input-field">
              <option value="">Select bank account</option>
              {bankData?.accounts?.map((a: any) => (
                <option key={a.id} value={a.id}>{a.bank_name} — {a.account_holder}</option>
              ))}
            </select>
            <button onClick={() => setShowAddBank(!showAddBank)} className="text-blue-500 text-sm mt-2 hover:text-blue-700">
              + Add new bank account
            </button>
          </div>

          {showAddBank && (
            <div className="bg-gray-50 rounded-xl p-4 space-y-3">
              <input placeholder="Account Number" value={newBank.account_number}
                onChange={(e) => setNewBank({ ...newBank, account_number: e.target.value })} className="input-field" />
              <input placeholder="IFSC Code" value={newBank.ifsc_code}
                onChange={(e) => setNewBank({ ...newBank, ifsc_code: e.target.value })} className="input-field" />
              <input placeholder="Account Holder Name" value={newBank.account_holder}
                onChange={(e) => setNewBank({ ...newBank, account_holder: e.target.value })} className="input-field" />
              <button onClick={() => addBankMutation.mutate()} className="btn-primary w-full">Add Account</button>
            </div>
          )}

          <button onClick={() => submitMutation.mutate()} disabled={!canSubmit || submitMutation.isPending} className="btn-primary w-full">
            {submitMutation.isPending ? t('common.loading') : t('claims.submitClaim')}
          </button>
        </div>
      )}

      {/* Timeline */}
      <div className="card">
        <h2 className="font-semibold text-lg mb-4">Timeline</h2>
        <div className="space-y-4">
          {claim.timeline?.map((entry: any, i: number) => (
            <div key={i} className="flex items-start gap-3">
              <div className="timeline-dot mt-1.5" />
              <div>
                <p className="font-medium capitalize">{entry.status.replace(/_/g, ' ')}</p>
                <p className="text-xs text-gray-400">{new Date(entry.timestamp).toLocaleString()}</p>
                {entry.notes && <p className="text-sm text-gray-500 mt-1">{entry.notes}</p>}
              </div>
            </div>
          ))}
          {(!claim.timeline || claim.timeline.length === 0) && (
            <p className="text-gray-400 text-sm">No status updates yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
