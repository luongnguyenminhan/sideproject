import { getDictionary, createTranslator } from '@/utils/translation';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import type { UserResponse } from '@/types/auth.type';
import Image from 'next/image';
import React from 'react';
import { cookies } from 'next/headers';
import authApi from '@/apis/authApi';
import ThemeSwapper from '@/components/global/themeSwapper';
import AuthHeader from '@/components/layout/authHeader';
import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faComments, faQuestionCircle, faInfoCircle } from '@fortawesome/free-solid-svg-icons';
import { TranslationProvider } from '@/contexts/TranslationContext';
import { ReduxProvider } from '@/redux/provider';

// getMeServer is correct as:
async function getMeServer(): Promise<UserResponse | null> {
  const cookieStore = await cookies(); // synchronous
  const accessToken = cookieStore.get('access_token')?.value;
  if (!accessToken) return null;
  return await authApi.getMe({ Authorization: `Bearer ${accessToken}` });
}

export default async function Header() {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);
  const user = await getMeServer();

  const navigationItems = [
    { href: `/${locale}/chat`, label: t('navigation.chat'), icon: faComments },
    { href: `/${locale}/about`, label: t('navigation.about'), icon: faInfoCircle },
    { href: `/${locale}/help`, label: t('navigation.help'), icon: faQuestionCircle },
  ];

  return (
    <ReduxProvider>
      <header className="w-full px-8 md:px-6 py-2 flex items-center justify-between bg-gradient-to-r from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] shadow-lg dark:shadow-xl transition-all duration-500 min-h-0 h-14">
        <div className="flex items-center gap-2">
          <Link href={`/${locale}`} className="flex items-center gap-2">
            <Image
              src="/assets/logo/logo_web.png"
              alt="App Logo"
              width={80}
              height={30}
              className="!m-4"
            />
            <span className="hidden md:inline text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]">
              {t('common.branding')}
            </span>
          </Link>
        </div>

        {/* Navigation Menu */}
        <nav className="hidden lg:flex items-center gap-1">
          {navigationItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-[color:var(--foreground)] hover:bg-[color:var(--muted)] hover:text-[color:var(--primary)] transition-all duration-200"
            >
              <FontAwesomeIcon icon={item.icon} className="w-4 h-4" />
              <span className="hidden xl:inline">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {/* Mobile Navigation Dropdown */}
          <div className="lg:hidden relative group">
            <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-[color:var(--foreground)] hover:bg-[color:var(--muted)] transition-all duration-200">
              <FontAwesomeIcon icon={faHome} className="w-4 h-4" />
              <span className="hidden sm:inline">{t('navigation.menu')}</span>
            </button>
            
            {/* Dropdown Menu */}
            <div className="absolute right-0 top-full mt-2 w-48 bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              {navigationItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-[color:var(--card-foreground)] hover:bg-[color:var(--muted)] first:rounded-t-lg last:rounded-b-lg transition-colors duration-200"
                >
                  <FontAwesomeIcon icon={item.icon} className="w-4 h-4" />
                  {item.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Theme and Language Switchers moved here for compact header */}
          <div className="fixed min-h-0 bottom-4 right-4 z-[9999]">
            <ThemeSwapper />
          </div>
          
          <TranslationProvider dictionary={dictionary} locale={locale}>
            <AuthHeader
              user={user}
              locale={locale}
            />
          </TranslationProvider>
        </div>
      </header>
    </ReduxProvider>
  );
}
