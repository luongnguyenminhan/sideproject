import axiosInstance from './axiosInstance'
import { handleApiCall } from '@/utils/apiHandler'
import type {
  Conversation,
  ConversationListRequest,
  CreateConversationRequest,
  UpdateConversationRequest,
  SendMessageRequest,
  SendMessageResponse,
  SaveApiKeyRequest,
  ApiKey,
  ChatFile,
  FileListRequest,
  ConversationListResponse,
  FileListResponse
} from '@/types/chat.type'

class ChatApi {
  private baseUrl = '/chat'
  private conversationsUrl = '/conversations'
  private apiKeysUrl = '/api-keys'
  private filesUrl = '/files'

  // ================== Conversations ==================
  
  async getConversations(params?: ConversationListRequest): Promise<ConversationListResponse | null> {
    return handleApiCall(() => axiosInstance.get(this.conversationsUrl, { params }))
  }

  async createConversation(data: CreateConversationRequest): Promise<Conversation | null> {
    return handleApiCall(() => axiosInstance.post(this.conversationsUrl, data))
  }

  async getConversation(conversationId: string): Promise<Conversation | null> {
    return handleApiCall(() => axiosInstance.get(`${this.conversationsUrl}/${conversationId}`))
  }

  async updateConversation(conversationId: string, data: UpdateConversationRequest): Promise<Conversation | null> {
    return handleApiCall(() => axiosInstance.put(`${this.conversationsUrl}/${conversationId}`, data))
  }

  async deleteConversation(conversationId: string): Promise<{ deleted: boolean } | null> {
    return handleApiCall(() => axiosInstance.delete(`${this.conversationsUrl}/${conversationId}`))
  }

  async getConversationMessages(
    conversationId: string,
    page: number = 1,
    pageSize: number = 50,
    beforeMessageId?: string
  ): Promise<any> {
    const params = {
      page,
      page_size: pageSize,
      ...(beforeMessageId && { before_message_id: beforeMessageId })
    }
    return handleApiCall(() => 
      axiosInstance.get(`${this.conversationsUrl}/${conversationId}/messages`, { params })
    )
  }

  // ================== Chat Messages ==================
  
  async sendMessage(data: SendMessageRequest): Promise<SendMessageResponse | null> {
    return handleApiCall(() => axiosInstance.post(`${this.baseUrl}/send-message`, data))
  }

  // ================== API Keys ==================
  
  async saveApiKey(data: SaveApiKeyRequest): Promise<ApiKey | null> {
    return handleApiCall(() => axiosInstance.post(this.apiKeysUrl, data))
  }

  async getApiKeys(): Promise<ApiKey[] | null> {
    return handleApiCall(() => axiosInstance.get(this.apiKeysUrl))
  }

  async deleteApiKey(keyId: string): Promise<{ deleted: boolean } | null> {
    return handleApiCall(() => axiosInstance.delete(`${this.apiKeysUrl}/${keyId}`))
  }

  async setDefaultApiKey(keyId: string): Promise<ApiKey | null> {
    return handleApiCall(() => axiosInstance.put(`${this.apiKeysUrl}/${keyId}/set-default`))
  }

  // ================== Files ==================
  
  async uploadFiles(files: File[], conversationId?: string): Promise<ChatFile[] | null> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }

    return handleApiCall(() => 
      axiosInstance.post(`${this.filesUrl}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    )
  }

  async getFiles(params?: FileListRequest): Promise<FileListResponse | null> {
    return handleApiCall(() => axiosInstance.get(this.filesUrl, { params }))
  }

  async getFile(fileId: string): Promise<ChatFile | null> {
    return handleApiCall(() => axiosInstance.get(`${this.filesUrl}/${fileId}`))
  }

  async deleteFile(fileId: string): Promise<{ deleted: boolean } | null> {
    return handleApiCall(() => axiosInstance.delete(`${this.filesUrl}/${fileId}`))
  }

  async getFileDownloadUrl(fileId: string, expires: number = 3600): Promise<{ download_url: string; expires_in: number } | null> {
    return handleApiCall(() => axiosInstance.get(`${this.filesUrl}/${fileId}/url`, {
      params: { expires }
    }))
  }

  // Download file directly (returns blob)
  async downloadFile(fileId: string): Promise<Blob> {
    const response = await axiosInstance.get(`${this.filesUrl}/${fileId}/download`, {
      responseType: 'blob'
    })
    return response.data
  }

  // ================== File Upload with Progress ==================
  
  async uploadFilesWithProgress(
    files: File[], 
    conversationId?: string,
    onProgress?: (progress: number) => void
  ): Promise<ChatFile[] | null> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }

    return handleApiCall(() => 
      axiosInstance.post(`${this.filesUrl}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        }
      })
    )
  }
}

export default new ChatApi()
