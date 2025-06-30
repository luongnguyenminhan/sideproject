/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useEffect } from 'react';
import { X, FileText } from 'lucide-react';
import { Question } from '@/types/question.types';
import { useTranslation } from '@/contexts/TranslationContext';
import SurveyContainer from '../survey/SurveyContainer';

interface SurveyModalProps {
  isOpen: boolean;
  onClose: () => void;
  questions: Question[];
  onComplete?: (answers: Record<number, any>) => void;
  title?: string;
  websocket?: { isConnected: () => boolean; sendRawMessage: (message: string) => void } | null;
  conversationId?: string;
}

export function SurveyModal({ 
  isOpen, 
  onClose, 
  questions, 
  onComplete,
  title = 'Survey Form',
  websocket,
  conversationId
}: SurveyModalProps) {
  const { t } = useTranslation();

  // Reset state when modal opens/closes
  useEffect(() => {
    // State is now managed within SurveyContainer, but we can keep this for potential future use.
  }, [isOpen]);

  if (!isOpen) return null;

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
          <div className="bg-[color:var(--background)]/95 rounded-2xl shadow-xl border border-[color:var(--border)]/50 backdrop-blur-sm h-full flex flex-col overflow-hidden">
            {questions.length > 0 ? (
              <SurveyContainer
                questions={questions}
                onSurveyComplete={onComplete}
                websocket={websocket}
                conversationId={conversationId}
                isEmbedded={true}
                onClose={onClose}
              />
            ) : (
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