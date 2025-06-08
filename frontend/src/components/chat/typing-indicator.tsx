'use client';

import { DotsTypingIndicator } from '@/components/ui/TypingIndicator';
import Image from 'next/image';
import { useTranslation } from '@/contexts/TranslationContext';

interface TypingIndicatorProps {
  typingText: string;
}

export function TypingIndicator({ typingText }: TypingIndicatorProps) {
  const { t } = useTranslation();
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3 px-2">
        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-[color:var(--primary)]/10 animate-pulse overflow-hidden">
          <Image
            src="/assets/logo/logo_web.png"
            alt="Assistant Logo"
            width={24}
            height={24}
            className="w-6 h-6 object-contain animate-pulse"
          />
        </div>
        <span className="text-sm font-medium text-[color:var(--foreground)]">
          {t('chat.assistant')}
        </span>
      </div>
      <div className="ml-11">
        <div className="bg-[color:var(--card)]/50 border border-[color:var(--border)] rounded-lg p-4 backdrop-blur-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <span className="text-sm text-[color:var(--muted-foreground)]">
              {typingText}
            </span>
            <DotsTypingIndicator />
          </div>
        </div>
      </div>
    </div>
  );
}
