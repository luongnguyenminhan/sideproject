import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { i18n, type Locale } from '@/i18n.config';

// Define protected routes that require authentication
const protectedRoutes = [
  '/home',
  '/dashboard',
  '/profile',
  '/settings',
];

// Define auth routes that should redirect authenticated users
const authRoutes = [
  '/auth',
  '/login',
  '/signup',
];

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

  // Get authentication status
  const accessToken = request.cookies.get('access_token')?.value;
  const isAuthenticated = !!accessToken;

  // Extract locale and actual path
  const localeRegex = /^\/([a-z]{2})(\/.*)?$/;
  const localeMatch = pathname.match(localeRegex);
  let locale: string = '';
  let actualPath = pathname;
  
  if (localeMatch) {
    locale = localeMatch[1];
    actualPath = localeMatch[2] || '/';
  }

  // Check authentication requirements before locale handling
  if (locale && i18n.locales.includes(locale as Locale)) {
    // Check if the current path is protected
    const isProtectedRoute = protectedRoutes.some(route => 
      actualPath === route || actualPath.startsWith(route + '/')
    );

    // Check if the current path is an auth route
    const isAuthRoute = authRoutes.some(route => 
      actualPath === route || actualPath.startsWith(route + '/')
    );

    // Redirect unauthenticated users away from protected routes
    if (isProtectedRoute && !isAuthenticated) {
      const authUrl = new URL(`/${locale}/auth`, request.url);
      // Preserve the intended destination for redirect after login
      authUrl.searchParams.set('callbackUrl', pathname);
      return NextResponse.redirect(authUrl);
    }

    // Redirect authenticated users away from auth routes
    if (isAuthRoute && isAuthenticated) {
      const homeUrl = new URL(`/${locale}`, request.url);
      return NextResponse.redirect(homeUrl);
    }
  }

  // Kiểm tra xem pathname có locale chưa
  const pathnameIsMissingLocale = i18n.locales.every(
    (locale) => !pathname.startsWith(`/${locale}/`) && pathname !== `/${locale}`
  );

  // Redirect nếu không có locale
  if (pathnameIsMissingLocale) {
    const detectedLocale = getLocale(request);
    const newPathname = `/${detectedLocale}${pathname}`;
    
    // Check auth requirements for the new path after adding locale
    const newActualPath = pathname || '/';
    const isProtectedRoute = protectedRoutes.some(route => 
      newActualPath === route || newActualPath.startsWith(route + '/')
    );
    
    if (isProtectedRoute && !isAuthenticated) {
      // Redirect to auth with locale
      const authUrl = new URL(`/${detectedLocale}/auth`, request.url);
      authUrl.searchParams.set('callbackUrl', newPathname);
      return NextResponse.redirect(authUrl);
    }
    
    return NextResponse.redirect(new URL(newPathname, request.url));
  }

  // Thêm locale vào headers
  const detectedLocale = getLocale(request);
  const response = NextResponse.next();
  response.headers.set('x-locale', detectedLocale);
  
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
