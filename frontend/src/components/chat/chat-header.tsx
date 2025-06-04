'use client';

import { Button } from '@/components/ui/button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars } from '@fortawesome/free-solid-svg-icons';

interface ChatHeaderProps {
  conversationName?: string;
  defaultTitle: string;
  onOpenMobileSidebar: () => void;
}

export function ChatHeader({
  conversationName,
  defaultTitle,
  onOpenMobileSidebar
}: ChatHeaderProps) {
  return (
    <div className="border-b border-[color:var(--border)] bg-[color:var(--card)]/80 backdrop-blur-sm p-4">
      <div className="flex items-center gap-3">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onOpenMobileSidebar}
          className="md:hidden"
        >
          <FontAwesomeIcon icon={faBars} />
        </Button>
        <h2 className="text-xl font-semibold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent">
          {conversationName || defaultTitle}
        </h2>
      </div>
    </div>
  );
}
