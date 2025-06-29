/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState, useEffect } from 'react';
import { X, FileText, ArrowRight, Check } from 'lucide-react';
import { Question } from '@/types/question.types';
import { useTranslation } from '@/contexts/TranslationContext';
import QuestionRenderer from '@/components/survey/QuestionRenderer';
import AnimatedStepper from '@/components/survey/AnimatedStepper';

interface SurveyModalProps {
  isOpen: boolean;
  onClose: () => void;
  questions: Question[];
  onComplete?: (answers: Record<number, any>) => void;
  title?: string;
}

export function SurveyModal({ 
  isOpen, 
  onClose, 
  questions, 
  onComplete,
  title = 'Survey Form'
}: SurveyModalProps) {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showResults, setShowResults] = useState(false);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
      setSelectedAnswers({});
      setIsSubmitting(false);
      setShowResults(false);
    }
  }, [isOpen]);

  const progress = questions.length > 0 ? ((currentStep + 1) / questions.length) * 100 : 0;

  const handleAnswerChange = (questionIndex: number, answerId: string, value?: any) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionIndex]: value !== undefined ? value : answerId,
    }));
  };

  const handleNext = async () => {
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      setIsSubmitting(true);
      try {
        // Call completion callback with answers
        if (onComplete) {
          await onComplete(selectedAnswers);
        }
        setShowResults(true);
      } catch (error) {
        console.error('Error completing survey:', error);
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
    if (questionIndex >= questions.length) return false;
    
    const question = questions[questionIndex];
    const answers = selectedAnswers[questionIndex];

    if (!answers) return false;

    switch (question.Question_type) {
      case 'text_input':
        const options = question.Question_data as any[];
        return options?.every((option) => {
          if (option.required) {
            const textAnswers = answers as Record<string, string>;
            return textAnswers[option.id] && textAnswers[option.id].trim() !== '';
          }
          return true;
        }) || false;
      case 'multiple_choice':
        return Array.isArray(answers) && answers.length > 0;
      case 'single_option':
        return answers !== undefined && answers !== null;
      case 'sub_form':
        const subQuestions = question.Question_data as Question[];
        const subAnswers = answers as Record<number, any>;
        return subQuestions?.every((_, subIndex) => {
          return subAnswers[subIndex] !== undefined;
        }) || false;
      default:
        return true;
    }
  };

  if (!isOpen) return null;

  const currentQuestion = questions[currentStep];

  if (showResults) {
    return (
      <div className="fixed inset-0 z-50 flex">
        {/* Left half - Survey Results */}
        <div className="w-1/2 bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] flex items-center justify-center p-6">
          <div className="max-w-md w-full">
            <div className="bg-[color:var(--background)]/95 rounded-2xl shadow-2xl border border-[color:var(--border)]/50 backdrop-blur-sm p-8 text-center">
              <div className="mb-6">
                <div className="inline-flex items-center space-x-2 bg-[color:var(--feature-green)] text-[color:var(--feature-green-text)] px-4 py-2 rounded-full text-sm font-medium mb-4 shadow-lg">
                  <Check className="w-4 h-4" />
                  <span>{t('survey.results.completed')}</span>
                </div>
                
                <h2 className="text-2xl font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent mb-4">
                  {t('survey.results.title')}
                </h2>
                
                <p className="text-[color:var(--muted-foreground)] mb-6">
                  {t('survey.results.description')}
                </p>

                {/* Success animation */}
                <div className="relative mb-6">
                  <div className="w-16 h-16 mx-auto bg-[color:var(--feature-green)] rounded-full flex items-center justify-center shadow-lg">
                    <Check className="w-8 h-8 text-[color:var(--feature-green-text)]" />
                  </div>
                  <div className="absolute inset-0 w-16 h-16 mx-auto bg-[color:var(--feature-green)] rounded-full animate-ping opacity-20"></div>
                </div>
              </div>

              <button
                onClick={onClose}
                className="w-full px-6 py-3 bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>

        {/* Right half - Overlay to prevent interaction with chat */}
        <div className="w-1/2 bg-black/20 backdrop-blur-sm" onClick={onClose} />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Left half - Survey Form */}
      <div className="w-1/2 bg-gradient-to-br from-[color:var(--gradient-bg-from)] via-[color:var(--gradient-bg-via)] to-[color:var(--gradient-bg-to)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[color:var(--border)]/20 bg-[color:var(--background)]/10 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[color:var(--feature-blue)] rounded-lg flex items-center justify-center">
              <FileText className="w-4 h-4 text-[color:var(--feature-blue-text)]" />
            </div>
            <h2 className="text-lg font-semibold text-[color:var(--foreground)]">{title}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[color:var(--muted)] rounded-lg transition-colors duration-200"
          >
            <X className="w-5 h-5 text-[color:var(--muted-foreground)]" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-hidden flex flex-col">
          <div className="bg-[color:var(--background)]/95 rounded-2xl shadow-xl border border-[color:var(--border)]/50 backdrop-blur-sm p-6 h-full flex flex-col">
            {questions.length > 0 && (
              <>
                {/* Progress Stepper */}
                <div className="mb-6">
                  <AnimatedStepper 
                    currentStep={currentStep}
                    totalSteps={questions.length}
                    questions={questions}
                  />
                </div>

                {/* Question Header */}
                <div className="text-center mb-6 flex-shrink-0">
                  <div className="inline-flex items-center space-x-2 bg-[color:var(--feature-blue)] text-[color:var(--feature-blue-text)] px-3 py-1 rounded-full text-sm font-medium mb-3">
                    <span>
                      Question {currentStep + 1} of {questions.length}
                    </span>
                    <span>•</span>
                    <span className="capitalize">
                      {currentQuestion?.Question_type === 'single_option' ? t('survey.type.single_option') : 
                        currentQuestion?.Question_type === 'multiple_choice' ? t('survey.type.multiple_choice') :
                        currentQuestion?.Question_type === 'text_input' ? t('survey.type.text_input') :
                        currentQuestion?.Question_type === 'sub_form' ? t('survey.type.sub_form') :
                        t('survey.type.unknown_type')}
                    </span>
                  </div>
                  
                  <h3 className="text-xl font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent mb-2">
                    {currentQuestion?.Question}
                  </h3>
                  
                  {currentQuestion?.subtitle && (
                    <p className="text-[color:var(--muted-foreground)]">
                      {currentQuestion.subtitle}
                    </p>
                  )}
                </div>

                {/* Question Content */}
                <div className="flex-1 overflow-y-auto mb-6 min-h-0">
                  {currentQuestion && (
                    <QuestionRenderer
                      question={currentQuestion}
                      questionIndex={currentStep}
                      selectedAnswers={selectedAnswers}
                      onAnswerChange={handleAnswerChange}
                    />
                  )}
                </div>

                {/* Navigation */}
                <div className="flex justify-between items-center gap-4 flex-shrink-0">
                  <button
                    onClick={handleBack}
                    disabled={currentStep === 0}
                    className={`
                      flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-300
                      ${
                        currentStep === 0
                          ? 'text-[color:var(--muted-foreground)] cursor-not-allowed bg-[color:var(--muted)]/30'
                          : 'text-[color:var(--foreground)] hover:bg-[color:var(--muted)] border border-[color:var(--border)]'
                      }
                    `}
                  >
                    <span>{t('survey.previous')}</span>
                  </button>

                  <button
                    onClick={handleNext}
                    disabled={!isQuestionAnswered(currentStep) || isSubmitting}
                    className={`
                      flex items-center space-x-2 px-6 py-2 rounded-lg font-medium transition-all duration-300 transform
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
                        : currentStep === questions.length - 1
                        ? t('survey.complete')
                        : t('survey.continue')
                      }
                    </span>
                    {!isSubmitting && <ArrowRight className="w-4 h-4" />}
                    {isSubmitting && (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    )}
                  </button>
                </div>

                {/* Progress Bar */}
                <div className="mt-4 space-y-2 flex-shrink-0">
                  <div className="flex justify-between text-xs font-medium text-[color:var(--muted-foreground)]">
                    <span>Progress</span>
                    <span>{Math.round(progress)}% Complete</span>
                  </div>
                  <div className="w-full bg-[color:var(--muted)] rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] h-full rounded-full transition-all duration-700 ease-out relative"
                      style={{ width: `${progress}%` }}
                    >
                      <div className="absolute inset-0 bg-white/20 rounded-full animate-pulse"></div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {questions.length === 0 && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <FileText className="w-12 h-12 text-[color:var(--muted-foreground)] mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-[color:var(--foreground)] mb-2">
                    {t('survey.noQuestions')}
                  </h3>
                  <p className="text-[color:var(--muted-foreground)] text-sm">
                    {t('survey.waitingForData')}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right half - Overlay to prevent interaction with chat */}
      <div className="w-1/2 bg-black/20 backdrop-blur-sm" onClick={onClose} />
    </div>
  );
}