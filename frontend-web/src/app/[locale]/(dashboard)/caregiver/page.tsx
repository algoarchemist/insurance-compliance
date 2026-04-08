'use client';

import { useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { caregiverApi } from '@/lib/api';
import { useAuthStore } from '@/stores';

export default function CaregiverPage() {
  const t = useTranslations();
  const { user } = useAuthStore();
  const [invitePhone, setInvitePhone] = useState('');
  const [inviteMsg, setInviteMsg] = useState('');

  const { data: eldersData } = useQuery({
    queryKey: ['my-elders'],
    queryFn: () => caregiverApi.myElders().then((r) => r.data),
  });

  const handleInvite = async () => {
    try {
      await caregiverApi.invite(invitePhone);
      setInviteMsg('Invitation sent!');
      setInvitePhone('');
    } catch {
      setInviteMsg('Failed to send invitation');
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <h1 className="section-title">{t('common.caregiver')}</h1>

      {/* Invite Caregiver (if elder) */}
      {user?.is_elder && (
        <div className="card bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200">
          <h3 className="font-semibold mb-3">Invite a Caregiver</h3>
          <p className="text-sm text-gray-500 mb-4">Add a family member who can manage your insurance on your behalf.</p>
          <div className="flex gap-3">
            <input value={invitePhone} onChange={(e) => setInvitePhone(e.target.value)} placeholder="Caregiver's phone number" className="input-field flex-1" />
            <button onClick={handleInvite} className="btn-primary">Invite</button>
          </div>
          {inviteMsg && <p className="text-sm mt-2 text-blue-600">{inviteMsg}</p>}
        </div>
      )}

      {/* My Elders (if caregiver) */}
      {eldersData?.elders?.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Elders I Manage</h2>
          <div className="space-y-4">
            {eldersData.elders.map((elder: any) => (
              <div key={elder.elder_id} className="card hover:border-blue-200 cursor-pointer">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-2xl">👵</div>
                    <div>
                      <h3 className="font-semibold text-lg">{elder.name}</h3>
                      <p className="text-sm text-gray-500">ABHA: {elder.abha_number || '—'}</p>
                    </div>
                  </div>
                  <div className="flex gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-blue-600">{elder.policy_count}</p>
                      <p className="text-xs text-gray-400">Policies</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-orange-500">{elder.claim_count}</p>
                      <p className="text-xs text-gray-400">Claims</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!user?.is_elder && (!eldersData?.elders || eldersData.elders.length === 0) && (
        <div className="card text-center py-16 text-gray-400">
          <span className="text-6xl block mb-4">🤝</span>
          <p className="text-lg">No caregiver relationships yet</p>
          <p className="text-sm mt-2">Ask an elder to invite you, or invite a caregiver if you&apos;re over 60.</p>
        </div>
      )}
    </div>
  );
}
