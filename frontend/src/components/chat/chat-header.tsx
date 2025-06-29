'use client';

import { Button } from '@/components/ui/button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars, faComments, faFile, faClipboardList } from '@fortawesome/free-solid-svg-icons';

interface ChatHeaderProps {
  conversationName?: string;
  defaultTitle: string;
  onOpenMobileSidebar: () => void;
  isConversationSidebarCollapsed?: boolean;
  isFileSidebarCollapsed?: boolean;
  onToggleConversationSidebar?: () => void;
  onToggleFileSidebar?: () => void;
  onToggleSurvey?: () => void;
  hasSurveyData?: boolean;
  isSurveyOpen?: boolean;
}

export function ChatHeader({
  conversationName,
  defaultTitle,
  onOpenMobileSidebar,
  isConversationSidebarCollapsed = false,
  isFileSidebarCollapsed = false,
  onToggleConversationSidebar,
  onToggleFileSidebar,
  onToggleSurvey,
  hasSurveyData = false,
  isSurveyOpen = false
}: ChatHeaderProps) {
  return (
    <div className="border-b border-[color:var(--border)] bg-[color:var(--card)]/80 backdrop-blur-sm p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Mobile menu button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={onOpenMobileSidebar}
            className="md:hidden hover:bg-[color:var(--accent)] transition-all duration-200"
          >
            <FontAwesomeIcon icon={faBars} />
          </Button>

          {/* Desktop sidebar indicators when collapsed */}
          <div className="hidden md:flex items-center gap-2">
            {isConversationSidebarCollapsed && onToggleConversationSidebar && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleConversationSidebar}
                className="h-8 w-8 p-0 hover:bg-[color:var(--accent)] transition-all duration-200 group"
                title="Expand conversations sidebar"
              >
                <FontAwesomeIcon 
                  icon={faComments} 
                  className="text-sm text-[color:var(--muted-foreground)] group-hover:text-[color:var(--foreground)] group-hover:scale-110 transition-all duration-200" 
                />
              </Button>
            )}
          </div>

          {/* Survey button - Show when there's survey data */}
          {hasSurveyData && onToggleSurvey && (
            <Button
              variant={isSurveyOpen ? "default" : "outline"}
              size="sm"
              onClick={onToggleSurvey}
              className={`h-8 px-3 transition-all duration-200 group relative ${
                isSurveyOpen 
                  ? 'bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white shadow-lg border-0' 
                  : 'hover:bg-[color:var(--accent)] border-[color:var(--feature-blue)] text-[color:var(--feature-blue)] hover:text-[color:var(--foreground)]'
              }`}
              title={isSurveyOpen ? "Close survey" : "Open survey"}
            >
              <FontAwesomeIcon 
                icon={faClipboardList} 
                className={`text-sm transition-all duration-200 mr-2 ${
                  isSurveyOpen 
                    ? 'text-white' 
                    : 'text-[color:var(--feature-blue)] group-hover:text-[color:var(--foreground)] group-hover:scale-110'
                }`}
              />
              <span className="hidden sm:inline text-sm font-medium">
                {isSurveyOpen ? 'Close Survey' : 'Open Survey'}
              </span>
              {/* Indicator for new/available survey */}
              {!isSurveyOpen && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-[color:var(--feature-green)] rounded-full animate-pulse border-2 border-[color:var(--background)]">
                  <div className="absolute inset-0 w-3 h-3 bg-[color:var(--feature-green)] rounded-full animate-ping opacity-75"></div>
                </div>
              )}
            </Button>
          )}

          <h2 className="text-xl font-semibold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent">
            {conversationName || defaultTitle}
          </h2>
        </div>

        {/* Right side indicators */}
        <div className="hidden lg:flex items-center gap-2">
          {isFileSidebarCollapsed && onToggleFileSidebar && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleFileSidebar}
              className="h-8 w-8 p-0 hover:bg-[color:var(--accent)] transition-all duration-200 group"
              title="Expand files sidebar"
            >
              <FontAwesomeIcon 
                icon={faFile} 
                className="text-sm text-[color:var(--muted-foreground)] group-hover:text-[color:var(--foreground)] group-hover:scale-110 transition-all duration-200" 
              />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
