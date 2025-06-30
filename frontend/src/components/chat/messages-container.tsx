'use client';

import { useEffect, useRef } from 'react';
import { ChatMessage } from './chat-message';
import { TypingIndicator } from './typing-indicator';
import { EmptyChatState } from './empty-chat-state';

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

interface User {
  profile_picture?: string;
  name?: string;
  username?: string;
}

interface MessagesContainerProps {
  messages: Message[];
  user?: User;
  isTyping: boolean;
  error: string | null;
  // Translation strings
  copyText: string;
  copiedText: string;
  typingText: string;
  noMessagesText: string;
  startConversationText: string;
  // Survey props
  globalSurveyData?: boolean; // Global survey state (for overall context)
  onToggleSurvey?: () => void;
  onOpenSurvey?: () => void;
}

export function MessagesContainer({
  messages,
  user,
  isTyping,
  error,
  copyText,
  copiedText,
  typingText,
  noMessagesText,
  startConversationText,
  // globalSurveyData = false, // Not used currently
  onToggleSurvey,
  onOpenSurvey
}: MessagesContainerProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Auto scroll when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div 
      ref={messagesContainerRef}
      className="flex-1 overflow-y-auto p-4 space-y-4"
    >
      {error && (
        <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {messages.length === 0 ? (
        <EmptyChatState 
          noMessagesText={noMessagesText}
          startConversationText={startConversationText}
        />
      ) : (
        <>
          {messages.map((message) => (
            <div key={message.id} className="space-y-2">
              <ChatMessage 
                message={message}
                user={user}
                copyText={copyText}
                copiedText={copiedText}
                // Check each message individually for survey tokens
                hasSurveyData={message.role === 'assistant' && message.content.includes('<survey>')}
                onToggleSurvey={onToggleSurvey}
                onOpenSurvey={onOpenSurvey}
              />
            </div>
          ))}
          {isTyping && (
            <TypingIndicator typingText={typingText} />
          )}
        </>
      )}
      
      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  );
}
