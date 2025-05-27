import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { i18n, type Locale } from '@/i18n.config';

function getLocale(request: NextRequest): Locale {
  // Lấy locale từ URL path
  const pathname = request.nextUrl.pathname;
  const pathnameIsMissingLocale = i18n.locales.every(
    (locale) => !pathname.startsWith(`/${locale}/`) && pathname !== `/${locale}`
  );

  // Nếu URL không có locale, tìm locale phù hợp
  if (pathnameIsMissingLocale) {
    // Kiểm tra Accept-Language header
    const acceptLanguage = request.headers.get('accept-language');
    if (acceptLanguage) {
      const preferredLocale = acceptLanguage
        .split(',')
        .map((lang) => lang.split(';')[0].trim())
        .find((lang) => i18n.locales.includes(lang as Locale));
      
      if (preferredLocale) {
        return preferredLocale as Locale;
      }
    }
    
    return i18n.defaultLocale;
  }

  // Lấy locale từ pathname
  const segments = pathname.split('/');
  const locale = segments[1] as Locale;
  return i18n.locales.includes(locale) ? locale : i18n.defaultLocale;
}

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  
  // Bỏ qua các route đặc biệt
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/favicon.ico') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Kiểm tra xem pathname có locale chưa
  const pathnameIsMissingLocale = i18n.locales.every(
    (locale) => !pathname.startsWith(`/${locale}/`) && pathname !== `/${locale}`
  );

  // Redirect nếu không có locale
  if (pathnameIsMissingLocale) {
    const locale = getLocale(request);
    return NextResponse.redirect(
      new URL(`/${locale}${pathname}`, request.url)
    );
  }

  // Thêm locale vào headers
  const locale = getLocale(request);
  const response = NextResponse.next();
  response.headers.set('x-locale', locale);
  
  return response;
}

export const config = {
  matcher: [
    // Khớp tất cả paths trừ:
    // - api routes
    // - _next static files
    // - favicon.ico
    // - files with extensions
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)'
  ]
};
