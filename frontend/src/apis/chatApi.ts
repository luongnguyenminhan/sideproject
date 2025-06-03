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
