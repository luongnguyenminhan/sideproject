import type { RequestSchema, FilterableRequestSchema } from './common.type'
import { Question } from './question.types'

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
// CV UPLOAD TYPES
// ============================================

export interface UploadCVRequest extends RequestSchema {
  conversation_id?: string
}

export interface PersonalInformation {
  full_name?: string
  email?: string
  phone_number?: string
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  other_url?: string[]
  address?: string
}

export interface EducationItem {
  institution_name?: string
  degree_name?: string
  major?: string
  graduation_date?: string
  gpa?: string
  relevant_courses?: string[]
  description?: string
}

export interface ExperienceItem {
  company_name?: string
  job_title?: string
  start_date?: string
  end_date?: string
  duration?: string
  responsibilities_achievements?: string[]
  location?: string
}

export interface SkillItem {
  skill_name?: string
  proficiency_level?: string
  category?: string
}

export interface ProjectItem {
  project_name?: string
  description?: string
  technologies_used?: string[]
  role?: string
  project_url?: string
  start_date?: string
  end_date?: string
}

export interface CertificateItem {
  certificate_name?: string
  issuing_organization?: string
  issue_date?: string
  expiration_date?: string
  credential_id?: string
}

export interface KeywordItem {
  keyword: string
}

export interface CharacteristicItem {
  characteristic_type?: string
  statement?: string
  evidence?: string[]
}

export interface CVAnalysisResult {
  identified_sections?: string[]
  raw_cv_content?: string
  processed_cv_text?: string
  personal_information?: PersonalInformation
  education_history?: {
    items: EducationItem[]
  }
  work_experience_history?: {
    items: ExperienceItem[]
  }
  skills_summary?: {
    items: SkillItem[]
  }
  projects?: {
    items: ProjectItem[]
  }
  certificates_and_courses?: {
    items: CertificateItem[]
  }
  interests_and_hobbies?: {
    items: unknown[]
  }
  other_sections_data?: Record<string, unknown>
  cv_summary?: string
  extracted_keywords?: {
    items: KeywordItem[]
  }
  inferred_characteristics?: CharacteristicItem[]
  keywords?: string[]
  llm_token_usage?: {
    input_tokens?: number
    output_tokens?: number
    total_tokens?: number
    price_usd?: number
  }
}

export interface UploadCVResponse {
  file_path: string
  cv_file_url: string
  extracted_text: string
  cv_analysis_result: CVAnalysisResult
  personal_info: PersonalInformation
  skills_count: number
  experience_count: number
  cv_summary: string
}

export interface GetCVMetadataRequest extends RequestSchema {
  conversation_id: string
}

export interface CVMetadataResponse {
  file_path: string
  cv_file_url: string
  extracted_text: string
  cv_analysis_result: CVAnalysisResult
  personal_info: PersonalInformation
  skills_count: number
  experience_count: number
  cv_summary: string
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
  type: 'user_message' | 'assistant_message_chunk' | 'assistant_message_complete' | 'assistant_typing' | 'error' | 'pong' | 'survey_data'
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
  data?: Question[] // For survey_data messages
  conversation_id?: string
  timestamp?: string
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
  survey_data?: Question[] // For survey questions from N8N API
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
