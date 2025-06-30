/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useCallback } from 'react';
import { questionSessionService, SessionQuestions } from '@/apis/questionSessionService';

export interface UseSurveyQuestionsReturn {
  questions: SessionQuestions | null;
  loading: boolean;
  error: string | null;
  fetchQuestions: (sessionId: string) => Promise<void>;
  clearQuestions: () => void;
}

export const useSurveyQuestions = (): UseSurveyQuestionsReturn => {
  const [questions, setQuestions] = useState<SessionQuestions | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuestions = useCallback(async (sessionId: string) => {
    if (!sessionId) {
      setError('Session ID is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('[useSurveyQuestions] Fetching questions for session:', sessionId);
      const response = await questionSessionService.getSessionQuestions(sessionId);
      
      console.log('[useSurveyQuestions] Questions fetched successfully:', response);
      setQuestions(response);
    } catch (err: any) {
      console.error('[useSurveyQuestions] Error fetching questions:', err);
      setError(err.message || 'Failed to fetch survey questions');
    } finally {
      setLoading(false);
    }
  }, []);

  const clearQuestions = useCallback(() => {
    setQuestions(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    questions,
    loading,
    error,
    fetchQuestions,
    clearQuestions,
  };
}; 