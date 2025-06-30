/* eslint-disable @typescript-eslint/no-unused-vars */
'use client'

import { useState, useEffect } from 'react'
import { SurveyPanel } from './SurveyPanel'
import { useSurveyQuestions } from '@/hooks/useSurveyQuestions'
import { Question } from '@/types/question.types'
import { useTranslation } from '@/contexts/TranslationContext'

interface SurveyPanelWrapperProps {
  isOpen: boolean
  onClose: () => void
  websocket?: { isConnected: () => boolean; sendRawMessage: (message: string) => void } | null
  conversationId?: string
  onSurveyComplete?: (answers: Record<number, unknown>) => void
  onSendToChat?: (message: string, isAIResponse?: boolean) => void
  fallbackQuestions?: Question[]
}

export function SurveyPanelWrapper({
  isOpen,
  onClose,
  websocket,
  conversationId,
  onSurveyComplete,
  onSendToChat,
  fallbackQuestions = []
}: SurveyPanelWrapperProps) {
  const { t } = useTranslation()
  const { questions: apiQuestions, loading, error, fetchQuestions } = useSurveyQuestions()
  const [displayQuestions, setDisplayQuestions] = useState<Question[]>(fallbackQuestions)
  const [title, setTitle] = useState('Career Survey')

  // Effect to fetch questions when panel opens
  useEffect(() => {
    console.log('[SurveyPanelWrapper] Effect triggered:', { 
      isOpen, 
      hasSessionStorage: typeof window !== 'undefined' 
    })
    
    if (isOpen) {
      // Small delay to ensure sessionStorage is set
      const checkSessionId = () => {
        const sessionId = window.sessionStorage.getItem('current_survey_session_id')
        
        console.log('[SurveyPanelWrapper] Panel opened, checking for session ID:', {
          sessionId,
          fallbackQuestionsLength: fallbackQuestions.length,
          timestamp: new Date().toISOString()
        })
        
        if (sessionId) {
          console.log('[SurveyPanelWrapper] Found session ID, fetching questions...')
          fetchQuestions(sessionId)
        } else {
          console.log('[SurveyPanelWrapper] No session ID found, using fallback questions')
          setDisplayQuestions(fallbackQuestions)
        }
      }
      
      // Check immediately and after small delay
      checkSessionId()
      setTimeout(checkSessionId, 100) // Backup check after 100ms
    }
  }, [isOpen, fetchQuestions, fallbackQuestions])

  // Effect to update display questions when API questions are fetched
  useEffect(() => {
    console.log('[SurveyPanelWrapper] API questions changed:', {
      hasApiQuestions: !!apiQuestions,
      apiQuestionsStructure: apiQuestions ? {
        session_id: apiQuestions.session_id,
        session_name: apiQuestions.session_name,
        session_type: apiQuestions.session_type,
        total_questions: apiQuestions.total_questions,
        questions_array_length: apiQuestions.questions?.length || 0,
        questions_is_array: Array.isArray(apiQuestions.questions)
      } : null,
      currentDisplayQuestions: displayQuestions.length
    })

    if (apiQuestions?.questions && Array.isArray(apiQuestions.questions)) {
      console.log('[SurveyPanelWrapper] Setting questions from API:', {
        sessionName: apiQuestions.session_name,
        sessionType: apiQuestions.session_type,
        questionsCount: apiQuestions.total_questions,
        questions: apiQuestions.questions.slice(0, 2) // Preview first 2 questions
      })
      
      setDisplayQuestions(apiQuestions.questions)
      setTitle(apiQuestions.session_name || 'Career Survey')
    }
  }, [apiQuestions, displayQuestions.length])

  // Handle close - clear session storage
  const handleClose = () => {
    console.log('[SurveyPanelWrapper] Closing survey panel')
    window.sessionStorage.removeItem('current_survey_session_id')
    onClose()
  }

  // Loading state - show when loading OR when we have no questions yet and should be fetching
  const shouldShowLoading = isOpen && (
    loading || 
    (displayQuestions.length === 0 && !error && typeof window !== 'undefined' && window.sessionStorage?.getItem('current_survey_session_id'))
  )
  
  if (shouldShowLoading) {
    return (
      <div className="h-full flex flex-col bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] w-full">
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[color:var(--feature-blue)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-[color:var(--foreground)] font-medium">Loading Survey Questions...</p>
            <p className="text-sm text-[color:var(--muted-foreground)] mt-2">
              Fetching personalized questions from AI
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error && isOpen) {
    return (
      <div className="h-full flex flex-col bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] w-full">
        <div className="flex items-center justify-center h-full">
          <div className="text-center max-w-md p-6">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.232 15.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-[color:var(--foreground)] mb-2">Failed to Load Survey</h3>
            <p className="text-sm text-[color:var(--muted-foreground)] mb-4">{error}</p>
            <div className="flex gap-2 justify-center">
              <button
                onClick={() => {
                  const sessionId = window.sessionStorage.getItem('current_survey_session_id')
                  if (sessionId) {
                    fetchQuestions(sessionId)
                  }
                }}
                className="px-4 py-2 bg-[color:var(--feature-blue)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
              >
                Retry
              </button>
              <button
                onClick={handleClose}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Debug log final render
  console.log('[SurveyPanelWrapper] Final render:', {
    isOpen,
    displayQuestionsLength: displayQuestions.length,
    title,
    shouldShowLoading,
    loading,
    error,
    hasSessionId: typeof window !== 'undefined' ? !!window.sessionStorage?.getItem('current_survey_session_id') : false
  })

  // Render SurveyPanel with fetched or fallback questions
  return (
    <SurveyPanel
      isOpen={isOpen}
      onClose={handleClose}
      questions={displayQuestions}
      title={title}
      websocket={websocket}
      conversationId={conversationId}
      onSurveyComplete={onSurveyComplete}
      onSendToChat={onSendToChat}
    />
  )
} 