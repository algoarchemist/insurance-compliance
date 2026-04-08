'use client';

import { useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { hospitalsApi } from '@/lib/api';

export default function HospitalsPage() {
  const t = useTranslations();
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['hospitals', search, typeFilter],
    queryFn: () => hospitalsApi.list({ city: search, type: typeFilter || undefined }).then((r) => r.data),
  });

  return (
    <div className="space-y-6 animate-slide-up">
      <h1 className="section-title">{t('hospitals.title')}</h1>

      {/* Search & Filter */}
      <div className="flex gap-4">
        <input
          id="hospital-search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('hospitals.searchPlaceholder')}
          className="input-field flex-1"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="input-field w-48"
        >
          <option value="">All Types</option>
          <option value="government">Government</option>
          <option value="private">Private</option>
          <option value="trust">Trust</option>
        </select>
        <button className="btn-accent">📍 {t('hospitals.nearMe')}</button>
      </div>

      {/* Hospital Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="shimmer h-48 rounded-2xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.hospitals?.map((h: any) => (
            <div key={h.id} className="card hover:border-blue-200 transition-all cursor-pointer group">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${
                    h.type === 'government' ? 'bg-green-100' : h.type === 'private' ? 'bg-blue-100' : 'bg-purple-100'
                  }`}>
                    🏥
                  </div>
                  <div>
                    <h3 className="font-semibold group-hover:text-blue-600 transition-colors">{h.name}</h3>
                    <p className="text-sm text-gray-500">{h.city}, {h.state}</p>
                  </div>
                </div>
                {h.distance_km && (
                  <span className="badge-info">{h.distance_km} km</span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <span className={`badge ${h.type === 'government' ? 'badge-success' : 'badge-info'}`}>{h.type}</span>
                {h.empanelment_type && (
                  <span className="badge-warning">{h.empanelment_type}</span>
                )}
                {h.specialities?.slice(0, 3).map((s: string) => (
                  <span key={s} className="badge bg-gray-100 text-gray-600">{s}</span>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center">
                <span className="text-sm text-gray-400">{h.phone}</span>
                <button className="text-blue-500 text-sm font-medium hover:text-blue-700">
                  {t('hospitals.viewCoverage')} →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      {data?.hospitals?.length === 0 && (
        <div className="card text-center py-12 text-gray-400">
          <span className="text-5xl block mb-3">🏥</span>
          <p>{t('common.noResults')}</p>
        </div>
      )}
    </div>
  );
}
