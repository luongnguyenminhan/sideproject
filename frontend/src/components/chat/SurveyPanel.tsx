'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faClipboardList, faTimes } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'
import { Question } from '@/types/question.types'
import SurveyContainer from '@/components/survey/SurveyContainer'

interface SurveyPanelProps {
  isOpen: boolean
  onClose: () => void
  questions: Question[]
  title?: string
  websocket?: { isConnected: () => boolean; sendRawMessage: (message: string) => void } | null
  conversationId?: string
  onSurveyComplete?: (answers: Record<number, unknown>) => void
  onSendToChat?: (message: string, isAIResponse?: boolean) => void
}

export function SurveyPanel({
  isOpen,
  onClose,
  questions,
  title = 'Career Survey',
  websocket,
  conversationId,
  onSurveyComplete,
  onSendToChat
}: SurveyPanelProps) {
  const { t } = useTranslation()
  const [isProcessing, setIsProcessing] = useState(false)

  // Simplified survey completion handler - chỉ pass through, để SurveyContainer xử lý
  const handleSurveyComplete = async (answers: Record<number, unknown>) => {
    console.log('[SurveyPanel] Survey completed with answers:', answers)
    setIsProcessing(true)

    try {
      // Call completion callback - let SurveyContainer handle API calls
      if (onSurveyComplete) {
        await onSurveyComplete(answers)
      }

      console.log('[SurveyPanel] Survey processing completed successfully')
      
    } catch (error) {
      console.error('[SurveyPanel] Survey completion failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  // Debug logging for survey panel  
  console.log('[SurveyPanel] Render with props:', {
    isOpen,
    questionsCount: questions.length,
    hasQuestions: questions.length > 0,
    title,
    conversationId,
    isProcessing,
    hasSendToChatCallback: !!onSendToChat,
    questionsPreview: questions.slice(0, 2)
  })

  if (!isOpen) return null

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)]">
      {/* Survey Header - Compact for Resizable Layout */}
      <div className="flex items-center justify-between p-3 border-b border-[color:var(--border)]/20 bg-[color:var(--background)]/10 backdrop-blur-md flex-shrink-0">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="w-8 h-8 bg-gradient-to-r from-[color:var(--feature-blue)] to-[color:var(--feature-purple)] rounded-lg flex items-center justify-center shadow-lg">
            <FontAwesomeIcon icon={faClipboardList} className="text-white text-sm" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-sm font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent truncate">
              {title}
              {isProcessing && (
                <span className="ml-2 inline-flex items-center">
                  <div className="w-3 h-3 border-2 border-[color:var(--feature-blue)] border-t-transparent rounded-full animate-spin"></div>
                </span>
              )}
            </h2>
            <p className="text-xs text-[color:var(--muted-foreground)] truncate">
              {isProcessing 
                ? 'Processing...' 
                : `${questions.length} questions`
              }
            </p>
          </div>
        </div>
        <Button
          onClick={onClose}
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 hover:bg-[color:var(--accent)] transition-all duration-200 group flex-shrink-0"
          title="Close survey"
        >
          <FontAwesomeIcon 
            icon={faTimes} 
            className="text-xs text-[color:var(--muted-foreground)] group-hover:text-[color:var(--foreground)]" 
          />
        </Button>
      </div>

      {/* Survey Content - Optimized for Resizable */}
      <div className="flex-1 overflow-hidden">
        {questions.length > 0 ? (
          <div className="h-full p-2">
            <div className="bg-[color:var(--background)]/95 rounded-xl shadow-lg border border-[color:var(--border)]/50 backdrop-blur-sm h-full overflow-hidden">
              <SurveyContainer 
                questions={questions}
                onSurveyComplete={handleSurveyComplete}
                websocket={websocket}
                conversationId={conversationId}
                isEmbedded={true}
                onSendToChat={onSendToChat}
              />
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center p-4">
            <div className="text-center max-w-xs">
              <div className="w-16 h-16 mx-auto mb-4 bg-[color:var(--muted)] rounded-full flex items-center justify-center">
                <FontAwesomeIcon icon={faClipboardList} className="text-2xl text-[color:var(--muted-foreground)]" />
              </div>
              <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-2">
                {t('survey.noQuestions') || 'No Questions'}
              </h3>
              <p className="text-[color:var(--muted-foreground)] text-sm">
                {t('survey.waitingForData') || 'Waiting for survey data...'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Status Indicator for Processing */}
      {isProcessing && (
        <div className="px-3 py-2 bg-[color:var(--background)]/90 border-t border-[color:var(--border)]/20 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-[color:var(--feature-blue)] border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-[color:var(--muted-foreground)]">
            Processing survey response...
          </span>
        </div>
      )}
    </div>
  )
}
