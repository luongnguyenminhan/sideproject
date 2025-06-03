// Agent type enum matching backend AgentType
export enum AgentType {
  CHAT = 'chat',
  ANALYSIS = 'analysis', 
  TASK = 'task',
  CUSTOM = 'custom',
}

// Model provider enum for agent config
export enum ModelProvider {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
}

// Memory type enum matching backend MemoryType
export enum MemoryType {
  CONVERSATION = 'conversation',
  EPISODIC = 'episodic',
  SEMANTIC = 'semantic',
  WORKING = 'working',
  TOOL_USAGE = 'tool_usage',
  SYSTEM = 'system'
}

// Tool configuration interface
export interface ToolConfig {
  enabled_tools?: string[];
  tool_settings?: Record<string, unknown>;
  custom_tools?: Record<string, unknown>;
}

// Workflow configuration interface
export interface WorkflowConfig {
  steps?: Array<{
    name: string;
    type: string;
    config?: Record<string, unknown>;
  }>;
  conditions?: Record<string, unknown>;
  retry_config?: {
    max_retries?: number;
    backoff_factor?: number;
  };
}

// Memory configuration interface
export interface MemoryConfig {
  max_conversations?: number;
  retention_days?: number;
  auto_summarize?: boolean;
  memory_types?: MemoryType[];
}

// Create agent payload interface matching backend CreateAgentRequest
export interface CreateAgentPayload {
  name: string;
  description?: string;
  agent_type: AgentType;
  config_id?: string;
}

// Update agent payload interface matching backend UpdateAgentRequest
export interface UpdateAgentPayload {
  name?: string;
  description?: string;
  config_id?: string;
  is_active?: boolean;
}

// Create agent config payload matching backend CreateAgentConfigRequest
export interface CreateAgentConfigPayload {
  name: string;
  description?: string;
  agent_type: string;
  model_provider: ModelProvider;
  model_name: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  tools_config?: ToolConfig;
  workflow_config?: WorkflowConfig;
  memory_config?: MemoryConfig;
}

// Update agent config payload matching backend UpdateAgentConfigRequest
export interface UpdateAgentConfigPayload {
  name?: string;
  description?: string;
  model_provider?: ModelProvider;
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  tools_config?: ToolConfig;
  workflow_config?: WorkflowConfig;
  memory_config?: MemoryConfig;
}

// Agent configuration interface
export interface AgentConfig {
  id: string;
  name: string;
  description?: string;
  agent_type: string;
  model_provider: ModelProvider;
  model_name: string;
  temperature: number;
  max_tokens?: number;
  system_prompt?: string;
  tools_config?: ToolConfig;
  workflow_config?: WorkflowConfig;
  memory_config?: MemoryConfig;
  create_date: string;
  update_date: string;
}

// Agent interface matching backend AgentResponse
export interface Agent {
  id: string;
  name: string;
  description?: string;
  agent_type: AgentType;
  config_id: string;
  user_id: string;
  is_active: boolean;
  created_by: string;
  create_date: string;
  update_date: string;
  config?: AgentConfig;
}

// Agent chat request payload matching backend AgentChatRequest
export interface AgentChatPayload {
  message: string;
  conversation_id: string;
  api_key?: string;
  streaming?: boolean;
}

// Agent memory interface matching backend AgentMemoryResponse
export interface AgentMemory {
  id: string;
  agent_id: string;
  conversation_id?: string;
  memory_type: MemoryType;
  content: Record<string, unknown>;
  importance_score: number;
  session_id?: string;
  metadata?: Record<string, unknown>;
  create_date: string;
  update_date: string;
}

// Clear agent memory payload matching backend ClearAgentMemoryRequest
export interface ClearAgentMemoryPayload {
  memory_type?: string;
  conversation_id?: string;
}

// Test agent payload matching backend TestAgentRequest
export interface TestAgentPayload {
  test_message: string;
}

// Create default agent payload matching backend CreateDefaultAgentRequest
export interface CreateDefaultAgentPayload {
  agent_type: AgentType;
  custom_name?: string;
}

// Create custom agent payload matching backend CreateCustomAgentRequest
export interface CreateCustomAgentPayload {
  name: string;
  description?: string;
  config: CreateAgentConfigPayload;
}

// Search agents request matching backend SearchAgentsRequest
export interface SearchAgentsParams {
  page?: number;
  page_size?: number;
  agent_type?: AgentType;
  is_active?: boolean;
  search_term?: string;
}

// Agent chat response matching backend AgentChatResponse
export interface AgentChatResponse {
  response: string;
  conversation_id: string;
  agent_id: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

// Agent stream chunk matching backend AgentStreamChunk
export interface AgentStreamChunk {
  content: string;
  conversation_id: string;
  is_complete: boolean;
  metadata?: Record<string, unknown>;
}

// Agent test response matching backend AgentTestResponse
export interface AgentTestResponse {
  response: string;
  execution_time: number;
  token_usage?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

// Workflow validation response matching backend WorkflowValidationResponse
export interface WorkflowValidationResponse {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

// Agent stats response matching backend AgentStatsResponse
export interface AgentStatsResponse {
  total_conversations: number;
  total_messages: number;
  avg_response_time: number;
  success_rate: number;
  last_active: string;
}

// Agent capabilities interface
export interface AgentCapabilities {
  supports_streaming: boolean;
  supports_tools: boolean;
  supports_memory: boolean;
  supports_context: boolean;
  max_context_length: number;
  supported_file_types: string[];
}

// Default config template interface
export interface DefaultConfigTemplate {
  agent_type: AgentType;
  template: {
    name: string;
    description: string;
    model_provider: ModelProvider;
    model_name: string;
    temperature: number;
    max_tokens: number;
    system_prompt: string;
    tools_config: ToolConfig;
    workflow_config: WorkflowConfig;
  };
  description: string;
  recommended_use_cases: string[];
}

// Model info interface for available models
export interface ModelInfo {
  provider: string;
  models: string[];
}

// Available models response
export interface AvailableModelsResponse {
  providers: ModelInfo[];
}

// Agent creation form validation errors
export interface AgentFormErrors {
  name?: string;
  agent_type?: string;
  config_id?: string;
  general?: string;
}