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
    <header className="w-full px-0 md:px-8 py-4 flex items-center justify-between bg-gradient-to-r from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] shadow-lg dark:shadow-xl transition-all duration-500">
      <div className="flex items-center gap-3">
        <Image
          src="/file.svg"
          alt="App Logo"
          width={40}
          height={40}
          className="rounded-xl shadow-md animate-pulse"
        />
        <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]">
          {t('common.branding')}
        </span>
      </div>
      {user ? (
        <div className="relative group">
          <button
            type="button"
            className="flex items-center gap-3 bg-white/60 dark:bg-gray-800/60 px-4 py-2 rounded-2xl shadow-md backdrop-blur-md transition-all duration-300 hover:bg-white/80 dark:hover:bg-gray-700/80 group cursor-pointer focus:outline-none"
            tabIndex={0}
          >
            <Image
              src={user.profile_picture || '/file.svg'}
              alt={user.name || user.username}
              width={36}
              height={36}
              className="rounded-full border-2 border-[color:var(--gradient-text-from)] shadow-sm"
            />
            <div className="flex flex-col text-right">
              <span className="font-semibold text-gray-900 dark:text-white text-base truncate max-w-[200px]">{user.name || user.username}</span>
              <span className="text-xs text-gray-500 dark:text-gray-300 truncate max-w-[200px]">{user.email}</span>
            </div>
            <svg className="ml-2 w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-transform duration-200 group-hover:rotate-180 group-focus:rotate-180" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <div className="absolute right-0 mt-2 min-w-[160px] bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 pointer-events-none group-hover:pointer-events-auto group-focus-within:pointer-events-auto transition-all duration-200 z-50">
            <form action={logoutAction}>
              <button
                type="submit"
                className="w-full flex items-center gap-2 px-4 py-3 text-left text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-xl transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2h4a2 2 0 012 2v1" /></svg>
                {t('auth.logout', { default: 'Logout' })}
              </button>
            </form>
          </div>
        </div>
      ) : (
        <Link href="/auth">
          <Button variant="default" size="lg">
            {t('auth.login', { default: 'Login' })}
          </Button>
        </Link>
      )}
    </header>
  );
}
