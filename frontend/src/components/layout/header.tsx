import { getDictionary, createTranslator } from '@/utils/translation';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import type { UserResponse } from '@/types/auth.type';
import Image from 'next/image';
import React from 'react';
import { cookies } from 'next/headers';
import authApi from '@/apis/authApi';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { redirect } from 'next/navigation';
import ThemeSwapper from '@/components/global/themeSwapper';

// getMeServer is correct as:
async function getMeServer(): Promise<UserResponse | null> {
  const cookieStore = await cookies(); // synchronous
  const accessToken = cookieStore.get('access_token')?.value;
  if (!accessToken) return null;
  return await authApi.getMe({ Authorization: `Bearer ${accessToken}` });
}

// Server action to clear the access_token cookie and redirect
async function logoutAction() {
  'use server';
  // Remove the cookie (server-side)
  const cookieStore = await cookies();
  cookieStore.set('access_token', '', { path: '/', maxAge: -1 });
  redirect('/auth');
}

export default async function Header() {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);
  const user = await getMeServer();

  return (
    <header className="w-full px-8 md:px-6 py-2 flex items-center justify-between bg-gradient-to-r from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] shadow-lg dark:shadow-xl transition-all duration-500 min-h-0 h-14">
      <div className="flex items-center gap-2">
        <Image
          src="/Logo CLB 2023.png"
          alt="App Logo"
          width={80}
          height={30}
          className="!m-4"
        />
        <span className="hidden md:inline text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]">
          {t('common.branding')}
        </span>
      </div>
      <div className="flex items-center gap-2">
        {/* Theme and Language Switchers moved here for compact header */}
        <div className="flex items-center gap-2">
          <ThemeSwapper />
        </div>
        {user ? (
          <div className="relative group ml-2">
            <button
              type="button"
              className="flex items-center gap-2 bg-white/60 dark:bg-gray-800/60 px-2 py-1 rounded-xl shadow-md backdrop-blur-md transition-all duration-300 hover:bg-white/80 dark:hover:bg-gray-700/80 group cursor-pointer focus:outline-none min-h-0 h-8"
              tabIndex={0}
            >
              <Image
                src={user.profile_picture || '/file.svg'}
                alt={user.name || user.username}
                width={24}
                height={24}
                className="rounded-full border border-[color:var(--gradient-text-from)] shadow-sm"
              />
              <div className="flex flex-col text-right">
                <span className="font-semibold text-gray-900 dark:text-white text-xs truncate max-w-[120px]">{user.name || "Unnamed User"}</span>
                <span className="text-[10px] text-gray-500 dark:text-gray-300 truncate max-w-[120px]">{user.email}</span>
              </div>
              <svg className="ml-1 w-3 h-3 text-gray-400 group-hover:text-gray-600 transition-transform duration-200 group-hover:rotate-180 group-focus:rotate-180" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
            </button>
            <div className="absolute right-0 mt-1 min-w-[120px] bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-100 dark:border-gray-700 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 pointer-events-none group-hover:pointer-events-auto group-focus-within:pointer-events-auto transition-all duration-200 z-50">
              <form action={logoutAction}>
                <button
                  type="submit"
                  className="w-full flex items-center gap-2 px-3 py-2 text-left text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors text-xs"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2h4a2 2 0 012 2v1" /></svg>
                  {t('auth.logout')}
                </button>
              </form>
            </div>
          </div>
        ) : (
          <Link href="/auth">
            <Button variant="default" size="sm" className="text-xs px-3 py-1 h-8 min-h-0 dark:bg-gray-800/60 bg-white/60 hover:bg-white/80 dark:hover:bg-gray-700/80 transition-colors duration-300 shadow-md backdrop-blur-md text-gray-900 dark:text-white">
              {t('auth.login')}
            </Button>
          </Link>
        )}
      </div>
    </header>
  );
}
