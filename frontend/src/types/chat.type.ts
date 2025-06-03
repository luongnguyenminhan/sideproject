import type { RequestSchema, FilterableRequestSchema } from './common.type'

// ============================================
// MESSAGE TYPES
// ============================================

export interface MessageResponse {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' 
  content: string
  timestamp: string
  model_used?: string
  tokens_used?: string
  response_time_ms?: string
  file_attachments: string[]
}

export interface MessageListRequest extends FilterableRequestSchema {
  before_message_id?: string
  limit?: number
}

export interface SendMessageRequest extends RequestSchema {
  conversation_id: string
  content: string
  file_ids?: string[]
  api_key?: string
}

export interface SendMessageResponse {
  user_message: MessageResponse
  ai_message: MessageResponse
}

// ============================================
// CONVERSATION TYPES
// ============================================

export interface ConversationResponse {
  id: string
  name: string
  message_count: number
  last_activity: string
  create_date: string
  update_date?: string
  system_prompt?: string
}

export interface ConversationListRequest extends FilterableRequestSchema {
  search?: string
  order_by?: string
  order_direction?: 'asc' | 'desc'
}

export interface CreateConversationRequest extends RequestSchema {
  name: string
  initial_message?: string
  system_prompt?: string
}

export interface UpdateConversationRequest extends RequestSchema {
  name?: string
  system_prompt?: string
}

// ============================================
// FILE TYPES
// ============================================

export interface FileResponse {
  id: string
  name: string
  original_name: string
  size: number
  type: string
  upload_date: string
  download_url: string
}

export interface UploadFileResponse {
  uploaded_files: FileResponse[]
  failed_files: string[]
}

export interface FileListRequest extends FilterableRequestSchema {
  file_type?: string
  search?: string
}


// ============================================
// WEBSOCKET TYPES
// ============================================

export interface WebSocketTokenRequest extends RequestSchema {
  conversation_id?: string
}

export interface WebSocketTokenResponse {
  token: string
  expires_in: number
}

export interface WebSocketOptions {
  conversationId: string
  token: string
  onMessage?: (message: WebSocketResponse) => void
  onError?: (error: Event) => void
  onClose?: (event: CloseEvent) => void
  onOpen?: (event: Event) => void
}

export interface WebSocketResponse {
  type: 'user_message' | 'assistant_message_chunk' | 'assistant_message_complete' | 'assistant_typing' | 'error' | 'pong'
  message?: {
    id?: string
    content: string
    role?: string
    timestamp?: string
    model_used?: string
    response_time_ms?: string
  }
  chunk?: string
  is_final?: boolean
  status?: boolean
  error?: string
}

export interface ChatWebSocketMessage extends RequestSchema {
  type: 'chat_message'
  content: string
  api_key?: string
}

export interface PingWebSocketMessage extends RequestSchema {
  type: 'ping'
}

export type WebSocketMessage = ChatWebSocketMessage | PingWebSocketMessage

// ============================================
// STATISTICS TYPES
// ============================================

export interface ConversationStatsResponse {
  total_messages: number
  user_messages: number
  assistant_messages: number
  total_tokens_used: number
  total_cost: number
  avg_response_time_ms: number
  most_used_model?: string
  first_message_date?: string
  last_activity_date?: string
}

// ============================================
// UI STATE TYPES FOR CHATCLIENTWRAPPER
// ============================================

export interface Conversation {
  id: string
  name: string
  messages: Message[]
  lastActivity: Date
  messageCount: number
  systemPrompt?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
  model_used?: string
  response_time_ms?: string
  file_attachments?: string[]
}

export interface UploadedFile {
  id: string
  name: string
  originalName: string
  size: number
  type: string
  uploadDate: Date
  downloadUrl?: string
}

export interface ChatState {
  conversations: Conversation[]
  activeConversationId: string | null
  messages: Message[]
  isLoading: boolean
  isTyping: boolean
  error: string | null
  uploadedFiles: UploadedFile[]
  wsToken: string | null
}

// ============================================
// HELPER FUNCTIONS FOR TYPE CONVERSION
// ============================================

export function convertToUIConversation(apiConversation: ConversationResponse): Conversation {
  return {
    id: apiConversation.id,
    name: apiConversation.name,
    messages: [], // Will be loaded separately
    lastActivity: new Date(apiConversation.last_activity),
    messageCount: apiConversation.message_count,
    systemPrompt: apiConversation.system_prompt
  }
}

export function convertToUIMessage(apiMessage: MessageResponse): Message {
  return {
    id: apiMessage.id,
    role: apiMessage.role,
    content: apiMessage.content,
    timestamp: new Date(apiMessage.timestamp),
    model_used: apiMessage.model_used,
    response_time_ms: apiMessage.response_time_ms,
    file_attachments: apiMessage.file_attachments
  }
}

export function convertToUIFile(apiFile: FileResponse): UploadedFile {
  return {
    id: apiFile.id,
    name: apiFile.name,
    originalName: apiFile.original_name,
    size: apiFile.size,
    type: apiFile.type,
    uploadDate: new Date(apiFile.upload_date),
    downloadUrl: apiFile.download_url
  }
}

// ============================================
// ERROR TYPES
// ============================================

export interface ChatError {
  code: string
  message: string
  details?: string
}
