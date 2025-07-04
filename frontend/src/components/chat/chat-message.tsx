/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faCopy, faCheck } from '@fortawesome/free-solid-svg-icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Image from 'next/image';
import { MessageCodeBlock } from './message-code-block';
import { useTranslation } from '@/contexts/TranslationContext';
import { processMessageText } from '@/utils/text-processing';
import { useSurveyQuestions } from '@/hooks/useSurveyQuestions';

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

interface ChatMessageProps {
  message: Message;
  user?: User;
  copyText: string;
  copiedText: string;
  hasSurveyData?: boolean;
  onToggleSurvey?: () => void;
  onOpenSurvey?: () => void;
}

export function ChatMessage({ 
  message, 
  user, 
  copyText, 
  copiedText, 
  hasSurveyData = false, 
  onToggleSurvey,
  onOpenSurvey
}: ChatMessageProps) {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const { t } = useTranslation();
  const { loading, error, fetchQuestions } = useSurveyQuestions();

  // Check for survey token in message
  const surveyTokenMatch = message.content.match(/<survey>([^<]+)<\/survey>/)
  const hasSurveyToken = !!surveyTokenMatch
  const surveySessionId = surveyTokenMatch ? surveyTokenMatch[1] : null
  const shouldShowSurveyButton = message.role === 'assistant' && (hasSurveyData || hasSurveyToken) && (onToggleSurvey || onOpenSurvey)
  
  // Enhanced debug logging
  if (message.role === 'assistant') {
    console.log('[ChatMessage] Assistant message analysis:', {
      messageId: message.id,
      hasSurveyData,
      hasSurveyToken,
      surveySessionId,
      shouldShowSurveyButton,
      hasToggleFunction: !!onToggleSurvey,
      hasOpenFunction: !!onOpenSurvey,
      contentSnippet: message.content.substring(0, 100) + '...',
      surveyTokenPosition: message.content.indexOf('<survey>'),
      messageTimestamp: message.timestamp
    })
  }
  const handleCopyMessage = async (messageId: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <Card className="max-w-[80%] p-4 backdrop-blur-sm transition-all duration-300 hover:shadow-[var(--card-hover-shadow)] bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-[color:var(--primary-foreground)] border-[color:var(--primary)]">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white/20 overflow-hidden">
              {user?.profile_picture ? (
                <Image
                  src={user.profile_picture}
                  alt="User Avatar"
                  width={32}
                  height={32}
                  className="w-8 h-8 object-cover rounded-full"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const fallback = target.parentElement?.querySelector('.fallback-icon');
                    if (fallback) {
                      (fallback as HTMLElement).style.display = 'flex';
                    }
                  }}
                />
              ) : null}
              <FontAwesomeIcon 
                icon={faUser} 
                className={`text-sm text-white ${user?.profile_picture ? 'fallback-icon hidden' : ''}`}
                style={{ display: user?.profile_picture ? 'none' : 'block' }}
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="mb-2 leading-relaxed whitespace-pre-wrap break-words">
                {message.content}
              </p>
              <p className="text-xs mt-2 text-white/70">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="space-y-2">
      {/* Bot Avatar and Timestamp */}
      <div className="flex items-center gap-3 px-2">
        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-[color:var(--primary)]/10 overflow-hidden">
          <Image
            src="/assets/logo/logo_web.jpg"
            alt="Assistant Logo"
            width={24}
            height={24}
            className="w-6 h-6 object-contain"
          />
        </div>
        <span className="text-sm font-medium text-[color:var(--foreground)]">
            {t('chat.assistant')}
        </span>
        <span className="text-xs text-[color:var(--muted-foreground)]">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
      
      {/* Bot Message Content - Enhanced responsive markdown */}
      <div className="ml-11 space-y-3">
        <div className="prose prose-sm max-w-none prose-gray dark:prose-invert">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code: (props: any) => {
                const { inline, className, children, ...rest } = props;
                const match = /language-(\w+)/.exec(className || '');
                const codeContent = String(children).replace(/\n$/, '');
                const language = match ? match[1] : 'text';
                
                // Handle inline code with simple styling
                if (inline) {
                  return (
                    <code 
                      className="bg-[color:var(--muted)] text-[color:var(--foreground)] px-1.5 py-0.5 rounded text-sm font-mono border border-[color:var(--border)]/50 shadow-sm" 
                      {...rest}
                    >
                      {children}
                    </code>
                  );
                }
                
                // Handle block code with MessageCodeBlock
                return (
                  <MessageCodeBlock
                    code={codeContent}
                    language={language}
                    variant={match ? 'header' : 'floating'}
                  />
                );
              },
              img: (props: any) => (
                <div className="my-4">
                  <Image
                    {...props}
                    alt={props.alt || 'Image'}
                    className="max-w-full h-auto rounded-lg border border-[color:var(--border)] shadow-sm hover:shadow-md transition-shadow duration-200"
                    style={{ maxHeight: '500px', objectFit: 'contain' }}
                    width={props.width || 600}
                    height={props.height || 400}
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                  {props.alt && (
                    <p className="text-sm text-[color:var(--muted-foreground)] mt-2 italic text-center">
                      {props.alt}
                    </p>
                  )}
                </div>
              ),
              blockquote: (props: any) => (
                <blockquote className="border-l-4 border-[color:var(--primary)] bg-[color:var(--muted)]/30 p-4 my-4 rounded-r-lg">
                  <div className="text-[color:var(--muted-foreground)] text-sm mb-2 font-medium">
                    System Prompt
                  </div>
                  <div className="text-[color:var(--foreground)] italic">
                    {props.children}
                  </div>
                </blockquote>
              ),
              h1: (props: any) => (
                <h1 className="text-2xl font-bold mb-4 text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </h1>
              ),
              h2: (props: any) => (
                <h2 className="text-xl font-semibold mb-3 text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </h2>
              ),
              h3: (props: any) => (
                <h3 className="text-lg font-medium mb-2 text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </h3>
              ),
              ul: (props: any) => (
                <ul className="list-disc pl-6 mb-4 text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </ul>
              ),
              ol: (props: any) => (
                <ol className="list-decimal pl-6 mb-4 text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </ol>
              ),
              li: (props: any) => (
                <li className="mb-1 text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </li>
              ),
              p: (props: any) => (
                <p className="mb-3 leading-relaxed text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </p>
              ),
              a: (props: any) => (
                <a 
                  href={props.href} 
                  className="text-[color:var(--primary)] hover:underline" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  {...props}
                >
                  {props.children}
                </a>
              ),
              table: (props: any) => (
                <div className="overflow-x-auto mb-4">
                  <table className="min-w-full border border-[color:var(--border)] rounded-lg" {...props}>
                    {props.children}
                  </table>
                </div>
              ),
              th: (props: any) => (
                <th className="border border-[color:var(--border)] px-3 py-2 bg-[color:var(--muted)] font-medium text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </th>
              ),
              td: (props: any) => (
                <td className="border border-[color:var(--border)] px-3 py-2 text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </td>
              ),
              strong: (props: any) => (
                <strong className="font-semibold text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </strong>
              ),
              em: (props: any) => (
                <em className="italic text-[color:var(--foreground)]" {...props}>
                  {props.children}
                </em>
              )
            }}
          >
            {processMessageText(message.content.replace(/<survey>[^<]+<\/survey>/g, ''))}
          </ReactMarkdown>
        </div>
        
        
        {/* Survey Button - Show if this is an assistant message with special survey token or has survey data */}
        {shouldShowSurveyButton && (
          <div className="mb-3">
            <button
              onClick={async (e) => {
                e.preventDefault()
                e.stopPropagation()
                console.log('[ChatMessage] Survey button clicked:', { 
                  hasSurveyData, 
                  hasToggle: !!onToggleSurvey, 
                  hasOpen: !!onOpenSurvey,
                  hasSurveyToken,
                  surveySessionId
                })
                
                // If we have a session ID from the token, set it first then open survey
                if (surveySessionId) {
                  console.log('[ChatMessage] Setting session ID and opening survey:', surveySessionId)
                  
                  // Store session ID FIRST for the survey component to pick up
                  window.sessionStorage.setItem('current_survey_session_id', surveySessionId)
                  
                  // Then open survey - SurveyPanelWrapper will fetch questions automatically
                  if (onOpenSurvey) {
                    onOpenSurvey()
                  }
                  
                  // Optional: Pre-fetch questions in background for better UX
                  try {
                    await fetchQuestions(surveySessionId)
                    console.log('[ChatMessage] Background fetch completed successfully')
                  } catch (err) {
                    console.error('[ChatMessage] Background fetch failed (not critical):', err)
                  }
                } else if (onOpenSurvey) {
                  console.log('[ChatMessage] Calling onOpenSurvey')
                  onOpenSurvey()
                } else if (onToggleSurvey) {
                  console.log('[ChatMessage] Calling onToggleSurvey')
                  onToggleSurvey()
                }
              }}
              disabled={loading}
              className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 shadow-sm hover:shadow-md active:scale-95 transform ${
                loading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700'
              }`}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              )}
              {loading ? 'Loading...' : (t('survey.openSurvey') || 'Open Survey')}
            </button>
            
            {/* Error message */}
            {error && (
              <div className="mt-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-2">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Copy Button */}
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleCopyMessage(message.id, message.content)}
            className="text-xs text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)] transition-colors"
          >
            <FontAwesomeIcon 
              icon={copiedMessageId === message.id ? faCheck : faCopy} 
              className="mr-1" 
            />
            {copiedMessageId === message.id ? copiedText : copyText}
          </Button>
        </div>
        
        {/* Optional: Message metadata */}
        {(message.model_used || message.response_time_ms) && (
          <div className="text-xs text-[color:var(--muted-foreground)] flex gap-4">
            {/* Add metadata display here if needed */}
          </div>
        )}
      </div>
    </div>
  );
}
