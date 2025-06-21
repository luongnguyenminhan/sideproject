'use client';

import React from 'react';
import Link from 'next/link';
import { MagnetButton } from '@/components/animations';
import LoginModal from '@/components/auth/loginModal';
import { useTranslation } from '@/contexts/TranslationContext';
import { useLoginModal } from '@/hooks/useLoginModal';

interface HeroButtonsProps {
  isAuthenticated: boolean;
  getStartedText: string;
  learnMoreText: string;
  locale: string;
}

export default function HeroButtons({
  isAuthenticated,
  getStartedText,
  learnMoreText,
  locale
}: HeroButtonsProps) {
  const { t } = useTranslation();
  const { isLoginModalOpen, openLoginModal, closeLoginModal } = useLoginModal();

  const handleGetStartedClick = (e: React.MouseEvent) => {
    if (!isAuthenticated) {
      e.preventDefault();
      openLoginModal();
    }
  };

  const handleLoginSuccess = () => {
    closeLoginModal();
  };

  return (
    <>
      <div className="flex flex-col sm:flex-row gap-8 justify-center mt-16">
        <MagnetButton magnetStrength={0.8}>
          <div className="group relative">
            <div className="absolute inset-0 bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] rounded-xl blur-lg opacity-75 group-hover:opacity-100 transition-opacity duration-300"></div>
            <Link 
              href={isAuthenticated ? `/${locale}/chat` : '#'}
              onClick={handleGetStartedClick}
              className="relative px-12 py-4 text-lg text-[color:var(--primary-foreground)] font-semibold rounded-xl transition-all duration-300 shadow-lg hover:shadow-[var(--button-hover-shadow)] transform hover:-translate-y-2 bg-gradient-to-br from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:from-blue-700 hover:to-blue-900 border border-white/20 inline-block"
            >
              {getStartedText}
            </Link>
          </div>
        </MagnetButton>
        
        <MagnetButton magnetStrength={0.5}>
          <div className="group relative">
            <div className="absolute inset-0 bg-[color:var(--card)] rounded-xl blur-sm opacity-50 group-hover:opacity-75 transition-opacity duration-300"></div>
            <button className="relative px-12 py-4 text-lg bg-[color:var(--card)] hover:bg-[color:var(--muted)] text-[color:var(--card-foreground)] font-semibold rounded-xl border-2 border-[color:var(--border)] transition-all duration-300 hover:border-[color:var(--ring)] transform hover:-translate-y-2 backdrop-blur-sm">
              {learnMoreText}
            </button>
          </div>
        </MagnetButton>
      </div>

      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={closeLoginModal}
        onSuccess={handleLoginSuccess}
        t={t}
      />
    </>
  );
}
