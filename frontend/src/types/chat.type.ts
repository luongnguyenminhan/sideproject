import { CommonResponse, FilterableRequestSchema, Pagination } from './common.type'

// Base Message interface
export interface Message {
  id: string
  conversation_id: string
  user_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  model_used?: string
  tokens_used?: string
  response_time_ms?: string
  create_date: string
  update_date: string
}

// Conversation interface
export interface Conversation {
  id: string
  name: string
  user_id: string
  message_count: number
  last_activity: string
  create_date: string
  update_date: string
}

// File interface
export interface ChatFile {
  id: string
  name: string
  original_name: string
  size: number
  formatted_size: string
  type: string
  upload_date: string
  download_count: number
  is_public: boolean
  is_image: boolean
  is_video: boolean
  is_audio: boolean
  is_document: boolean
  file_extension: string
}

// API Key interface
export interface ApiKey {
  id: string
  provider: string
  masked_key: string
  is_default: boolean
  key_name: string
  create_date: string
}

// Request interfaces
export interface SendMessageRequest {
  conversation_id: string
  content: string
  api_key?: string
}

export interface CreateConversationRequest {
  name: string
  initial_message?: string
}

export interface UpdateConversationRequest {
  name?: string
}

export interface ConversationListRequest extends FilterableRequestSchema {
  search?: string
  order_by?: string
  order_direction?: string
}

export interface SaveApiKeyRequest {
  provider: string
  api_key: string
  is_default?: boolean
  key_name?: string
}

export interface FileListRequest extends FilterableRequestSchema {
  file_type?: string
  search?: string
  conversation_id?: string
}

// Response interfaces
export interface SendMessageResponse {
  user_message: Message
  ai_message: Message
}

export interface ConversationListResponse extends Pagination<Conversation> {}

export interface FileListResponse extends Pagination<ChatFile> {}

export interface ApiKeyListResponse extends Pagination<ApiKey> {}

// WebSocket message types
export interface WebSocketMessage {
  type: string
  [key: string]: unknown
}

export interface ChatWebSocketMessage extends WebSocketMessage {
  type: 'chat_message'
  content: string
  api_key?: string
}

export interface PingWebSocketMessage extends WebSocketMessage {
  type: 'ping'
}

export interface UserMessageResponse extends WebSocketMessage {
  type: 'user_message'
  message: Message
}

export interface AssistantTypingResponse extends WebSocketMessage {
  type: 'assistant_typing'
  status: boolean
}

export interface AssistantMessageChunkResponse extends WebSocketMessage {
  type: 'assistant_message_chunk'
  chunk: string
  is_final: boolean
}

export interface AssistantMessageCompleteResponse extends WebSocketMessage {
  type: 'assistant_message_complete'
  message: Message
}

export interface ErrorWebSocketResponse extends WebSocketMessage {
  type: 'error'
  message: string
}

export interface PongWebSocketResponse extends WebSocketMessage {
  type: 'pong'
}

// Union type for all possible WebSocket responses
export type WebSocketResponse = 
  | UserMessageResponse
  | AssistantTypingResponse
  | AssistantMessageChunkResponse
  | AssistantMessageCompleteResponse
  | ErrorWebSocketResponse
  | PongWebSocketResponse

// Chat state interface for frontend
export interface ChatState {
  conversations: Conversation[]
  activeConversation: Conversation | null
  messages: Message[]
  isLoading: boolean
  isConnected: boolean
  typingStatus: boolean
  error: string | null
  files: ChatFile[]
  apiKeys: ApiKey[]
}

// WebSocket connection options
export interface WebSocketOptions {
  conversationId: string
  token: string
  onMessage?: (message: WebSocketResponse) => void
  onError?: (error: Event) => void
  onClose?: (event: CloseEvent) => void
  onOpen?: (event: Event) => void
}

// File upload progress
export interface FileUploadProgress {
  fileId: string
  fileName: string
  progress: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}

// Chat API response types
export type ConversationResponse = CommonResponse<Conversation>
export type ConversationListApiResponse = CommonResponse<ConversationListResponse>
export type SendMessageApiResponse = CommonResponse<SendMessageResponse>
export type FileListApiResponse = CommonResponse<FileListResponse>
export type FileUploadApiResponse = CommonResponse<ChatFile[]>
export type ApiKeyApiResponse = CommonResponse<ApiKey>
export type ApiKeyListApiResponse = CommonResponse<ApiKey[]>
export type DeleteResponse = CommonResponse<{ deleted: boolean }>
