'use client'

import ChatClientWrapper from '@/components/chat/ChatClientWrapper'
import { Button } from '@/components/ui/button'
import ClientWrapper from '@/components/layout/client-wrapper'
import { TranslationProvider } from '@/contexts/TranslationContext'
import { useState } from 'react'

// Mock dictionary for testing
const mockDictionary = {
  chat: {
    title: 'Chat Test',
    sendMessage: 'Send Message',
    newChat: 'New Chat'
  }
}

export default function ChatTestPage() {
  const [useV2, setUseV2] = useState(false)
  const [showComparison, setShowComparison] = useState(false)

  return (
    <ClientWrapper>
      <div className="h-[calc(100vh-56px)] bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
        <div className="h-full bg-background overflow-hidden">
          <TranslationProvider dictionary={mockDictionary} locale="en">
            
            {/* Test Controls */}
            <div className="fixed top-4 left-4 z-50 bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-4 shadow-lg">
              <div className="text-sm font-semibold text-[color:var(--foreground)] mb-3">
                🧪 WebSocket Test Controls
              </div>
              
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => setUseV2(false)}
                    variant={!useV2 ? "default" : "outline"}
                    size="sm"
                  >
                    WebSocket V1 (Agent)
                  </Button>
                  <Button
                    onClick={() => setUseV2(false)}
                    variant={useV2 ? "default" : "outline"}
                    size="sm"
                  >
                    WebSocket V2 (n8n)
                  </Button>
                </div>
                
                <Button
                  onClick={() => setShowComparison(!showComparison)}
                  variant="outline"
                  size="sm"
                >
                  {showComparison ? 'Hide' : 'Show'} Side-by-Side
                </Button>
                
                <div className="text-xs text-[color:var(--muted-foreground)] mt-2">
                  <div>Current: WebSocket {useV2 ? 'V2 (n8n)' : 'V1 (Agent)'}</div>
                  <div>URL Pattern: {useV2 ? '/api/v2/chat/ws/' : '/api/v1/chat/ws/'}</div>
                </div>
              </div>
            </div>

            {/* Chat Interface */}
            {showComparison ? (
              // Side-by-side comparison
              <div className="flex h-full">
                <div className="flex-1 border-r border-[color:var(--border)]">
                  <div className="h-8 bg-[color:var(--muted)] flex items-center justify-center text-sm font-medium">
                    WebSocket V1 (Agent System)
                  </div>
                  <div className="h-[calc(100%-2rem)]">
                    <ChatClientWrapper useWebSocketV2={false} />
                  </div>
                </div>
                <div className="flex-1">
                  <div className="h-8 bg-[color:var(--primary)] text-[color:var(--primary-foreground)] flex items-center justify-center text-sm font-medium">
                    WebSocket V2 (n8n Integration)
                  </div>
                  <div className="h-[calc(100%-2rem)]">
                    <ChatClientWrapper useWebSocketV2={true} />
                  </div>
                </div>
              </div>
            ) : (
              // Single view
              <ChatClientWrapper useWebSocketV2={useV2} />
            )}
            
          </TranslationProvider>
        </div>
      </div>
    </ClientWrapper>
  )
} 