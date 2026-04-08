'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useAuthStore, useAccessibilityStore } from '@/stores';

const navItems = [
  { href: '/en/dashboard', label: 'dashboard', icon: '🏠' },
  { href: '/en/policies', label: 'policies', icon: '📋' },
  { href: '/en/hospitals', label: 'hospitals', icon: '🏥' },
  { href: '/en/claims', label: 'claims', icon: '📄' },
  { href: '/en/caregiver', label: 'caregiver', icon: '🤝' },
  { href: '/en/settings', label: 'settings', icon: '⚙️' },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const t = useTranslations('common');
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { largeText } = useAccessibilityStore();

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col fixed h-full z-10 shadow-sm">
        {/* Logo */}
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-2xl font-bold text-gradient">{t('appName')}</h1>
          {user && (
            <p className="text-xs text-gray-400 mt-1 font-mono">{user.swasth_id}</p>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link ${pathname === item.href ? 'active' : ''}`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{t(item.label)}</span>
            </Link>
          ))}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-gray-100">
          {user && (
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                {user.full_name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user.full_name}</p>
                <p className="text-xs text-gray-400">{user.role}</p>
              </div>
            </div>
          )}
          <button
            onClick={() => { logout(); window.location.href = '/en/login'; }}
            className="w-full text-left nav-link text-red-500 hover:bg-red-50 hover:text-red-600"
          >
            <span>🚪</span>
            <span>{t('logout')}</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen">
        <div className="max-w-6xl mx-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
