import { create } from 'zustand';

interface User {
  id: string;
  swasth_id: string;
  full_name: string;
  abha_number?: string;
  phone: string;
  is_elder: boolean;
  preferred_lang: string;
  role: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  accessToken: string | null;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

function loadStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: loadStoredUser(),
  isAuthenticated: typeof window !== 'undefined' && !!localStorage.getItem('access_token'),
  accessToken: typeof window !== 'undefined' ? localStorage.getItem('access_token') : null,

  login: (user, accessToken, refreshToken) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      localStorage.setItem('user', JSON.stringify(user));
    }
    set({ user, isAuthenticated: true, accessToken });
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
    set({ user: null, isAuthenticated: false, accessToken: null });
  },

  setUser: (user) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(user));
    }
    set({ user });
  },
}));


// Accessibility store
interface AccessibilityState {
  largeText: boolean;
  highContrast: boolean;
  voiceNavigation: boolean;
  fontSize: number;
  toggleLargeText: () => void;
  toggleHighContrast: () => void;
  toggleVoiceNavigation: () => void;
  setFontSize: (size: number) => void;
}

export const useAccessibilityStore = create<AccessibilityState>((set) => ({
  largeText: false,
  highContrast: false,
  voiceNavigation: false,
  fontSize: 16,

  toggleLargeText: () =>
    set((s) => ({ largeText: !s.largeText, fontSize: s.largeText ? 16 : 20 })),
  toggleHighContrast: () =>
    set((s) => ({ highContrast: !s.highContrast })),
  toggleVoiceNavigation: () =>
    set((s) => ({ voiceNavigation: !s.voiceNavigation })),
  setFontSize: (size) => set({ fontSize: size }),
}));
