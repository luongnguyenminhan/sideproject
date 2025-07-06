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
  UploadFileResponse,
  UploadCVResponse,
  CVMetadataResponse,
  ChatHistory,
  WebSocketOptions,
  WebSocketResponse
} from '@/types/chat.type'
import type { CommonResponse, Pagination, ApiResponse } from '@/types/common.type'

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
  // CV MANAGEMENT
  // ============================================
  
  async uploadCV(file: File, conversationId?: string) {
    const formData = new FormData()
    formData.append('file', file)
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }

    return handleApiCall<UploadCVResponse>(() =>
      axiosInstance.post<CommonResponse<UploadCVResponse>>('/chat/upload-cv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
    )
  }

  async getCVMetadata(conversationId: string) {
    return handleApiCall<CVMetadataResponse>(() =>
      axiosInstance.get<CommonResponse<CVMetadataResponse>>(`/chat/conversation/${conversationId}/cv-metadata`)
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
  
  // WebSocket v2 connection for n8n integration
  createWebSocketV2Connection(conversationId: string, token: string, authorizationToken?: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const basePath = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('http://', '').replace('https://', '').replace('/api', '').replace('/v1', '') || 'localhost:8000';

    // Build query parameters
    const params = new URLSearchParams();
    params.append('token', token);
    
    // Add authorization token if available
    if (authorizationToken) {
      params.append('authorization_token', authorizationToken);
    }

    // WebSocket v2 route: /api/v1/chat/v2/ws/{conversation_id}
    return `${protocol}//${basePath}/api/v2/chat/ws/${conversationId}?${params.toString()}`;
  }

  // Get chat history for n8n context
  async getChatHistory(conversationId: string, limit: number = 10, page: number = 1): Promise<ApiResponse<ChatHistory>> {
    const response = await axiosInstance.get(`/chat/conversation/${conversationId}/history`, {
      params: { limit, page }
    });
    return response.data;
  }
}

const chatApi = new ChatApi()
export default chatApi

// WebSocket v2 Class for n8n integration
export class ChatWebSocketV2 {
  private ws: WebSocket | null = null;
  private url: string;
  private options: WebSocketOptions;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: NodeJS.Timeout | null = null;
  private isManualClose = false;
  private isConnecting = false;

  constructor(options: WebSocketOptions) {
    this.options = options;
    this.url = chatApi.createWebSocketV2Connection(
      options.conversationId, 
      options.token, 
      options.authorizationToken
    );
  }

  async connect(): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;
    
    try {
      console.log(`[ChatWebSocketV2] Connecting to: ${this.url}`);
      
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = (event) => {
        console.log('[ChatWebSocketV2] Connection opened');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.startPingInterval();
        
        if (this.options.onOpen) {
          this.options.onOpen(event);
        }
      };

      this.ws.onmessage = (event) => {
        try {
          console.log('[ChatWebSocketV2] Raw message received:', event.data);
          const data: WebSocketResponse = JSON.parse(event.data);
          console.log('[ChatWebSocketV2] Parsed message:', data);
          
          if (this.options.onMessage) {
            this.options.onMessage(data);
          }
        } catch (error) {
          console.error('[ChatWebSocketV2] Error parsing message:', error);
          console.error('[ChatWebSocketV2] Raw message that failed:', event.data);
        }
      };

      this.ws.onclose = (event) => {
        console.log(`[ChatWebSocketV2] Connection closed. Code: ${event.code}, Reason: ${event.reason}`);
        this.isConnecting = false;
        this.stopPingInterval();
        
        if (this.options.onClose) {
          this.options.onClose(event);
        }

        // Auto-reconnect if not manually closed
        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (event) => {
        console.error('[ChatWebSocketV2] WebSocket error:', event);
        this.isConnecting = false;
        
        if (this.options.onError) {
          this.options.onError(event);
        }
      };

    } catch (error) {
      console.error('[ChatWebSocketV2] Failed to create WebSocket connection:', error);
      this.isConnecting = false;
      throw error;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`[ChatWebSocketV2] Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isManualClose) {
        this.connect().catch(error => {
          console.error('[ChatWebSocketV2] Reconnect attempt failed:', error);
        });
      }
    }, delay);
  }

  private startPingInterval(): void {
    this.stopPingInterval();
    
    // Send ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendPing();
      }
    }, 30000);
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  sendMessage(content: string, apiKey?: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('[ChatWebSocketV2] Cannot send message: WebSocket not connected');
      return;
    }

    const message = {
      type: 'chat_message',
      content: content.trim(),
      ...(apiKey && { api_key: apiKey })
    };

    console.log('[ChatWebSocketV2] Sending message:', { type: message.type, contentLength: content.length });
    this.ws.send(JSON.stringify(message));
  }

  sendPing(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const pingMessage = {
      type: 'ping'
    };

    console.log('[ChatWebSocketV2] Sending ping');
    this.ws.send(JSON.stringify(pingMessage));
  }

  close(): void {
    console.log('[ChatWebSocketV2] Manually closing connection');
    this.isManualClose = true;
    this.stopPingInterval();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual close');
      this.ws = null;
    }
  }

  getConnectionState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED;
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  updateToken(newToken: string, newAuthorizationToken?: string): void {
    console.log('[ChatWebSocketV2] Updating tokens and reconnecting');
    this.options.token = newToken;
    if (newAuthorizationToken !== undefined) {
      this.options.authorizationToken = newAuthorizationToken;
    }
    this.url = chatApi.createWebSocketV2Connection(
      this.options.conversationId, 
      newToken, 
      newAuthorizationToken
    );
    
    // Reconnect with new tokens
    this.close();
    this.isManualClose = false;
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('[ChatWebSocketV2] Failed to reconnect with new tokens:', error);
      });
    }, 1000);
  }
}

// Helper function to create WebSocket v2 connection
export function createChatWebSocketV2(options: WebSocketOptions): ChatWebSocketV2 {
  return new ChatWebSocketV2(options);
}
