/* eslint-disable @typescript-eslint/no-explicit-any */
import axiosInstance from '@/apis/axiosInstance'
import { handleApiCall, handleApiCallNoData } from '@/utils/apiHandler'
import type { 
  SendMessageRequest, 
  SendMessageResponse,
  ConversationListRequest,
  ConversationResponse,
  CreateConversationRequest,
  UpdateConversationRequest,
  MessageListRequest,
  MessageResponse,
  FileResponse,
  WebSocketTokenRequest,
  WebSocketTokenResponse,
  UploadFileResponse
} from '@/types/chat.type'
import type { CommonResponse, Pagination } from '@/types/common.type'

class ChatApi {
  // ============================================
  // CONVERSATION MANAGEMENT
  // ============================================
  
  async getConversations(params: ConversationListRequest = {}) {
    return handleApiCall<Pagination<ConversationResponse>>(() =>
      axiosInstance.get<CommonResponse<Pagination<ConversationResponse>>>('/conversations/', { params })
    )
  }

  async createConversation(data: CreateConversationRequest) {
    return handleApiCall<ConversationResponse>(() =>
      axiosInstance.post<CommonResponse<ConversationResponse>>('/conversations/', data)
    )
  }

  async getConversation(conversationId: string) {
    return handleApiCall<ConversationResponse>(() =>
      axiosInstance.get<CommonResponse<ConversationResponse>>(`/conversations/${conversationId}`)
    )
  }

  async updateConversation(conversationId: string, data: UpdateConversationRequest) {
    return handleApiCall<ConversationResponse>(() =>
      axiosInstance.put<CommonResponse<ConversationResponse>>(`/conversations/${conversationId}`, data)
    )
  }

  async deleteConversation(conversationId: string) {
    return handleApiCallNoData(() =>
      axiosInstance.delete<CommonResponse<null>>(`/conversations/${conversationId}`)
    )
  }

  // ============================================
  // MESSAGE MANAGEMENT  
  // ============================================
  
  async getConversationMessages(conversationId: string, params: MessageListRequest = {}) {
    return handleApiCall<Pagination<MessageResponse>>(() =>
      axiosInstance.get<CommonResponse<Pagination<MessageResponse>>>(
        `/conversations/${conversationId}/messages`, 
        { params }
      )
    )
  }

  async sendMessage(data: SendMessageRequest) {
    return handleApiCall<SendMessageResponse>(() =>
      axiosInstance.post<CommonResponse<SendMessageResponse>>('/chat/send-message', data)
    )
  }

  // ============================================
  // FILE MANAGEMENT
  // ============================================
  
  async uploadFiles(files: File[], conversationId?: string) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }

    return handleApiCall<UploadFileResponse>(() =>
      axiosInstance.post<CommonResponse<UploadFileResponse>>('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
    )
  }

  async getFiles(params: { 
    page?: number
    page_size?: number
    file_type?: string
    search?: string
    conversation_id?: string
  } = {}) {
    // If conversation_id is provided, use conversation-specific endpoint
    if (params.conversation_id) {
      const { conversation_id, ...otherParams } = params
      return handleApiCall<Pagination<FileResponse>>(() =>
        axiosInstance.get<CommonResponse<Pagination<FileResponse>>>(
          `/files/conversation/${conversation_id}`, 
          { params: otherParams }
        )
      )
    }
    
    return handleApiCall<Pagination<FileResponse>>(() =>
      axiosInstance.get<CommonResponse<Pagination<FileResponse>>>('/files/', { params })
    )
  }

  async deleteFile(fileId: string) {
    return handleApiCallNoData(() =>
      axiosInstance.delete<CommonResponse<null>>(`/files/${fileId}`)
    )
  }

  async getFileDownloadUrl(fileId: string, expires: number = 3600) {
    return handleApiCall<{ download_url: string; expires_in: number }>(() =>
      axiosInstance.get<CommonResponse<{ download_url: string; expires_in: number }>>(
        `/files/${fileId}/download`, 
        { params: { expires } }
      )
    )
  }

  async uploadCV(file: File, conversationId?: string) {
    const formData = new FormData()
    formData.append('file', file)
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }

    return handleApiCall<{
      file_path: string
      cv_file_url: string
      extracted_text: string
      cv_analysis_result: {
        raw_cv_content?: string
        processed_cv_text?: string
        personal_information?: {
          full_name?: string
          email?: string
          phone_number?: string
          linkedin_url?: string
          github_url?: string
          portfolio_url?: string
          other_url?: string[]
          address?: string
        }
        education_history?: {
          items: Array<{
            institution_name?: string
            degree_name?: string
            major?: string
            graduation_date?: string
            gpa?: string
            relevant_courses?: string[]
            description?: string
          }>
        }
        work_experience_history?: {
          items: Array<{
            company_name?: string
            job_title?: string
            start_date?: string
            end_date?: string
            duration?: string
            responsibilities_achievements?: string[]
            location?: string
          }>
        }
        skills_summary?: {
          items: Array<{
            skill_name?: string
            proficiency_level?: string
            category?: string
          }>
        }
        projects_showcase?: {
          items: Array<{
            project_name?: string
            description?: string
            technologies_used?: string[]
            role?: string
            project_url?: string
            start_date?: string
            end_date?: string
          }>
        }
        certificates_and_courses?: {
          items: Array<{
            certificate_name?: string
            issuing_organization?: string
            issue_date?: string
            expiration_date?: string
            credential_id?: string
          }>
        }
        cv_summary?: string
        extracted_keywords?: {
          items: Array<{ keyword: string }>
        }
        inferred_characteristics?: {
          items: Array<{
            characteristic_type?: string
            statement?: string
            evidence?: string[]
          }>
        }
        llm_token_usage?: {
          input_tokens?: number
          output_tokens?: number
          total_tokens?: number
          price_usd?: number
        }
      }
      personal_info: {
        full_name?: string
        email?: string
        phone_number?: string
        linkedin_url?: string
        github_url?: string
        portfolio_url?: string
        other_url?: string[]
        address?: string
      }
      skills_count: number
      experience_count: number
      cv_summary: string
    }>(() =>
      axiosInstance.post<CommonResponse<{
        file_path: string
        cv_file_url: string
        extracted_text: string
        cv_analysis_result: Record<string, any>
        personal_info: Record<string, any>
        skills_count: number
        experience_count: number
        cv_summary: string
      }>>('/chat/upload-cv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
    )
  }

  async getCVMetadata(conversationId: string) {
    return handleApiCall<any | null>(() =>
      axiosInstance.get<CommonResponse<any | null>>(
        `/chat/conversation/${conversationId}/cv-metadata`
      )
    )
  }

  // ============================================
  // WEBSOCKET TOKEN
  // ============================================
  
  async getWebSocketToken(data: WebSocketTokenRequest = {}) {
    return handleApiCall<WebSocketTokenResponse>(() =>
      axiosInstance.post<CommonResponse<WebSocketTokenResponse>>('/chat/websocket/token', data)
    )
  }

  // ============================================
  // AGENT MANAGEMENT (matching static folder)
  // ============================================
  
  async getCurrentAgent() {
    return handleApiCall<{ 
      id: string;
      name: string;
      description: string;
      is_active: boolean;
      model_provider: string;
      model_name: string;
      temperature: number;
      max_tokens: number;
      tools_config: {
        web_search: boolean;
        memory_retrieval: boolean;
      };
      api_provider: string;
      has_api_key: boolean;
      create_date: string;
      update_date?: string;
    }>(() =>
      axiosInstance.get<CommonResponse<{ 
        id: string;
        name: string;
        description: string;
        is_active: boolean;
        model_provider: string;
        model_name: string;
        temperature: number;
        max_tokens: number;
        default_system_prompt?: string;
        tools_config: {
          web_search: boolean;
          memory_retrieval: boolean;
        };
        api_provider: string;
        has_api_key: boolean;
        create_date: string;
        update_date?: string;
      }>>('/chat/agent')
    )
  }

  async getAvailableModels() {
    return handleApiCall<{
      providers: {
        provider: string;
        models: string[];
      }[]
    }>(() =>
      axiosInstance.get<CommonResponse<{
        providers: {
          provider: string;
          models: string[];
        }[]
      }>>('/chat/models')
    )
  }

  async updateAgentConfig(data: {
    model_provider?: string;
    model_name?: string;
    temperature?: number;
    max_tokens?: number;
    default_system_prompt?: string;
  }) {
    return handleApiCall<{ message: string }>(() =>
      axiosInstance.put<CommonResponse<{ message: string }>>('/chat/agent/config', data)
    )
  }

  async updateAgentApiKey(data: {
    api_key: string;
    api_provider?: string;
  }) {
    return handleApiCall<{ message: string }>(() =>
      axiosInstance.put<CommonResponse<{ message: string }>>('/chat/agent/api-key', data)
    )
  }

  async validateAgent() {
    return handleApiCall<{
      is_valid: boolean;
      test_response?: string;
      error_message?: string;
      execution_time_ms?: number;
    }>(() =>
      axiosInstance.post<CommonResponse<{
        is_valid: boolean;
        test_response?: string;
        error_message?: string;
        execution_time_ms?: number;
      }>>('/chat/validate', {
        test_message: "Hello, this is a test message to validate the agent configuration."
      })
    )
  }
  
}

const chatApi = new ChatApi()
export default chatApi
