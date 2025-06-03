'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { DotsTypingIndicator } from '@/components/ui/TypingIndicator'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPaperPlane, faRobot, faUser, faBars } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
  model_used?: string
  response_time_ms?: string
  file_attachments?: string[]
}

interface Conversation {
  id: string
  name: string
  messages: Message[]
  lastActivity: Date
  messageCount: number
}

interface ChatInterfaceProps {
  conversation: Conversation | null
  activeConversationId: string | null
  messages: Message[]
  isLoading: boolean
  isTyping: boolean
  error: string | null
  onSendMessage: (content: string) => void
  onOpenMobileSidebar: () => void
}

export function ChatInterface({ 
  conversation, 
  activeConversationId,
  messages,
  isLoading,
  isTyping,
  error,
  onSendMessage,
  onOpenMobileSidebar
}: ChatInterfaceProps) {
  const { t } = useTranslation()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    onSendMessage(input)
    setInput('')
  }

  // Check if user can send messages
  const canSendMessage = () => {
    return activeConversationId && !isLoading
  }

  // Auto scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Auto scroll when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  // Auto scroll when conversation changes
  useEffect(() => {
    if (activeConversationId) {
      // Small delay to ensure messages are rendered
      setTimeout(scrollToBottom, 100)
    }
  }, [activeConversationId])

  if (!conversation && !activeConversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
        <Card className="p-8 text-center max-w-md mx-4 bg-[color:var(--card)] border border-[color:var(--border)] shadow-lg backdrop-blur-sm">
          <h2 className="text-2xl font-semibold mb-4 bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent">
            {t('chat.welcomeTitle')}
          </h2>
          <p className="text-[color:var(--muted-foreground)]">
            {t('chat.welcomeDescription')}
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
      {/* Chat Header */}
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
            {conversation?.name || t('chat.defaultChatTitle')}
          </h2>
        </div>
      </div>

      {/* Messages Area */}
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
          <div className="text-center text-[color:var(--muted-foreground)] mt-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center">
              <FontAwesomeIcon icon={faRobot} className="text-2xl" />
            </div>
            <p className="text-lg">{t('chat.noMessages')}</p>
            <p className="text-sm">{t('chat.startConversation')}</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <Card className={`max-w-[80%] p-4 backdrop-blur-sm transition-all duration-300 hover:shadow-[var(--card-hover-shadow)] ${
                  message.role === 'user' 
                    ? 'bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-[color:var(--primary-foreground)] border-[color:var(--primary)]' 
                    : 'bg-[color:var(--card)] border-[color:var(--border)] text-[color:var(--card-foreground)]'
                }`}>
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'user' 
                        ? 'bg-white/20' 
                        : 'bg-[color:var(--primary)]/10'
                    }`}>
                      <FontAwesomeIcon 
                        icon={message.role === 'user' ? faUser : faRobot} 
                        className={`text-sm ${
                          message.role === 'user' 
                            ? 'text-white' 
                            : 'text-[color:var(--primary)]'
                        }`} 
                      />
                    </div>
                    <div className="flex-1">
                      <div className={`prose prose-sm max-w-none ${
                        message.role === 'user' 
                          ? 'prose-invert' 
                          : 'prose-gray dark:prose-invert'
                      }`}>
                        <p className="mb-2 leading-relaxed whitespace-pre-wrap">
                          {message.content}
                          {message.isStreaming && (
                            <span className="inline-flex items-center ml-1">
                              <span className="w-1 h-4 bg-[color:var(--primary)] animate-pulse"></span>
                            </span>
                          )}
                        </p>
                      </div>
                      <p className={`text-xs mt-2 ${
                        message.role === 'user' 
                          ? 'text-white/70' 
                          : 'text-[color:var(--muted-foreground)]'
                      }`}>
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <Card className="p-4 bg-[color:var(--card)] border-[color:var(--border)] backdrop-blur-sm animate-fadeIn">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center bg-[color:var(--primary)]/10 animate-pulse">
                      <FontAwesomeIcon 
                        icon={faRobot} 
                        className="text-sm text-[color:var(--primary)] animate-pulse" 
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-[color:var(--muted-foreground)]">
                        {t('chat.typing')}
                      </span>
                      <DotsTypingIndicator />
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </>
        )}
        
        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-[color:var(--border)] bg-[color:var(--card)]/80 backdrop-blur-sm p-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-3 items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t('chat.typeMessage')}
              disabled={!canSendMessage()}
              className="flex-1 px-4 py-3 bg-[color:var(--background)] border border-[color:var(--border)] rounded-xl text-[color:var(--foreground)] placeholder:text-[color:var(--muted-foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none transition-all duration-200 disabled:opacity-50"
            />
            <Button
              type="submit"
              disabled={!input.trim() || !canSendMessage()}
              className="px-6 py-3 bg-gradient-to-r text-white from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:shadow-[var(--button-hover-shadow)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              ) : (
                <FontAwesomeIcon icon={faPaperPlane} />
              )}
            </Button>
          </form>
          {isLoading && (
            <div className="flex items-center justify-center mt-2 text-sm text-[color:var(--muted-foreground)]">
              <DotsTypingIndicator text={t('chat.sending')} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
