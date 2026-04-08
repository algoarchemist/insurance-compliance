import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      appName: 'Sugamai',
      login: 'Login',
      dashboard: 'Dashboard',
      policies: 'My Policies',
      hospitals: 'Hospitals',
      claims: 'Claims',
      settings: 'Settings',
      enterAadhaar: 'Enter Aadhaar Number',
      sendOtp: 'Send OTP',
      verifyOtp: 'Verify OTP',
    },
  },
  ta: {
    translation: {
      appName: 'சுகமை',
      login: 'உள்நுழை',
      dashboard: 'முகப்பு',
      policies: 'என் பாலிசிகள்',
      hospitals: 'மருத்துவமனை',
      claims: 'க்ளெய்ம்கள்',
      settings: 'அமைப்புகள்',
      enterAadhaar: 'ஆதார் எண்ணை உள்ளிடவும்',
      sendOtp: 'OTP அனுப்பு',
      verifyOtp: 'OTP சரிபார்',
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
