/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { DotsTypingIndicator } from '@/components/ui/TypingIndicator'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPaperPlane, faRobot, faUser, faBars, faCopy, faCheck } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Image from 'next/image'

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
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const [copiedCodeBlocks, setCopiedCodeBlocks] = useState<Set<string>>(new Set())
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

  const handleCopyMessage = async (messageId: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedMessageId(messageId)
      setTimeout(() => setCopiedMessageId(null), 2000)
    } catch (err) {
      console.error('Failed to copy message:', err)
    }
  }

  const handleCopyCodeBlock = async (code: string, blockId: string) => {
    try {
      await navigator.clipboard.writeText(code)
      setCopiedCodeBlocks(prev => new Set(prev).add(blockId))
      setTimeout(() => {
        setCopiedCodeBlocks(prev => {
          const newSet = new Set(prev)
          newSet.delete(blockId)
          return newSet
        })
      }, 2000)
    } catch (err) {
      console.error('Failed to copy code block:', err)
    }
  }

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
              <div key={message.id} className="space-y-2">
                {message.role === 'user' ? (
                  <div className="flex justify-end">
                    <Card className="max-w-[80%] p-4 backdrop-blur-sm transition-all duration-300 hover:shadow-[var(--card-hover-shadow)] bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-[color:var(--primary-foreground)] border-[color:var(--primary)]">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white/20">
                          <FontAwesomeIcon 
                            icon={faUser} 
                            className="text-sm text-white" 
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
                  </div>                ) : (
                  <div className="space-y-2">
                    {/* Bot Avatar and Timestamp */}
                    <div className="flex items-center gap-3 px-2">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center bg-[color:var(--primary)]/10">
                        <FontAwesomeIcon 
                          icon={faRobot} 
                          className="text-sm text-[color:var(--primary)]" 
                        />
                      </div>
                      <span className="text-sm font-medium text-[color:var(--foreground)]">
                        Assistant
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
                              const { inline, className, children, ...rest } = props
                              const match = /language-(\w+)/.exec(className || '')
                              const codeContent = String(children).replace(/\n$/, '')
                              const blockId = `${message.id}-${Math.random().toString(36).substr(2, 9)}`
                              const language = match ? match[1] : 'text'
                              
                              return !inline && match ? (
                                // CODE BLOCK EXAMPLE 1: ChatGPT-style code block with header and actions
                                <div className="contain-inline-size rounded-md border-[0.5px] border-[color:var(--border)] relative bg-[color:var(--card)] my-4 w-full max-w-full overflow-hidden">
                                  {/* Header with language and actions */}
                                  <div className="flex items-center text-[color:var(--muted-foreground)] px-4 py-2 text-xs font-sans justify-between h-9 bg-[color:var(--card)] dark:bg-[color:var(--muted)] select-none rounded-t-[5px] border-b border-[color:var(--border)]">
                                    <span className="font-medium">{language}</span>
                                    <div className="flex items-center gap-1">
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleCopyCodeBlock(codeContent, blockId)}
                                        className="flex gap-1 items-center select-none px-3 py-1 h-auto text-xs hover:bg-[color:var(--accent)] transition-colors"
                                      >
                                        <FontAwesomeIcon 
                                          icon={copiedCodeBlocks.has(blockId) ? faCheck : faCopy} 
                                          className="w-3 h-3" 
                                        />
                                        {copiedCodeBlocks.has(blockId) ? 'Copied!' : 'Copy'}
                                      </Button>
                                    </div>
                                  </div>
                                  
                                  {/* Code content */}
                                  <div className="overflow-y-auto p-4" dir="ltr">
                                    <pre className="whitespace-pre overflow-x-auto">
                                      <code className={className} {...rest}>
                                        {codeContent}
                                      </code>
                                    </pre>
                                  </div>
                                </div>
                              ) : !inline ? (
                                // CODE BLOCK EXAMPLE 2: Simplified code block without language header
                                <div className="contain-inline-size rounded-md border border-[color:var(--border)] relative bg-[color:var(--muted)] my-4 w-full max-w-full overflow-hidden group">
                                  <div className="relative">
                                    <pre className="overflow-x-auto p-4">
                                      <code className={className} {...rest}>
                                        {codeContent}
                                      </code>
                                    </pre>
                                    
                                    {/* Floating copy button */}
                                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleCopyCodeBlock(codeContent, blockId)}
                                        className="text-xs bg-[color:var(--background)]/90 backdrop-blur-sm border border-[color:var(--border)] hover:bg-[color:var(--muted)] px-2 py-1 h-auto"
                                      >
                                        <FontAwesomeIcon 
                                          icon={copiedCodeBlocks.has(blockId) ? faCheck : faCopy} 
                                          className="w-3 h-3 mr-1" 
                                        />
                                        {copiedCodeBlocks.has(blockId) ? 'Copied!' : 'Copy'}
                                      </Button>
                                    </div>
                                  </div>
                                </div>
                              ) : (
                                // INLINE CODE EXAMPLE 1: Highlighted inline code
                                <code 
                                  className="bg-[color:var(--muted)] text-[color:var(--foreground)] px-1.5 py-0.5 rounded text-sm font-mono border border-[color:var(--border)]/50 shadow-sm" 
                                  {...rest}
                                >
                                  {children}
                                </code>
                              )
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
                          {message.content}
                        </ReactMarkdown>
                      </div>
                      
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
                          {copiedMessageId === message.id ? 'Copied!' : 'Copy'}
                        </Button>
                      </div>
                      
                      {/* Optional: Message metadata */}
                      {(message.model_used || message.response_time_ms) && (
                        <div className="text-xs text-[color:var(--muted-foreground)] flex gap-4">
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {isTyping && (
              <div className="space-y-2">
                <div className="flex items-center gap-3 px-2">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-[color:var(--primary)]/10 animate-pulse">
                    <FontAwesomeIcon 
                      icon={faRobot} 
                      className="text-sm text-[color:var(--primary)] animate-pulse" 
                    />
                  </div>
                  <span className="text-sm font-medium text-[color:var(--foreground)]">
                    Assistant
                  </span>
                </div>
                <div className="ml-11">
                  <div className="bg-[color:var(--card)]/50 border border-[color:var(--border)] rounded-lg p-4 backdrop-blur-sm animate-fadeIn">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-[color:var(--muted-foreground)]">
                        {t('chat.typing')}
                      </span>
                      <DotsTypingIndicator />
                    </div>
                  </div>
                </div>
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
