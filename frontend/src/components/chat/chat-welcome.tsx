'use client';

import { Card } from '@/components/ui/card';

interface ChatWelcomeProps {
  welcomeTitle: string;
  welcomeDescription: string;
}

export function ChatWelcome({ welcomeTitle, welcomeDescription }: ChatWelcomeProps) {
  return (
    <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
      <Card className="p-8 text-center max-w-md mx-4 bg-[color:var(--card)] border border-[color:var(--border)] shadow-lg backdrop-blur-sm">
        <h2 className="text-2xl font-semibold mb-4 bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent">
          {welcomeTitle}
        </h2>
        <p className="text-[color:var(--muted-foreground)]">
          {welcomeDescription}
        </p>
      </Card>
    </div>
  );
}
