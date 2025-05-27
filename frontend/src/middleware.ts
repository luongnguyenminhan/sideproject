import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { i18n, Locale } from '@/i18n.config';

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const segments = pathname.split('/').filter(Boolean);
  const firstSegment = segments[0];
  
  // Check if the first segment is a valid locale
  const locale = i18n.locales.includes(firstSegment as Locale) ? firstSegment as Locale : undefined;

  const response = NextResponse.next();
  if (locale) {
    response.headers.set('x-locale', locale);
    response.headers.set('x-pathname', pathname);
  } else {
    // Set default locale if no valid locale found
    response.headers.set('x-locale', i18n.defaultLocale);
    response.headers.set('x-pathname', pathname);
  }
  return response;
}

export const config = {
  matcher: ['/((?!api|_next|favicon.ico).*)'], // exclude internal routes
};
