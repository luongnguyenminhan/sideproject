/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState, useEffect } from 'react';
import { Check, ChevronLeft, ArrowRight } from 'lucide-react';
import { questionSessionService } from '@/apis/questionSessionService';
import { Question, QuestionOption } from '@/types/question.types';
import { useTranslation } from '@/contexts/TranslationContext';
import { submitSurveyResponse } from '@/apis/questionApi';
import AnimatedSurveyWrapper from './AnimatedSurveyWrapper';
import AnimatedStepper from './AnimatedStepper';
import QuestionRenderer from './QuestionRenderer';

interface SurveyContainerProps {
  questions: Question[];
  onSurveyComplete?: (answers: Record<number, unknown>) => void;
  websocket?: { isConnected: () => boolean; sendRawMessage: (message: string) => void } | null;
  conversationId?: string;
  isEmbedded?: boolean; // Để biết có phải đang chạy trong panel hay không
  onClose?: () => void;
}

const SurveyContainer: React.FC<SurveyContainerProps> = ({ 
  questions, 
  onSurveyComplete,
  websocket,
  conversationId,
  isEmbedded = false,
  onClose
}) => {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, any>>({});
  const [showResults, setShowResults] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [sessionQuestions, setSessionQuestions] = useState<Question[] | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Use session questions if available, otherwise use prop questions
  const effectiveQuestions = sessionQuestions || questions;

  // Check for session ID from storage and fetch questions (only once)
  useEffect(() => {
    const checkForSessionId = async () => {
      const sessionId = window.sessionStorage.getItem('current_survey_session_id');
      if (sessionId && sessionId !== currentSessionId) {
        console.log('[SurveyContainer] Found session ID in storage:', sessionId);
        setCurrentSessionId(sessionId);
        setIsLoadingSession(true);
        
        try {
          const sessionData = await questionSessionService.getSessionQuestions(sessionId);
          console.log('[SurveyContainer] Fetched session questions:', sessionData);
          
          if (sessionData.questions && sessionData.questions.length > 0) {
            setSessionQuestions(sessionData.questions);
            // Clear the session ID from storage
            window.sessionStorage.removeItem('current_survey_session_id');
          }
        } catch (error) {
          console.error('[SurveyContainer] Error fetching session questions:', error);
        } finally {
          setIsLoadingSession(false);
        }
      }
    };

    checkForSessionId();
  }, [currentSessionId]);

  // Debug logging for SurveyContainer
  console.log('[SurveyContainer] Render with questions:', {
    questionsCount: effectiveQuestions.length,
    currentStep,
    isEmbedded,
    conversationId,
    hasWebsocket: !!websocket,
    websocketConnected: websocket?.isConnected?.(),
    isLoadingSession,
    hasSessionQuestions: !!sessionQuestions,
    currentSessionId,
    questions: effectiveQuestions.map((q, i) => ({
      index: i,
      question: q.Question,
      type: q.Question_type,
      hasData: !!q.Question_data,
      dataLength: Array.isArray(q.Question_data) ? q.Question_data.length : 'not array'
    }))
  })


  const progress = ((currentStep + 1) / effectiveQuestions.length) * 100;

  const handleAnswerChange = (questionIndex: number, answerId: string, value?: any) => {
    setSelectedAnswers({
      ...selectedAnswers,
      [questionIndex]: value !== undefined ? value : answerId,
    });
  };

  const handleNext = async () => {
    if (currentStep < effectiveQuestions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      setIsSubmitting(true);
      try {
        // Send survey response via WebSocket if available
        if (websocket && websocket.isConnected()) {
          const surveyResponse = {
            type: 'survey_response',
            answers: selectedAnswers,
            conversation_id: conversationId,
            timestamp: new Date().toISOString()
          };
          
          websocket.sendRawMessage(JSON.stringify(surveyResponse));
          console.log('[SurveyContainer] Survey response sent via WebSocket');
        }

        // Call completion callback if provided
        if (onSurveyComplete) {
          await onSurveyComplete(selectedAnswers);
        } else if (!websocket?.isConnected()) {
          // Fallback to API submission if no websocket and no callback
          await submitSurveyResponse(selectedAnswers);
        }
        
        setShowResults(true);
      } catch (error) {
        console.error('Error submitting survey:', error);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const isQuestionAnswered = (questionIndex: number): boolean => {
    const question = effectiveQuestions[questionIndex];
    const answers = selectedAnswers[questionIndex];

    if (!answers) return false;

    switch (question.Question_type) {
      case 'text_input':
        const options = question.Question_data as QuestionOption[];
        return options.every((option) => {
          if (option.required) {
            const textAnswers = answers as Record<string, string>;
            return textAnswers[option.id] && textAnswers[option.id].trim() !== '';
          }
          return true;
        });
      case 'multiple_choice':
        return Array.isArray(answers) && answers.length > 0;
      case 'single_option':
        return answers !== undefined && answers !== null;
      case 'sub_form':
        const subQuestions = question.Question_data as Question[];
        const subAnswers = answers as Record<number, any>;
        return subQuestions.every((_, subIndex) => {
          return subAnswers[subIndex] !== undefined;
        });
      default:
        return true;
    }
  };

  const currentQuestion = effectiveQuestions[currentStep];

  if (showResults) {      return (
        <AnimatedSurveyWrapper currentStep={effectiveQuestions.length} totalSteps={effectiveQuestions.length}>
        <div className="w-full h-full flex flex-col">
          <div className="flex-1 container mx-auto px-4 py-4 md:py-8 flex items-center justify-center">
            <div className="w-full max-w-4xl mx-auto">
              <div className="bg-[color:var(--background)]/95 rounded-3xl shadow-2xl border border-[color:var(--border)]/50 backdrop-blur-sm p-8 md:p-12 text-center">
          <div className="mb-8">
            <div className="inline-flex items-center space-x-2 bg-[color:var(--feature-green)] text-[color:var(--feature-green-text)] px-6 py-3 rounded-full text-sm font-medium mb-6 shadow-lg">
              <Check className="w-5 h-5" />
              <span>{t('survey.results.completed')}</span>
            </div>
            
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent mb-6">
              {t('survey.results.title')}
            </h1>
            
            <p className="text-xl text-[color:var(--muted-foreground)] max-w-2xl mx-auto mb-8">
              {t('survey.results.description_sent')}
            </p>

            {/* Success animation */}
            <div className="relative mb-8">
              <div className="w-24 h-24 mx-auto bg-[color:var(--feature-green)] rounded-full flex items-center justify-center shadow-lg">
                <Check className="w-12 h-12 text-[color:var(--feature-green-text)]" />
              </div>
              <div className="absolute inset-0 w-24 h-24 mx-auto bg-[color:var(--feature-green)] rounded-full animate-ping opacity-20"></div>
            </div>
          </div>

          {onClose && (
            <div className="space-y-4">
              <button
                onClick={onClose}
                className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1"
              >
                {t('common.close')}
              </button>
            </div>
          )}
              </div>
            </div>
          </div>
        </div>
      </AnimatedSurveyWrapper>
    );
    }

  return (
    <AnimatedSurveyWrapper currentStep={currentStep} totalSteps={effectiveQuestions.length}>
      <div className={`w-full h-full flex flex-col ${isEmbedded ? '' : 'h-screen'}`}>
        {/* Header offset - only for full screen mode */}
        {!isEmbedded && <div className="h-14 flex-shrink-0"></div>}
        
        <div className={`flex-1 ${isEmbedded ? 'p-1' : 'container mx-auto px-4 py-4 md:py-8'} flex items-center overflow-hidden`}>
          <div className="w-full max-w-4xl mx-auto h-full">
            <div className={`bg-[color:var(--background)]/95 rounded-3xl shadow-2xl border border-[color:var(--border)]/50 backdrop-blur-sm ${
              isEmbedded ? 'h-full p-2' : 'h-full max-h-[calc(100vh-160px)] p-4 md:p-8'
            } flex flex-col overflow-hidden`}>
              {/* Animated Progress Indicator */}
              <AnimatedStepper 
                currentStep={currentStep}
                totalSteps={effectiveQuestions.length}
                questions={effectiveQuestions}
              />

              {/* Question Header */}
              <div className={`text-center ${isEmbedded ? 'mb-2 md:mb-4' : 'mb-4 md:mb-6'} flex-shrink-0`}>
                <div className={`inline-flex items-center space-x-2 bg-[color:var(--feature-blue)] text-[color:var(--feature-blue-text)] px-4 py-2 rounded-full ${
                  isEmbedded ? 'text-xs' : 'text-sm'
                } font-medium mb-4`}>
                  <span>
                    Question {currentStep + 1} of {effectiveQuestions.length}
                  </span>
                  <span>•</span>
                  <span className="capitalize">
                    {currentQuestion.Question_type == 'single_option' ? t('survey.type.single_option') : 
                      currentQuestion.Question_type == 'multiple_choice' ? t('survey.type.multiple_choice') :
                      currentQuestion.Question_type == 'text_input' ? t('survey.type.text_input') :
                      currentQuestion.Question_type == 'sub_form' ? t('survey.type.sub_form') :
                      t('survey.type.unknown_type')}
                  </span>
                </div>
                
                <h1 className={`${isEmbedded ? 'text-lg md:text-xl' : 'text-xl md:text-3xl'} font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent mb-3`}>
                  {currentQuestion.Question}
                </h1>
                
                {currentQuestion.subtitle && (
                  <p className={`${isEmbedded ? 'text-sm' : 'text-base md:text-lg'} text-[color:var(--muted-foreground)] max-w-3xl mx-auto`}>
                    {currentQuestion.subtitle}
                  </p>
                )}
              </div>

              {/* Question Content */}
              <div className={`flex-1 overflow-y-auto ${isEmbedded ? 'mb-2 md:mb-4' : 'mb-4 md:mb-6'} min-h-0 overflow-x-hidden`}>
                <QuestionRenderer
                  question={currentQuestion}
                  questionIndex={currentStep}
                  selectedAnswers={selectedAnswers}
                  onAnswerChange={handleAnswerChange}
                />
              </div>

              {/* Navigation */}
              <div className={`flex flex-col sm:flex-row justify-between items-center gap-2 md:gap-4 ${isEmbedded ? 'mb-1' : 'mb-4'} flex-shrink-0 px-2`}>
                <button
                  onClick={handleBack}
                  disabled={currentStep === 0}
                  className={`
                    flex items-center space-x-2 px-3 md:px-6 py-2 md:py-3 rounded-xl font-semibold transition-all duration-300 w-full sm:w-auto justify-center sm:justify-start text-sm md:text-base
                    ${
                      currentStep === 0
                        ? 'text-[color:var(--muted-foreground)] cursor-not-allowed bg-[color:var(--muted)]/30'
                        : 'text-[color:var(--foreground)] hover:bg-[color:var(--muted)] border border-[color:var(--border)]'
                    }
                  `}
                >
                  <ChevronLeft className="w-4 h-4 md:w-5 md:h-5" />
                  <span>{t('survey.previous')}</span>
                </button>

                <button
                  onClick={handleNext}
                  disabled={!isQuestionAnswered(currentStep) || isSubmitting}
                  className={`
                    flex items-center space-x-2 px-4 md:px-8 py-2 md:py-4 rounded-xl font-semibold transition-all duration-300 transform w-full sm:w-auto justify-center text-sm md:text-base
                    ${
                      isQuestionAnswered(currentStep) && !isSubmitting
                        ? 'bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white hover:shadow-lg hover:-translate-y-1'
                        : 'bg-[color:var(--muted)] text-[color:var(--muted-foreground)] cursor-not-allowed'
                    }
                  `}
                >
                  <span>
                    {isSubmitting
                      ? t('survey.submitting')
                      : currentStep === effectiveQuestions.length - 1
                      ? t('survey.complete')
                      : t('survey.continue')
                    }
                  </span>
                  {!isSubmitting && <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />}
                  {isSubmitting && (
                    <div className="w-4 h-4 md:w-5 md:h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  )}
                </button>
              </div>

              {/* Progress Bar */}
              <div className={`space-y-2 flex-shrink-0 px-2 ${isEmbedded ? 'pb-1' : 'pb-4'}`}>
                <div className={`flex justify-between ${isEmbedded ? 'text-xs' : 'text-sm'} font-medium text-[color:var(--muted-foreground)]`}>
                  <span>Progress</span>
                  <span>{Math.round(progress)}% Complete</span>
                </div>
                <div className={`w-full bg-[color:var(--muted)] rounded-full ${isEmbedded ? 'h-1.5' : 'h-3 md:h-4'} overflow-hidden`}>
                  <div
                    className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] h-full rounded-full transition-all duration-700 ease-out relative"
                    style={{ width: `${progress}%` }}
                  >
                    <div className="absolute inset-0 bg-white/20 rounded-full animate-pulse"></div>
                  </div>
                </div>
                <div className={`text-center ${isEmbedded ? 'text-xs' : 'text-sm'} text-[color:var(--muted-foreground)]`}>
                  {t('survey.step')} {currentStep + 1} / {effectiveQuestions.length}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AnimatedSurveyWrapper>
  );
};

export default SurveyContainer;
