import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NativeBaseProvider } from 'nativebase';
import { I18nextProvider } from 'react-i18next';
import i18n from '../lib/i18n';

const queryClient = new QueryClient();

export default function RootLayout() {
  return (
    <I18nextProvider i18n={i18n}>
      <NativeBaseProvider>
        <QueryClientProvider client={queryClient}>
          <StatusBar style="auto" />
          <Stack
            screenOptions={{
              headerStyle: { backgroundColor: '#0c8eeb' },
              headerTintColor: '#fff',
              headerTitleStyle: { fontWeight: 'bold' },
            }}
          >
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen name="login" options={{ headerShown: false }} />
          </Stack>
        </QueryClientProvider>
      </NativeBaseProvider>
    </I18nextProvider>
  );
}
