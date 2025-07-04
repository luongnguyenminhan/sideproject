'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faClipboardList, faTimes, faChevronLeft } from '@fortawesome/free-solid-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'
import { Question } from '@/types/question.types'
import SurveyContainer from '@/components/survey/SurveyContainer'
import { surveyAPI, type SurveyResponse } from '@/apis/surveyApi'

interface SurveyPanelProps {
  isOpen: boolean
  onClose: () => void
  questions: Question[]
  title?: string
  websocket?: { isConnected: () => boolean; sendRawMessage: (message: string) => void } | null
  conversationId?: string
  onSurveyComplete?: (answers: Record<number, unknown>) => void
  onSendToChat?: (message: string, isAIResponse?: boolean) => void // New prop for sending to chat
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
  const [isMinimized, setIsMinimized] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  // Enhanced survey completion handler
  const handleSurveyComplete = async (answers: Record<number, unknown>) => {
    console.log('[SurveyPanel] Survey completed with answers:', answers)
    setIsProcessing(true)

    try {
      // Chuẩn bị survey response data
      const surveyData: SurveyResponse = {
        type: 'survey_response',
        answers: answers,
        conversation_id: conversationId,
        timestamp: new Date().toISOString()
      }

      try {
        // Gọi API optimized cho chat integration
        const result = await surveyAPI.processAndSendToChat(surveyData)
        console.log('[SurveyPanel] Enhanced survey processing result:', result)
        
        if (result.error_code === 0 && result.data) {
          // Extract the processed data
          const surveyResultData = result.data
          const websocketMessages = surveyResultData?.websocket_messages || []
          
          // Send messages to chat using the callback
          if (onSendToChat && websocketMessages.length > 0) {
            for (let i = 0; i < websocketMessages.length; i++) {
              const message = websocketMessages[i]
              const isAIMessage = message.role === 'assistant'
              
              // Add delay between messages for better UX
              if (i > 0) {
                await new Promise(resolve => setTimeout(resolve, 1000))
              }
              
              await onSendToChat(message.content, isAIMessage)
              console.log(`[SurveyPanel] Message ${i + 1}/${websocketMessages.length} sent to chat (AI: ${isAIMessage})`)
            }
          }

          // Send via WebSocket if available (alternative/backup method)
          if (websocket && websocket.isConnected() && websocketMessages.length > 0) {
            for (let i = 0; i < websocketMessages.length; i++) {
              const message = websocketMessages[i]
              
              // Add delay between WebSocket messages
              if (i > 0) {
                await new Promise(resolve => setTimeout(resolve, 1500))
              }
              
              websocket.sendRawMessage(JSON.stringify(message))
              console.log(`[SurveyPanel] WebSocket message ${i + 1}/${websocketMessages.length} sent`)
            }
          }
        }
      } catch (primaryError) {
        console.error('[SurveyPanel] Primary API failed, trying fallback:', primaryError)
        
        // Fallback: thử complete workflow endpoint
        try {
          const fallbackResult = await surveyAPI.processSurveyWorkflow(surveyData)
          
          if (fallbackResult.error_code === 0 && fallbackResult.data) {
            const humanMessage = fallbackResult.data.human_readable_response
            const aiResponse = fallbackResult.data.ai_response
            
            if (humanMessage && onSendToChat) {
              await onSendToChat(humanMessage, false)
              if (aiResponse) {
                setTimeout(() => onSendToChat(aiResponse.content, true), 1000)
              }
            }
          }
        } catch (fallbackError) {
          console.error('[SurveyPanel] Fallback API also failed:', fallbackError)
          
          // Final fallback: submit basic response
          try {
            await surveyAPI.submitSurveyResponse(answers, conversationId)
          } catch (basicError) {
            console.error('[SurveyPanel] Basic submit also failed:', basicError)
          }
        }
      }

      // Call original completion callback if provided
      if (onSurveyComplete) {
        await onSurveyComplete(answers)
      }

      console.log('[SurveyPanel] Enhanced survey processing completed successfully')
      
    } catch (error) {
      console.error('[SurveyPanel] Error processing survey:', error)
      
      // Fallback: call original completion callback
      if (onSurveyComplete) {
        await onSurveyComplete(answers)
      }
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
                  {isProcessing && (
                    <span className="ml-2 inline-flex items-center">
                      <div className="w-4 h-4 border-2 border-[color:var(--feature-blue)] border-t-transparent rounded-full animate-spin"></div>
                    </span>
                  )}
                </h2>
                <p className="text-xs text-[color:var(--muted-foreground)]">
                  {isProcessing 
                    ? 'Processing survey response...' 
                    : `${questions.length} questions • AI-Generated`
                  }
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
                  onSurveyComplete={handleSurveyComplete} // Use our enhanced handler
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
