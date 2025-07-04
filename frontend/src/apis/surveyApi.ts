/* eslint-disable @typescript-eslint/no-explicit-any */
import axiosInstance from './axiosInstance';
import type { CommonResponse } from '@/types/common.type';

export interface SurveyResponse {
  type: 'survey_response';
  answers: Record<number | string, unknown>;
  conversation_id?: string;
  session_id?: string;
  timestamp: string;
}

export interface SubmitAnswersRequest {
  session_id?: string;
  answers: Record<string | number, unknown>;
  conversation_id?: string;
}

export interface SurveyProcessingResult {
  human_readable_response: string;
  ai_response?: {
    content: string;
    role: string;
  };
  websocket_messages?: Array<{
    content: string;
    role: 'user' | 'assistant';
  }>;
}

export const surveyAPI = {
  // Gửi survey response và nhận AI processing kết quả
  processSurveyWorkflow: async (data: SurveyResponse): Promise<CommonResponse<SurveyProcessingResult>> => {
    const response = await axiosInstance.post('/question-sessions/complete-survey-workflow', data);
    return response.data;
  },

  // Gửi survey và tự động gửi vào chat
  processAndSendToChat: async (data: SurveyResponse): Promise<CommonResponse<SurveyProcessingResult>> => {
    const response = await axiosInstance.post('/question-sessions/process-and-send-to-chat', data);
    return response.data;
  },

  // Submit survey response với session_id (khi có session cụ thể)
  submitAnswersToSession: async (data: SubmitAnswersRequest): Promise<CommonResponse<any>> => {
    const response = await axiosInstance.post('/question-sessions/submit-answers', data);
    return response.data;
  },

  // Submit survey response đơn giản (fallback - tự động tìm session)
  submitSurveyResponse: async (answers: Record<number | string, unknown>, conversationId?: string, sessionId?: string): Promise<CommonResponse<any>> => {
    // Convert to ParseSurveyResponseRequest format
    const requestData: SurveyResponse = {
      type: 'survey_response',
      answers: answers,
      conversation_id: conversationId || '',
      session_id: sessionId,
      timestamp: new Date().toISOString()
    };

    const response = await axiosInstance.post('/question-sessions/submit-response', requestData);
    return response.data;
  }
}; 