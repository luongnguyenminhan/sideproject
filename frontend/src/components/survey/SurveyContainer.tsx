/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState } from 'react';
import { ArrowRight, Check, ChevronLeft } from 'lucide-react';
import { Question, QuestionOption } from '@/types/question.types';
import { useTranslation } from '@/contexts/TranslationContext';
import QuestionRenderer from './QuestionRenderer';
import { submitSurveyResponse } from '@/apis/questionApi';

interface SurveyContainerProps {
  questions: Question[];
}

const SurveyContainer: React.FC<SurveyContainerProps> = ({ questions }) => {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, any>>({});
  const [showResults, setShowResults] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const progress = ((currentStep + 1) / questions.length) * 100;

  const handleAnswerChange = (questionIndex: number, answerId: string, value?: any) => {
    setSelectedAnswers({
      ...selectedAnswers,
      [questionIndex]: value !== undefined ? value : answerId,
    });
  };

  const handleNext = async () => {
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      setIsSubmitting(true);
      try {
        await submitSurveyResponse(selectedAnswers);
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
    const question = questions[questionIndex];
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

  if (showResults) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-[color:var(--background)] rounded-3xl shadow-2xl border border-[color:var(--border)] p-8 md:p-12 text-center">
          <div className="mb-8">
            <div className="inline-flex items-center space-x-2 bg-[color:var(--feature-green)] text-[color:var(--feature-green-text)] px-6 py-3 rounded-full text-sm font-medium mb-6 shadow-lg">
              <Check className="w-5 h-5" />
              <span>{t('survey.results.completed') || 'Survey Completed'}</span>
            </div>
            
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent mb-6">
              {t('survey.results.title') || 'Thank You!'}
            </h1>
            
            <p className="text-xl text-[color:var(--muted-foreground)] max-w-2xl mx-auto mb-8">
              {t('survey.results.description') || 'Your responses have been submitted successfully. We appreciate your time and feedback.'}
            </p>

            {/* Success animation */}
            <div className="relative mb-8">
              <div className="w-24 h-24 mx-auto bg-[color:var(--feature-green)] rounded-full flex items-center justify-center shadow-lg">
                <Check className="w-12 h-12 text-[color:var(--feature-green-text)]" />
              </div>
              <div className="absolute inset-0 w-24 h-24 mx-auto bg-[color:var(--feature-green)] rounded-full animate-ping opacity-20"></div>
            </div>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => {
                setShowResults(false);
                setCurrentStep(0);
                setSelectedAnswers({});
              }}
              className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1"
            >
              {t('survey.results.retake') || 'Retake Survey'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentStep];

  return (
    <div className="w-full max-w-4xl mx-auto h-full flex flex-col">
      <div className="bg-[color:var(--background)] rounded-3xl shadow-2xl border border-[color:var(--border)] p-4 md:p-8 h-full flex flex-col max-h-[calc(100vh-120px)] overflow-hidden">
        {/* Progress Indicator */}
        <div className="flex justify-center mb-6 md:mb-8 flex-shrink-0">
          <div className="flex items-center space-x-2 md:space-x-4">
            {questions.map((_, index) => (
              <div key={index} className="flex items-center">
                <div
                  className={`
                    w-8 h-8 md:w-12 md:h-12 rounded-full flex items-center justify-center font-semibold text-xs md:text-sm transition-all duration-300
                    ${
                      index < currentStep
                        ? 'bg-[color:var(--feature-green)] text-[color:var(--feature-green-text)] shadow-lg'
                        : index === currentStep
                        ? 'bg-[color:var(--primary)] text-[color:var(--primary-foreground)] ring-4 ring-[color:var(--primary)]/20 shadow-lg'
                        : 'bg-[color:var(--muted)] text-[color:var(--muted-foreground)]'
                    }
                  `}
                >
                  {index < currentStep ? (
                    <Check className="w-4 h-4 md:w-6 md:h-6" />
                  ) : (
                    index + 1
                  )}
                </div>
                {index < questions.length - 1 && (
                  <div
                    className={`
                      w-8 md:w-16 h-1 mx-1 md:mx-2 rounded-full transition-all duration-300
                      ${index < currentStep ? 'bg-[color:var(--feature-green)]' : 'bg-[color:var(--muted)]'}
                    `}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Question Header */}
        <div className="text-center mb-4 md:mb-6 flex-shrink-0">
          <div className="inline-flex items-center space-x-2 bg-[color:var(--feature-blue)] text-[color:var(--feature-blue-text)] px-4 py-2 rounded-full text-sm font-medium mb-4">
            <span>
              Question {currentStep + 1} of {questions.length}
            </span>
            <span>•</span>
            <span className="capitalize">
              {currentQuestion.Question_type.replace('_', ' ')}
            </span>
          </div>
          
          <h1 className="text-xl md:text-3xl font-bold bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)] bg-clip-text text-transparent mb-3">
            {currentQuestion.Question}
          </h1>
          
          {currentQuestion.subtitle && (
            <p className="text-base md:text-lg text-[color:var(--muted-foreground)] max-w-3xl mx-auto">
              {currentQuestion.subtitle}
            </p>
          )}
        </div>

        {/* Question Content */}
        <div className="flex-1 overflow-y-auto mb-4 md:mb-6 min-h-0">
          <QuestionRenderer
            question={currentQuestion}
            questionIndex={currentStep}
            selectedAnswers={selectedAnswers}
            onAnswerChange={handleAnswerChange}
          />
        </div>

        {/* Navigation */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-4 flex-shrink-0">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className={`
              flex items-center space-x-2 px-4 md:px-6 py-3 rounded-xl font-semibold transition-all duration-300 w-full md:w-auto justify-center md:justify-start
              ${
                currentStep === 0
                  ? 'text-[color:var(--muted-foreground)] cursor-not-allowed bg-[color:var(--muted)]/30'
                  : 'text-[color:var(--foreground)] hover:bg-[color:var(--muted)] border border-[color:var(--border)]'
              }
            `}
          >
            <ChevronLeft className="w-5 h-5" />
            <span>Previous</span>
          </button>

          <button
            onClick={handleNext}
            disabled={!isQuestionAnswered(currentStep) || isSubmitting}
            className={`
              flex items-center space-x-2 px-6 md:px-8 py-3 md:py-4 rounded-xl font-semibold transition-all duration-300 transform w-full md:w-auto justify-center
              ${
                isQuestionAnswered(currentStep) && !isSubmitting
                  ? 'bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-white hover:shadow-lg hover:-translate-y-1'
                  : 'bg-[color:var(--muted)] text-[color:var(--muted-foreground)] cursor-not-allowed'
              }
            `}
          >
            <span>
              {isSubmitting 
                ? 'Submitting...'
                : currentStep === questions.length - 1 
                ? 'Complete Survey' 
                : 'Continue'
              }
            </span>
            {!isSubmitting && <ArrowRight className="w-5 h-5" />}
            {isSubmitting && (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
          </button>
        </div>

        {/* Progress Bar */}
        <div className="space-y-3 flex-shrink-0">
          <div className="flex justify-between text-sm font-medium text-[color:var(--muted-foreground)]">
            <span>Progress</span>
            <span>{Math.round(progress)}% Complete</span>
          </div>
          <div className="w-full bg-[color:var(--muted)] rounded-full h-3 md:h-4 overflow-hidden">
            <div
              className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] h-full rounded-full transition-all duration-700 ease-out relative"
              style={{ width: `${progress}%` }}
            >
              <div className="absolute inset-0 bg-white/20 rounded-full animate-pulse"></div>
            </div>
          </div>
          <div className="text-center text-sm text-[color:var(--muted-foreground)]">
            Step {currentStep + 1} of {questions.length}
          </div>
        </div>
        </div>
      </div>
    );
};

export default SurveyContainer;
