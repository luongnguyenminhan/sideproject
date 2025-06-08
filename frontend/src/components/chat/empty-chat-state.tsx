'use client';

import Image from 'next/image';

interface EmptyChatStateProps {
  noMessagesText: string;
  startConversationText: string;
}

export function EmptyChatState({ noMessagesText, startConversationText }: EmptyChatStateProps) {
  return (
    <div className="text-center text-[color:var(--muted-foreground)] mt-8">
      <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center overflow-hidden">
        <Image
          src="/assets/logo/logo_web.png"
          alt="Logo"
          width={48}
          height={48}
          className="w-12 h-12 object-contain"
        />
      </div>
      <p className="text-lg">{noMessagesText}</p>
      <p className="text-sm">{startConversationText}</p>
    </div>
  );
}
