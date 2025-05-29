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
  ApiKeyRequest,
  ApiKeyResponse,
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
  } = {}) {
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
        `/chat/files/${fileId}/download`, 
        { params: { expires } }
      )
    )
  }

  // ============================================
  // API KEY MANAGEMENT
  // ============================================
  
  async saveApiKey(data: ApiKeyRequest) {
    return handleApiCall<ApiKeyResponse>(() =>
      axiosInstance.post<CommonResponse<ApiKeyResponse>>('/api-keys/', data)
    )
  }

  async getApiKeys() {
    return handleApiCall<ApiKeyResponse[]>(() =>
      axiosInstance.get<CommonResponse<ApiKeyResponse[]>>('/api-keys/')
    )
  }

  async deleteApiKey(keyId: string) {
    return handleApiCallNoData(() =>
      axiosInstance.delete<CommonResponse<null>>(`/api-keys/${keyId}`)
    )
  }

  async setDefaultApiKey(keyId: string) {
    return handleApiCall<ApiKeyResponse>(() =>
      axiosInstance.put<CommonResponse<ApiKeyResponse>>(`/api-keys/${keyId}/set-default`)
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
  
}

const chatApi = new ChatApi()
export default chatApi
