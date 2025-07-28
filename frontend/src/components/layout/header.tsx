import authApi from '@/apis/authApi';
import FloatingChatBubble from '@/components/chat/FloatingChatBubble';
import ThemeSwapper from '@/components/global/themeSwapper';
import AuthHeader from '@/components/layout/authHeader';
import Navigation from '@/components/layout/navigation';
import { TranslationProvider } from '@/contexts/TranslationContext';
import { ReduxProvider } from '@/redux/provider';
import type { UserResponse } from '@/types/auth.type';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import { createTranslator, getDictionary } from '@/utils/translation';
import { cookies } from 'next/headers';
import Image from 'next/image';
import Link from 'next/link';

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

  return (
    <ReduxProvider>
      <header className='w-full px-8 md:px-6 py-2 flex items-center justify-between bg-gradient-to-r from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] shadow-lg dark:shadow-xl transition-all duration-500 min-h-0 h-14'>
        <div className='flex items-center gap-2'>
          <Link href={`/${locale}`} className='flex items-center gap-2'>
            <Image
              src='/assets/logo/logo_web.jpg'
              alt='App Logo'
              width={50}
              height={50}
              className='!m-4 rounded-full'
            />
            <span className='hidden md:inline text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]'>
              {t('common.branding')}
            </span>
          </Link>
        </div>

        {/* Navigation Menu (Desktop) */}
        <nav className='hidden lg:flex items-center gap-1'>
          <TranslationProvider dictionary={dictionary} locale={locale}>
            <Navigation
              user={user}
              locale={locale}
              chatLabel={t('navigation.chat')}
              aboutLabel={t('navigation.about')}
              helpLabel={t('navigation.help')}
              isMobile={false}
            />
          </TranslationProvider>
        </nav>

        <div className='flex items-center gap-2'>
          {/* Theme and Language Switchers moved here for compact header */}
          <div className='fixed min-h-0 bottom-25 lg:bottom-4 right-4 z-[9999] flex flex-col gap-2 items-end'>
            <ThemeSwapper />
            <TranslationProvider dictionary={dictionary} locale={locale}>
              {/* Show chat bubble only if withChatBubble and authenticated */}
              {withChatBubble && isAuthenticated && <FloatingChatBubble />}
            </TranslationProvider>
          </div>
          <TranslationProvider dictionary={dictionary} locale={locale}>
            <AuthHeader user={user} locale={locale} />
          </TranslationProvider>
        </div>
      </header>{' '}
      {/* Bottom Navigation for Mobile */}
      <nav className='flex lg:hidden fixed bottom-0 p-4 py-10 left-0 w-full z-50 bg-[color:var(--card)] border-t border-[color:var(--border)] shadow-t-md h-16 justify-around items-center'>
        <TranslationProvider dictionary={dictionary} locale={locale}>
          <Navigation
            user={user}
            locale={locale}
            chatLabel={t('navigation.chat')}
            aboutLabel={t('navigation.about')}
            helpLabel={t('navigation.help')}
            isMobile={true}
          />
        </TranslationProvider>
      </nav>
    </ReduxProvider>
  );
}
