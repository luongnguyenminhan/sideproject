'use client';

import { useEffect } from 'react';
import { useTranslation } from '@/contexts/TranslationContext';
import { useSelector } from 'react-redux';
import { RootState } from '@/redux/store';
import { ChatHeader } from './chat-header';
import { ChatWelcome } from './chat-welcome';
import { MessagesContainer } from './messages-container';
import { MessageInput } from './message-input';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  model_used?: string;
  response_time_ms?: string;
  file_attachments?: string[];
}

interface Conversation {
  id: string;
  name: string;
  messages: Message[];
  lastActivity: Date;
  messageCount: number;
}

interface ChatInterfaceProps {
  conversation: Conversation | null;
  activeConversationId: string | null;
  messages: Message[];
  isLoading: boolean;
  isTyping: boolean;
  error: string | null;
  onSendMessage: (content: string) => void;
  onOpenMobileSidebar: () => void;
  isConversationSidebarCollapsed?: boolean;
  isFileSidebarCollapsed?: boolean;
  onToggleConversationSidebar?: () => void;
  onToggleFileSidebar?: () => void;
}

export function ChatInterface({ 
  conversation, 
  activeConversationId,
  messages,
  isLoading,
  isTyping,
  error,
  onSendMessage,
  onOpenMobileSidebar,
  isConversationSidebarCollapsed = false,
  isFileSidebarCollapsed = false,
  onToggleConversationSidebar,
  onToggleFileSidebar
}: ChatInterfaceProps) {
  const { t } = useTranslation();
  const { user } = useSelector((state: RootState) => state.auth);

  // Check if user can send messages - block when bot is responding
  const canSendMessage = (): boolean => {
    return Boolean(activeConversationId && !isLoading && !isTyping);
  };

  // Auto scroll when conversation changes
  useEffect(() => {
    if (activeConversationId) {
      // Small delay to ensure messages are rendered
      const timer = setTimeout(() => {
        // Scroll behavior is handled in MessagesContainer
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [activeConversationId]);

  // If no conversation is selected, show welcome screen
  if (!conversation && !activeConversationId) {
    return (
      <ChatWelcome 
        welcomeTitle={t('chat.welcomeTitle')}
        welcomeDescription={t('chat.welcomeDescription')}
      />
    );
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
      {/* Chat Header */}
      <ChatHeader 
        conversationName={conversation?.name}
        defaultTitle={t('chat.defaultChatTitle')}
        onOpenMobileSidebar={onOpenMobileSidebar}
        isConversationSidebarCollapsed={isConversationSidebarCollapsed}
        isFileSidebarCollapsed={isFileSidebarCollapsed}
        onToggleConversationSidebar={onToggleConversationSidebar}
        onToggleFileSidebar={onToggleFileSidebar}
      />

      {/* Messages Area */}
      <MessagesContainer 
        messages={messages}
        user={user || undefined}
        isTyping={isTyping}
        error={error}
        copyText={t('chat.copy')}
        copiedText={t('chat.copied')}
        typingText={t('chat.typing')}
        noMessagesText={t('chat.noMessages')}
        startConversationText={t('chat.startConversation')}
      />

      {/* Input Area */}
      <MessageInput 
        onSendMessage={onSendMessage}
        isLoading={isLoading}
        canSendMessage={canSendMessage()}
        placeholder={t('chat.typeMessage')}
      />
    </div>
  );
}
