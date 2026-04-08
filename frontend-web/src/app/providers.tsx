'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { useAccessibilityStore } from '@/stores';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  const { largeText, highContrast, fontSize } = useAccessibilityStore();

  return (
    <QueryClientProvider client={queryClient}>
      <div
        className={`${largeText ? 'large-text' : ''} ${highContrast ? 'high-contrast' : ''}`}
        style={{ fontSize: `${fontSize}px` }}
      >
        {children}
      </div>
    </QueryClientProvider>
  );
}
