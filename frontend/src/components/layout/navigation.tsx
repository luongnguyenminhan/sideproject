'use client';

import React from 'react';
import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faComments, faQuestionCircle, faInfoCircle } from '@fortawesome/free-solid-svg-icons';
import type { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import type { UserResponse } from '@/types/auth.type';
import LoginModal from '@/components/auth/loginModal';
import { useTranslation } from '@/contexts/TranslationContext';
import { useLoginModal } from '@/hooks/useLoginModal';

interface NavigationItem {
  href: string;
  label: string;
  icon: IconDefinition;
  requiresAuth?: boolean;
}

interface NavigationProps {
  user: UserResponse | null;
  locale: string;
  chatLabel: string;
  aboutLabel: string;
  helpLabel: string;
  isMobile?: boolean;
}

export default function Navigation({ 
  user, 
  locale, 
  chatLabel, 
  aboutLabel, 
  helpLabel, 
  isMobile = false 
}: NavigationProps) {
  const { t } = useTranslation();
  const { isLoginModalOpen, openLoginModal, closeLoginModal } = useLoginModal();
  const isAuthenticated = !!user;

  const navigationItems: NavigationItem[] = [
    { href: `/${locale}/chat`, label: chatLabel, icon: faComments, requiresAuth: true },
    { href: `/${locale}/about`, label: aboutLabel, icon: faInfoCircle },
    { href: `/${locale}/help`, label: helpLabel, icon: faQuestionCircle },
  ];

  const handleItemClick = (item: NavigationItem, e: React.MouseEvent) => {
    if (item.requiresAuth && !isAuthenticated) {
      e.preventDefault();
      openLoginModal();
    }
  };

  const handleLoginSuccess = () => {
    closeLoginModal();
  };

  if (isMobile) {
    return (
      <>
        {navigationItems.map((item) => (
          <Link
            key={item.href}
            href={item.requiresAuth && !isAuthenticated ? '#' : item.href}
            onClick={(e) => handleItemClick(item, e)}
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

        <LoginModal
          isOpen={isLoginModalOpen}
          onClose={closeLoginModal}
          onSuccess={handleLoginSuccess}
          t={t}
        />
      </>
    );
  }

  return (
    <>
      {navigationItems.map((item) => (
        <Link
          key={item.href}
          href={item.requiresAuth && !isAuthenticated ? '#' : item.href}
          onClick={(e) => handleItemClick(item, e)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-[color:var(--foreground)] hover:bg-[color:var(--muted)] hover:text-[color:var(--primary)] transition-all duration-200"
        >
          <FontAwesomeIcon icon={item.icon} className="w-4 h-4" />
          <span className="hidden xl:inline">{item.label}</span>
        </Link>
      ))}

      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={closeLoginModal}
        onSuccess={handleLoginSuccess}
        t={t}
      />
    </>
  );
}
