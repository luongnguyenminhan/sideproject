'use client';

import { Button } from '@/components/ui/button';
import LoginModal from '@/components/auth/loginModal';
import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import type { UserResponse } from '@/types/auth.type';
import { logoutAction } from '@/actions/auth';
import { useRouter } from 'next/navigation';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faCog } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from '@/contexts/TranslationContext';
import { useAppDispatch, useAppSelector } from '@/redux/hooks';
import { setUser, logout as logoutUser } from '@/redux/slices/authSlice';

interface AuthHeaderProps {
  user: UserResponse | null;
  locale: string;
}

export default function AuthHeader({ user: serverUser, locale }: AuthHeaderProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const router = useRouter();

  // Sync server user data with Redux store after getMe call
  useEffect(() => {
    if (serverUser && (!user || user.id !== serverUser.id)) {
      dispatch(setUser({
        id: serverUser.id,
        email: serverUser.email,
        username: serverUser.username,
        name: serverUser.name || undefined,
        profile_picture: serverUser.profile_picture || undefined,
        confirmed: serverUser.confirmed,
        role_id: serverUser.role || undefined,
      }));
    } else if (!serverUser && isAuthenticated) {
      dispatch(logoutUser());
    }
  }, [serverUser, user, isAuthenticated, dispatch]);

  const handleLoginClick = () => {
    setIsLoginModalOpen(true);
  };

  const handleLoginModalClose = () => {
    setIsLoginModalOpen(false);
  };

  const handleLoginSuccess = () => {
    setIsLoginModalOpen(false);
    // Use router.refresh() to re-fetch server components instead of full page reload
    router.refresh();
  };

  const handleLogout = async () => {
    dispatch(logoutUser());
    await logoutAction();
    router.refresh();
  };

  // Use Redux user data if available, fallback to server user
  const currentUser = serverUser;

  if (currentUser) {
    return (
      <div className="relative group ml-2">
        <button
          type="button"
          className="flex items-center gap-2 bg-white/60 dark:bg-gray-800/60 px-2 py-1 rounded-xl shadow-md backdrop-blur-md transition-all duration-300 hover:bg-white/80 dark:hover:bg-gray-700/80 group cursor-pointer focus:outline-none min-h-0 h-8"
          tabIndex={0}
        >
          <Image
            src={currentUser.profile_picture || '/file.svg'}
            alt={currentUser.name || currentUser.username}
            width={24}
            height={24}
            className="rounded-full border border-[color:var(--gradient-text-from)] shadow-sm"
          />
          <div className="flex flex-col text-right">
            <span className="font-semibold text-gray-900 dark:text-white text-xs truncate max-w-[120px]">
              {currentUser.name || "Unnamed User"}
            </span>
            <span className="text-[10px] text-gray-500 dark:text-gray-300 truncate max-w-[120px]">
              {currentUser.email}
            </span>
          </div>
          <svg 
            className="ml-1 w-3 h-3 text-gray-400 group-hover:text-gray-600 transition-transform duration-200 group-hover:rotate-180 group-focus:rotate-180" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div className="absolute right-0 mt-1 min-w-[160px] bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-100 dark:border-gray-700 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 pointer-events-none group-hover:pointer-events-auto group-focus-within:pointer-events-auto transition-all duration-200 z-50">
          <Link
            href={`/${locale}/profile`}
            className="w-full flex items-center gap-2 px-3 py-2 text-left text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-t-lg transition-colors text-xs"
          >
            <FontAwesomeIcon icon={faUser} className="w-3 h-3" />
            {t('navigation.profile')}
          </Link>
          <Link
            href={`/${locale}/settings`}
            className="w-full flex items-center gap-2 px-3 py-2 text-left text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-xs"
          >
            <FontAwesomeIcon icon={faCog} className="w-3 h-3" />
            {t('navigation.settings')}
          </Link>
          <div className="border-t border-gray-100 dark:border-gray-700"></div>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-left text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-b-lg transition-colors text-xs"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2h4a2 2 0 012 2v1" />
            </svg>
            {t('auth.logout')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <Button 
        variant="default" 
        size="sm" 
        onClick={handleLoginClick}
        className="text-xs px-3 py-1 h-8 min-h-0 dark:bg-gray-800/60 bg-white/60 hover:bg-white/80 dark:hover:bg-gray-700/80 transition-colors duration-300 shadow-md backdrop-blur-md text-gray-900 dark:text-white"
      >
        {t('auth.login')}
      </Button>
      
      <LoginModal 
        isOpen={isLoginModalOpen}
        onClose={handleLoginModalClose}
        onSuccess={handleLoginSuccess}
        t={t}
      />
    </>
  );
}
