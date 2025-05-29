'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPaperPlane, faKey, faRobot, faUser } from '@fortawesome/free-solid-svg-icons'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface Conversation {
  id: string
  name: string
  messages: Message[]
  lastActivity: Date
}

interface ChatInterfaceProps {
  conversation?: Conversation
  onSendMessage: (content: string) => void
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
  }
}

export function ChatInterface({ conversation, onSendMessage, translations }: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [isApiKeySet, setIsApiKeySet] = useState(false)
  const [showApiKeyInput, setShowApiKeyInput] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    onSendMessage(input)
    setInput('')
  }

  const handleApiKeySubmit = () => {
    if (apiKey.trim()) {
      setIsApiKeySet(true)
      setShowApiKeyInput(false)
      // Here you would typically store the API key securely or send it to your backend
      console.log('API Key submitted:', apiKey)
    }
  }

  const handleApiKeyReset = () => {
    setApiKey('')
    setIsApiKeySet(false)
    setShowApiKeyInput(false)
  }

  if (!conversation) {
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
          <h2 className="text-xl font-semibold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent">
            {conversation.name}
          </h2>
          
          {/* API Key Section */}
          <div className="flex items-center gap-2">
            {!isApiKeySet && !showApiKeyInput && (
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
            
            {showApiKeyInput && !isApiKeySet && (
              <div className="flex items-center gap-2">
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={translations.enterApiKey}
                  className="px-3 py-1 text-sm bg-[color:var(--background)] border border-[color:var(--border)] rounded-lg text-[color:var(--foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleApiKeySubmit()
                  }}
                />
                <Button onClick={handleApiKeySubmit} size="sm">
                  Set
                </Button>
              </div>
            )}
            
            {isApiKeySet && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-[color:var(--muted-foreground)]">
                  {translations.apiKeySet}
                </span>
                <Button
                  onClick={handleApiKeyReset}
                  size="sm"
                  variant="outline"
                  className="border-[color:var(--border)] hover:bg-[color:var(--accent)]"
                >
                  {translations.resetApiKey}
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {conversation.messages.length === 0 ? (
          <div className="text-center text-[color:var(--muted-foreground)] mt-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center">
              <FontAwesomeIcon icon={faRobot} className="text-2xl" />
            </div>
            <p className="text-lg">{translations.noMessages}</p>
            <p className="text-sm">{translations.startConversation}</p>
          </div>
        ) : (
          conversation.messages.map((message) => (
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
          ))
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
              placeholder={translations.typeMessage}
              className="flex-1 px-4 py-3 bg-[color:var(--background)] border border-[color:var(--border)] rounded-xl text-[color:var(--foreground)] placeholder:text-[color:var(--muted-foreground)] focus:ring-2 focus:ring-[color:var(--ring)] focus:outline-none transition-all duration-200"
            />
            <Button
              type="submit"
              disabled={!input.trim()}
              className="px-6 py-3 bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] hover:shadow-[var(--button-hover-shadow)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FontAwesomeIcon icon={faPaperPlane} />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
