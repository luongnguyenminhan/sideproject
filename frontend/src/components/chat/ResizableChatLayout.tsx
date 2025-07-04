'use client'

import { useState, useEffect } from 'react'
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import { SurveyPanelWrapper } from './SurveyPanelWrapper'
import { Question } from '@/types/question.types'

interface ResizableChatLayoutProps {
  children: React.ReactNode // Chat interface content
  isSurveyOpen: boolean
  onSurveyClose: () => void
  websocket?: { isConnected: () => boolean; sendRawMessage: (message: string) => void } | null
  conversationId?: string
  onSurveyComplete?: (answers: Record<number, unknown>) => void
  onSendToChat?: (message: string, isAIResponse?: boolean) => void
  fallbackQuestions?: Question[]
}

export function ResizableChatLayout({
  children,
  isSurveyOpen,
  onSurveyClose,
  websocket,
  conversationId,
  onSurveyComplete,
  onSendToChat,
  fallbackQuestions = []
}: ResizableChatLayoutProps) {
  const [chatPanelSize, setChatPanelSize] = useState(70) // Default 70% for chat
  const [surveyPanelSize, setSurveyPanelSize] = useState(30) // Default 30% for survey

  // Auto-adjust panel sizes when survey opens/closes
  useEffect(() => {
    if (isSurveyOpen) {
      setChatPanelSize(70)
      setSurveyPanelSize(30)
    } else {
      setChatPanelSize(100)
      setSurveyPanelSize(0)
    }
  }, [isSurveyOpen])

  // Handle panel resize
  const handlePanelResize = (sizes: number[]) => {
    if (sizes.length >= 2) {
      setChatPanelSize(sizes[0])
      setSurveyPanelSize(sizes[1])
    }
  }

  if (!isSurveyOpen) {
    // When survey is closed, show only chat
    return (
      <div className="h-full w-full">
        {children}
      </div>
    )
  }

  return (
    <div className="h-full w-full">
      <ResizablePanelGroup 
        direction="horizontal" 
        onLayout={handlePanelResize}
        className="h-full w-full"
      >
        {/* Chat Panel */}
        <ResizablePanel 
          defaultSize={chatPanelSize}
          minSize={40}
          maxSize={80}
          className="h-full"
        >
          <div className="h-full w-full overflow-hidden">
            {children}
          </div>
        </ResizablePanel>

        {/* Resizable Handle */}
        <ResizableHandle 
          withHandle 
          className="w-2 bg-[color:var(--border)] hover:bg-[color:var(--accent)] transition-colors duration-200"
        />

        {/* Survey Panel */}
        <ResizablePanel 
          defaultSize={surveyPanelSize}
          minSize={20}
          maxSize={60}
          className="h-full"
        >
          <div className="h-full w-full">
            <SurveyPanelWrapper
              isOpen={isSurveyOpen}
              onClose={onSurveyClose}
              websocket={websocket}
              conversationId={conversationId}
              onSurveyComplete={onSurveyComplete}
              onSendToChat={onSendToChat}
              fallbackQuestions={fallbackQuestions}
            />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
} 