'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPaperPlane, faKey, faRobot, faUser, faBars } from '@fortawesome/free-solid-svg-icons'

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

import type { ApiKeyResponse } from '@/types/chat.type'

interface ChatInterfaceProps {
  conversation: Conversation | null
  activeConversationId: string | null
  messages: Message[]
  isLoading: boolean
  isTyping: boolean
  error: string | null
  apiKeys: ApiKeyResponse[]
  apiKeyStatus: 'none' | 'loading' | 'valid' | 'invalid'
  onSendMessage: (content: string) => void
  onSaveApiKey: (provider: string, apiKey: string, isDefault?: boolean, keyName?: string) => void
  onDeleteApiKey: (keyId: string) => void
  onOpenMobileSidebar: () => void
  translations: {
    welcomeTitle: string
    welcomeDescription: string
    addApiKey: string
    enterApiKey: string
    apiKeySet: string
    resetApiKey: string
    noMessages: string
    startConversation: string
    typeMessage: string
    typing: string
    sending: string
    openMenu: string
  }
}

export function ChatInterface({ 
  conversation, 
  activeConversationId,
  messages,
  isLoading,
  isTyping,
  error,
  apiKeys,
  apiKeyStatus,
  onSendMessage,
  onSaveApiKey,
  onDeleteApiKey,
  onOpenMobileSidebar,
  translations 
}: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [apiKeyProvider, setApiKeyProvider] = useState('google')
  const [showApiKeyInput, setShowApiKeyInput] = useState(false)
  const [keyName, setKeyName] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    onSendMessage(input)
    setInput('')
  }

  const handleApiKeySubmit = async () => {
    if (apiKey.trim()) {
      await onSaveApiKey(apiKeyProvider, apiKey, true, keyName || undefined)
      setApiKey('')
      setKeyName('')
      setShowApiKeyInput(false)
    }
  }

  const handleApiKeyReset = () => {
    setApiKey('')
    setKeyName('')
    setShowApiKeyInput(false)
  }

  const handleDeleteApiKey = async (keyId: string) => {
    await onDeleteApiKey(keyId)
  }

  // Get display status for API key
  const getApiKeyDisplay = () => {
    const defaultKey = apiKeys.find(key => key.is_default)
    if (defaultKey) {
      return `${defaultKey.provider.toUpperCase()}: ${defaultKey.masked_key}`
    }
    return null
  }

  // Check if user can send messages
  const canSendMessage = () => {
    return apiKeyStatus === 'valid' && activeConversationId && !isLoading
  }

  if (!conversation && !activeConversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
        <Card className="p-8 text-center max-w-md mx-4 bg-[color:var(--card)] border border-[color:var(--border)] shadow-lg backdrop-blur-sm">
          <h2 className="text-2xl font-semibold mb-4 bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent">
            {translations.welcomeTitle}
          </h2>
          <p className="text-[color:var(--muted-foreground)]">
            {translations.welcomeDescription}
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
      {/* Chat Header */}
      <div className="border-b border-[color:var(--border)] bg-[color:var(--card)]/80 backdrop-blur-sm p-4">
        <div className="flex items-center justify-between">
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
              {conversation?.name || 'Chat'}
            </h2>
          </div>
          
          {/* API Key Section */}
          <div className="flex items-center gap-2">
            {/* API Key Status Display */}
            {apiKeyStatus === 'none' && !showApiKeyInput && (
              <Button
                onClick={() => setShowApiKeyInput(true)}
                size="sm"
                variant="outline"
                className="border-[color:var(--border)] hover:bg-[color:var(--accent)]"
              >
                <FontAwesomeIcon icon={faKey} className="mr-2" />
                {translations.addApiKey}
              </Button>
            )}
            
            {apiKeyStatus === 'loading' && (
              <div className="flex items-center gap-2">
                <span className="animate-spin">⟳</span>
                <span className="text-sm text-[color:var(--muted-foreground)]">Loading...</span>
              </div>
            )}
            
            {showApiKeyInput && (
              <div className="flex items-center gap-2">
                <select
                  value={apiKeyProvider}
                  onChange={(e) => setApiKeyProvider(e.target.value)}
                  className="px-2 py-1 text-xs bg-[color:var(--background)] border border-[color:var(--border)] rounded text-[color:var(--foreground)]"
                >
                  <option value="google">Google</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
                <input
                  type="text"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  placeholder="Key name (optional)"
                  className="px-2 py-1 text-xs bg-[color:var(--background)] border border-[color:var(--border)] rounded text-[color:var(--foreground)] w-24"
                />
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={translations.enterApiKey}
                  className="px-3 py-1 text-sm bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg text-[color:var(--foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleApiKeySubmit()
                    if (e.key === 'Escape') handleApiKeyReset()
                  }}
                />
                <Button onClick={handleApiKeySubmit} size="sm" disabled={apiKeyStatus === 'loading'}>
                  {apiKeyStatus === 'loading' ? '...' : 'Set'}
                </Button>
                <Button onClick={handleApiKeyReset} size="sm" variant="ghost">
                  ×
                </Button>
              </div>
            )}
            
            {apiKeyStatus === 'valid' && getApiKeyDisplay() && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-[color:var(--muted-foreground)] bg-green-100 dark:bg-green-900 px-2 py-1 rounded">
                  ✓ {getApiKeyDisplay()}
                </span>
                <Button
                  onClick={() => setShowApiKeyInput(true)}
                  size="sm"
                  variant="ghost"
                  className="text-xs"
                >
                  Change
                </Button>
              </div>
            )}
            
            {apiKeyStatus === 'invalid' && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-red-600 bg-red-100 dark:bg-red-900 px-2 py-1 rounded">
                  ⚠ Invalid API Key
                </span>
                <Button
                  onClick={() => setShowApiKeyInput(true)}
                  size="sm"
                  variant="outline"
                  className="border-red-300 text-red-600 hover:bg-red-50"
                >
                  Fix
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error && (
          <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {/* API Key Required Notice */}
        {apiKeyStatus !== 'valid' && activeConversationId && (
          <div className="bg-yellow-100 border border-yellow-300 text-yellow-800 px-4 py-3 rounded mb-4">
            <div className="flex items-center gap-2">
              <FontAwesomeIcon icon={faKey} />
              <span>Please set up your API key to start chatting</span>
              {!showApiKeyInput && (
                <Button
                  onClick={() => setShowApiKeyInput(true)}
                  size="sm"
                  variant="outline"
                  className="ml-2"
                >
                  Add API Key
                </Button>
              )}
            </div>
          </div>
        )}
        
        {messages.length === 0 ? (
          <div className="text-center text-[color:var(--muted-foreground)] mt-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center">
              <FontAwesomeIcon icon={faRobot} className="text-2xl" />
            </div>
            <p className="text-lg">{translations.noMessages}</p>
            <p className="text-sm">{translations.startConversation}</p>
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
                          {message.isStreaming && <span className="animate-pulse">|</span>}
                        </p>
                      </div>
                      <p className={`text-xs mt-2 ${
                        message.role === 'user' 
                          ? 'text-white/70' 
                          : 'text-[color:var(--muted-foreground)]'
                      }`}>
                        {message.timestamp.toLocaleTimeString()}
                        {message.model_used && ` • ${message.model_used}`}
                        {message.response_time_ms && ` • ${message.response_time_ms}ms`}
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <Card className="p-4 bg-[color:var(--card)] border-[color:var(--border)]">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center bg-[color:var(--primary)]/10">
                      <FontAwesomeIcon icon={faRobot} className="text-sm text-[color:var(--primary)]" />
                    </div>
                    <span className="text-sm text-[color:var(--muted-foreground)]">
                      {translations.typing}
                    </span>
                  </div>
                </Card>
              </div>
            )}
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-[color:var(--border)] bg-[color:var(--card)]/80 backdrop-blur-sm p-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-3 items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={canSendMessage() ? translations.typeMessage : 'Set up API key to start chatting'}
              disabled={!canSendMessage()}
              className="flex-1 px-4 py-3 bg-[color:var(--background)] border border-[color:var(--border)] rounded-xl text-[color:var(--foreground)] placeholder:text-[color:var(--muted-foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none transition-all duration-200 disabled:opacity-50"
            />
            <Button
              type="submit"
              disabled={!input.trim() || !canSendMessage()}
              className="px-6 py-3 bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:shadow-[var(--button-hover-shadow)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="animate-spin">⟳</span>
              ) : (
                <FontAwesomeIcon icon={faPaperPlane} />
              )}
            </Button>
          </form>
          {isLoading && (
            <div className="text-center mt-2 text-sm text-[color:var(--muted-foreground)]">
              {translations.sending}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
