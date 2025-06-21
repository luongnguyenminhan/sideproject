'use client';

import { useState } from 'react';

export function useLoginModal() {
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  const openLoginModal = () => setIsLoginModalOpen(true);
  const closeLoginModal = () => setIsLoginModalOpen(false);

  return {
    isLoginModalOpen,
    openLoginModal,
    closeLoginModal,
  };
}
