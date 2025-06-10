import { getDictionary, createTranslator } from '@/utils/translation';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import type { UserResponse } from '@/types/auth.type';
import Image from 'next/image';
import React from 'react';
import { cookies } from 'next/headers';
import authApi from '@/apis/authApi';
import ThemeSwapper from '@/components/global/themeSwapper';
import FloatingChatBubble from '@/components/chat/FloatingChatBubble';
import AuthHeader from '@/components/layout/authHeader';
import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faComments, faQuestionCircle, faInfoCircle } from '@fortawesome/free-solid-svg-icons';
import { TranslationProvider } from '@/contexts/TranslationContext';
import { ReduxProvider } from '@/redux/provider';

// getMeServer is correct as:
async function getMeServer(): Promise<UserResponse | null> {
  const cookieStore = await cookies(); // synchronous
  const accessToken = cookieStore.get('access_token')?.value;
  if (!accessToken) return null;
  return await authApi.getMe({ Authorization: `Bearer ${accessToken}` });
}

export default async function Header({ withChatBubble = false }: { withChatBubble?: boolean }) {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);
  const user = await getMeServer();
  const isAuthenticated = !!user;

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

        {/* Navigation Menu (Desktop) */}
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
          {/* Theme and Language Switchers moved here for compact header */}
          <div className="fixed min-h-0 bottom-25 lg:bottom-4 right-4 z-[9999] flex flex-col gap-2 items-end">
            <ThemeSwapper />
            <TranslationProvider dictionary={dictionary} locale={locale}>
              {/* Show chat bubble only if withChatBubble and authenticated */}
              {withChatBubble && isAuthenticated && <FloatingChatBubble />}
            </TranslationProvider>
          </div>
          <TranslationProvider dictionary={dictionary} locale={locale}>
            <AuthHeader
              user={user}
              locale={locale}
            />
          </TranslationProvider>
        </div>
      </header>

      {/* Bottom Navigation for Mobile */}
      <nav className="flex lg:hidden fixed bottom-0 p-4 py-10 left-0 w-full z-50 bg-[color:var(--card)] border-t border-[color:var(--border)] shadow-t-md h-16 justify-around items-center">
        {navigationItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex flex-col items-center justify-center flex-1 py-2 group transition-all duration-200"
          >
            <span
              className="flex items-center justify-center w-10 h-10 rounded-full mb-1
                bg-gradient-to-br from-[color:var(--gradient-bg-from)] to-[color:var(--gradient-bg-to)]
                text-[color:var(--primary)] group-hover:scale-110 group-hover:shadow-lg group-hover:text-[color:var(--accent)]
                transition-all duration-200 animate-fade-in"
            >
              <FontAwesomeIcon icon={item.icon} className="w-6 h-6" />
            </span>
            <span className="text-xs text-[color:var(--muted-foreground)] group-hover:text-[color:var(--primary)] transition-all duration-200 animate-fade-in">
              {item.label}
            </span>
          </Link>
        ))}
      </nav>
    </ReduxProvider>
  );
}
