'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faClipboardList, faTimes, faChevronLeft } from '@fortawesome/free-solid-svg-icons'
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
}

export function SurveyPanel({
  isOpen,
  onClose,
  questions,
  title = 'Career Survey',
  websocket,
  conversationId,
  onSurveyComplete
}: SurveyPanelProps) {
  const { t } = useTranslation()
  const [isMinimized, setIsMinimized] = useState(false)

  // Debug logging for survey panel
  console.log('[SurveyPanel] Render with props:', {
    isOpen,
    questionsCount: questions.length,
    hasQuestions: questions.length > 0,
    title,
    conversationId,
    questionsPreview: questions.slice(0, 2),
    questionsStructure: questions.map((q, i) => ({
      index: i,
      question: q.Question?.substring(0, 50) + '...',
      type: q.Question_type,
      hasData: !!q.Question_data,
      dataType: Array.isArray(q.Question_data) ? 'array' : typeof q.Question_data
    }))
  })

  if (!isOpen) return null

  return (
    <div className={`h-full flex flex-col bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] transition-all duration-300 ease-in-out ${
      isMinimized ? 'w-12' : 'w-full'
    }`}>
      {/* Survey Header */}
      <div className="flex items-center justify-between p-4 border-b border-[color:var(--border)]/20 bg-[color:var(--background)]/10 backdrop-blur-md flex-shrink-0">
        {!isMinimized ? (
          <>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-[color:var(--feature-blue)] to-[color:var(--feature-purple)] rounded-xl flex items-center justify-center shadow-lg">
                <FontAwesomeIcon icon={faClipboardList} className="text-white text-lg" />
              </div>
              <div>
                <h2 className="text-lg font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent">
                  {title}
                </h2>
                <p className="text-xs text-[color:var(--muted-foreground)]">
                  {questions.length} questions • AI-Generated
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setIsMinimized(true)}
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 hover:bg-[color:var(--accent)] transition-all duration-200 group"
                title="Minimize survey"
              >
                <FontAwesomeIcon 
                  icon={faChevronLeft} 
                  className="text-sm text-[color:var(--muted-foreground)] group-hover:text-[color:var(--foreground)]" 
                />
              </Button>
              <Button
                onClick={onClose}
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 hover:bg-[color:var(--accent)] transition-all duration-200 group"
                title="Close survey"
              >
                <FontAwesomeIcon 
                  icon={faTimes} 
                  className="text-sm text-[color:var(--muted-foreground)] group-hover:text-[color:var(--foreground)]" 
                />
              </Button>
            </div>
          </>
        ) : (
          <div className="w-full flex justify-center">
            <Button
              onClick={() => setIsMinimized(false)}
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 hover:bg-[color:var(--accent)] transition-all duration-200 group"
              title="Expand survey"
            >
              <FontAwesomeIcon 
                icon={faClipboardList} 
                className="text-sm text-[color:var(--feature-blue)] group-hover:text-[color:var(--foreground)]" 
              />
            </Button>
          </div>
        )}
      </div>

      {/* Survey Content */}
      {!isMinimized && (
        <div className="flex-1 overflow-hidden">
          {questions.length > 0 ? (
            <div className="h-full p-2">
              <div className="bg-[color:var(--background)]/95 rounded-2xl shadow-xl border border-[color:var(--border)]/50 backdrop-blur-sm h-full overflow-hidden">
                <SurveyContainer 
                  questions={questions}
                  onSurveyComplete={onSurveyComplete}
                  websocket={websocket}
                  conversationId={conversationId}
                  isEmbedded={true}
                />
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center p-8">
              <div className="text-center">
                <div className="w-24 h-24 mx-auto mb-6 bg-[color:var(--muted)] rounded-full flex items-center justify-center">
                  <FontAwesomeIcon icon={faClipboardList} className="text-3xl text-[color:var(--muted-foreground)]" />
                </div>
                <h3 className="text-xl font-semibold text-[color:var(--foreground)] mb-2">
                  {t('survey.noQuestions') || 'No Survey Questions'}
                </h3>
                <p className="text-[color:var(--muted-foreground)] text-sm">
                  {t('survey.waitingForData') || 'Waiting for survey data...'}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Minimized State Indicator */}
      {isMinimized && questions.length > 0 && (
        <div className="flex-1 flex flex-col items-center justify-center p-2">
          <div className="w-8 h-8 bg-[color:var(--feature-green)] rounded-full flex items-center justify-center mb-2 animate-pulse">
            <span className="text-white text-xs font-bold">{questions.length}</span>
          </div>
          <div className="text-xs text-[color:var(--muted-foreground)] text-center transform -rotate-90 whitespace-nowrap">
            Survey Active
          </div>
        </div>
      )}
    </div>
  )
}
