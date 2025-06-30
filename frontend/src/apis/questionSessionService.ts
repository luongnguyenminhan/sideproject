/**
 * Question Session API Service
 * Handle CRUD operations for question sessions and surveys
 */

import axiosInstance from './axiosInstance';
import { Question, QuestionOption as BaseQuestionOption } from '@/types/question.types';

// Extended types for API responses
export interface QuestionOption extends BaseQuestionOption {
  text?: string;
}

export interface Answer {
  id: string;
  question_id: string;
  question_text?: string;
  answer_data: Record<string, unknown>;
  answer_type: string;
  submitted_at?: string;
}

export interface SessionDetail {
  id: string;
  name: string;
  conversation_id: string;
  session_type: string;
  questions_data: Question[];
  session_status: string;
  start_date: string;
  completion_date?: string;
  extra_metadata?: string;
}

export interface QuestionSessionDetail {
  session: SessionDetail;
  answers: Answer[];
  followup_sessions?: SessionDetail[];
}

export interface SessionQuestions {
  session_id: string;
  session_name: string;
  session_type: string;
  questions: Question[];
  total_questions: number;
  session_status: string;
}

export interface CreateSessionRequest {
  name: string;
  conversation_id: string;
  session_type: string;
  questions_data: Question[];
  parent_session_id?: string;
  extra_metadata?: string;
}

export interface SubmitAnswersRequest {
  session_id: string;
  conversation_id?: string;
  answers: Record<string, unknown>;
}

class QuestionSessionService {
  /**
   * Get detailed question session information
   */
  async getQuestionSession(sessionId: string): Promise<QuestionSessionDetail> {
    try {
      console.log('[QuestionSessionService] Fetching session detail:', sessionId);
      const response = await axiosInstance.get(`/question-sessions/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('[QuestionSessionService] Error fetching session detail:', error);
      throw error;
    }
  }

  /**
   * Get questions data for a specific session
   */
  async getSessionQuestions(sessionId: string): Promise<SessionQuestions> {
    try {
      console.log('[QuestionSessionService] Fetching session questions:', sessionId);
      const response = await axiosInstance.get(`/question-sessions/${sessionId}/questions`);
      
      console.log('[QuestionSessionService] Raw API response:', {
        status: response.status,
        data: response.data,
        dataType: typeof response.data,
        hasDataProperty: 'data' in response.data,
        actualData: response.data.data
      });
      
      // API returns nested structure: { error_code: 0, message: "...", data: { actual_data } }
      return response.data.data || response.data;
    } catch (error) {
      console.error('[QuestionSessionService] Error fetching session questions:', error);
      throw error;
    }
  }

  /**
   * Get user's question sessions with pagination
   */
  async getUserSessions(params?: {
    conversation_id?: string;
    session_status?: string;
    session_type?: string;
    page?: number;
    page_size?: number;
    order_by?: string;
    order_direction?: string;
  }) {
    try {
      console.log('[QuestionSessionService] Fetching user sessions:', params);
      const response = await axiosInstance.get('/question-sessions', { params });
      return response.data;
    } catch (error) {
      console.error('[QuestionSessionService] Error fetching user sessions:', error);
      throw error;
    }
  }

  /**
   * Create a new question session
   */
  async createQuestionSession(request: CreateSessionRequest) {
    try {
      console.log('[QuestionSessionService] Creating session:', request);
      const response = await axiosInstance.post('/question-sessions', request);
      return response.data;
    } catch (error) {
      console.error('[QuestionSessionService] Error creating session:', error);
      throw error;
    }
  }

  /**
   * Update a question session
   */
  async updateQuestionSession(sessionId: string, updates: {
    name?: string;
    session_status?: string;
    questions_data?: Question[];
    extra_metadata?: string;
  }) {
    try {
      console.log('[QuestionSessionService] Updating session:', sessionId, updates);
      const response = await axiosInstance.put(`/question-sessions/${sessionId}`, updates);
      return response.data;
    } catch (error) {
      console.error('[QuestionSessionService] Error updating session:', error);
      throw error;
    }
  }

  /**
   * Submit answers for a question session
   */
  async submitAnswers(sessionId: string, answers: Record<string, unknown>, conversationId?: string) {
    try {
      const request: SubmitAnswersRequest = {
        session_id: sessionId,
        answers,
        conversation_id: conversationId
      };
      
      console.log('[QuestionSessionService] Submitting answers:', request);
      const response = await axiosInstance.post(`/question-sessions/${sessionId}/submit`, request);
      return response.data;
    } catch (error) {
      console.error('[QuestionSessionService] Error submitting answers:', error);
      throw error;
    }
  }

  /**
   * Get the most recent active session for a conversation
   */
  async getActiveSessionForConversation(conversationId: string) {
    try {
      console.log('[QuestionSessionService] Getting active session for conversation:', conversationId);
      const response = await axiosInstance.get(`/question-sessions/conversation/${conversationId}/active`);
      return response.data;
    } catch (error) {
      console.error('[QuestionSessionService] Error getting active session:', error);
      throw error;
    }
  }

  /**
   * Process survey response and send to chat (enhanced endpoint)
   */
  async processAndSendToChat(data: {
    type: string;
    answers: Record<number, unknown>;
    conversation_id?: string;
    timestamp?: string;
  }) {
    try {
      console.log('[QuestionSessionService] Processing survey and sending to chat:', data);
      const response = await axiosInstance.post('/question-sessions/process-and-send-to-chat', data);
      return response;
    } catch (error) {
      console.error('[QuestionSessionService] Error processing survey and sending to chat:', error);
      throw error;
    }
  }

  /**
   * Complete survey workflow (fallback endpoint)
   */
  async completeSurveyWorkflow(data: {
    type: string;
    answers: Record<number, unknown>;
    conversation_id?: string;
    timestamp?: string;
  }) {
    try {
      console.log('[QuestionSessionService] Completing survey workflow:', data);
      const response = await axiosInstance.post('/question-sessions/complete-survey-workflow', data);
      return response;
    } catch (error) {
      console.error('[QuestionSessionService] Error completing survey workflow:', error);
      throw error;
    }
  }

  /**
   * Cancel/delete a question session
   */
  async cancelQuestionSession(sessionId: string) {
    try {
      console.log('[QuestionSessionService] Cancelling session:', sessionId);
      const response = await axiosInstance.delete(`/question-sessions/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('[QuestionSessionService] Error cancelling session:', error);
      throw error;
    }
  }
}

export const questionSessionService = new QuestionSessionService();
export default questionSessionService;
