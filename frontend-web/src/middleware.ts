import createMiddleware from 'next-intl/middleware';

export default createMiddleware({
  locales: ['en', 'ta', 'hi', 'bn', 'te'],
  defaultLocale: 'en',
});

export const config = {
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
};
