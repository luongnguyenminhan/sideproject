import axiosInstance from './axiosInstance';
import { handleApiCall, handleApiCallNoData } from '@/utils/apiHandler';
import { AxiosResponse } from 'axios';
import { 
  CreateAgentPayload, 
  UpdateAgentPayload,
  CreateAgentConfigPayload,
  UpdateAgentConfigPayload,
  AgentChatPayload,
  ClearAgentMemoryPayload,
  TestAgentPayload,
  CreateDefaultAgentPayload,
  CreateCustomAgentPayload,
  SearchAgentsParams,
  Agent, 
  AgentConfig,
  AgentType,
  AgentCapabilities,
  AgentMemory,
  AgentChatResponse,
  AgentTestResponse,
  AgentStatsResponse,
  DefaultConfigTemplate,
  AvailableModelsResponse 
} from '@/types/agentTypes';
import { CommonResponse } from '@/types/common.type';

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Wrapper for API calls that should never return null
 * Throws an error if the API returns null data
 */
async function handleRequiredApiCall<T>(
  apiCall: () => Promise<AxiosResponse<CommonResponse<T>>>
): Promise<T> {
  const result = await handleApiCall(apiCall);
  if (result === null) {
    throw new Error('Unexpected null response from server');
  }
  return result;
}

// =============================================================================
// AGENT CRUD OPERATIONS
// =============================================================================

// Create new agent
export const createAgent = async (payload: CreateAgentPayload): Promise<Agent> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.post<CommonResponse<Agent>>('/agents/', payload)
  );
};

// Update agent
export const updateAgent = async (
  agent_id: string, 
  payload: UpdateAgentPayload
): Promise<Agent> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.put<CommonResponse<Agent>>(`/agents/${agent_id}`, payload)
  );
};

// Delete agent
export const deleteAgent = async (agent_id: string): Promise<void> => {
  return handleApiCallNoData(async () => 
    axiosInstance.delete<CommonResponse<null>>(`/agents/${agent_id}`)
  );
};

// Toggle agent active status
export const toggleAgent = async (agent_id: string): Promise<Agent> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.post<CommonResponse<Agent>>(`/agents/${agent_id}/toggle`)
  );
};

// Get agent by ID
export const getAgentById = async (agent_id: string): Promise<Agent> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.get<CommonResponse<Agent>>(`/agents/${agent_id}`)
  );
};

// List user's agents with search and filtering
export const getUserAgents = async (params?: SearchAgentsParams): Promise<{
  items: Agent[];
  total: number;
  page: number;
  page_size: number;
}> => {
  const data = await handleApiCall(async () => 
    axiosInstance.get<CommonResponse<{
      items: Agent[];
      paging: {
        total: number;
        page: number;
        page_size: number;
      };
    }>>('/agents/', { params })
  );

  return {
    items: data?.items || [],
    total: data?.paging?.total || 0,
    page: data?.paging?.page || 1,
    page_size: data?.paging?.page_size || 10,
  };
};

// =============================================================================
// AGENT CONFIGURATION OPERATIONS
// =============================================================================

// Create agent configuration
export const createAgentConfig = async (payload: CreateAgentConfigPayload): Promise<AgentConfig> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.post<CommonResponse<AgentConfig>>('/agents/configs/', payload)
  );
};

// Update agent configuration
export const updateAgentConfig = async (
  config_id: string, 
  payload: UpdateAgentConfigPayload
): Promise<AgentConfig> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.put<CommonResponse<AgentConfig>>(`/agents/configs/${config_id}`, payload)
  );
};

// Get agent configuration by ID
export const getAgentConfig = async (config_id: string): Promise<AgentConfig> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.get<CommonResponse<AgentConfig>>(`/agents/configs/${config_id}`)
  );
};

// List agent configurations
export const getAgentConfigs = async (params?: {
  page?: number;
  page_size?: number;
  agent_type?: string;
}): Promise<{
  items: AgentConfig[];
  total: number;
}> => {
  const data = await handleApiCall(async () => 
    axiosInstance.get<CommonResponse<{
      items: AgentConfig[];
      paging: { total: number };
    }>>('/agents/configs/', { params })
  );

  return {
    items: data?.items || [],
    total: data?.paging?.total || 0,
  };
};

// Delete agent configuration
export const deleteAgentConfig = async (config_id: string): Promise<void> => {
  return handleApiCallNoData(async () => 
    axiosInstance.delete<CommonResponse<null>>(`/agents/configs/${config_id}`)
  );
};

// =============================================================================
// AGENT CHAT AND EXECUTION
// =============================================================================

// Send chat message to agent
export const chatWithAgent = async (
  agent_id: string, 
  payload: AgentChatPayload
): Promise<AgentChatResponse> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.post<CommonResponse<AgentChatResponse>>(`/agents/${agent_id}/chat`, payload)
  );
};

// Test agent with a message
export const testAgent = async (
  agent_id: string, 
  payload: TestAgentPayload
): Promise<AgentTestResponse> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.post<CommonResponse<AgentTestResponse>>(`/agents/${agent_id}/test`, payload)
  );
};

// =============================================================================
// AGENT MEMORY OPERATIONS
// =============================================================================

// Get agent memory
export const getAgentMemory = async (
  agent_id: string,
  params?: {
    memory_type?: string;
    conversation_id?: string;
    page?: number;
    page_size?: number;
  }
): Promise<{
  items: AgentMemory[];
  total: number;
}> => {
  const data = await handleApiCall(async () => 
    axiosInstance.get<CommonResponse<{
      items: AgentMemory[];
      paging: { total: number };
    }>>(`/agents/${agent_id}/memory`, { params })
  );

  return {
    items: data?.items || [],
    total: data?.paging?.total || 0,
  };
};

// Clear agent memory
export const clearAgentMemory = async (
  agent_id: string, 
  payload?: ClearAgentMemoryPayload
): Promise<void> => {
  return handleApiCallNoData(async () => 
    axiosInstance.post<CommonResponse<null>>(`/agents/${agent_id}/memory/clear`, payload || {})
  );
};

// =============================================================================
// AGENT CAPABILITIES AND INFO
// =============================================================================

// Get agent capabilities
export const getAgentCapabilities = async (agent_id: string): Promise<AgentCapabilities> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.get<CommonResponse<AgentCapabilities>>(`/agents/${agent_id}/capabilities`)
  );
};

// Get agent statistics
export const getAgentStats = async (agent_id: string): Promise<AgentStatsResponse> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.get<CommonResponse<AgentStatsResponse>>(`/agents/${agent_id}/stats`)
  );
};

// =============================================================================
// AGENT TEMPLATES AND DEFAULTS
// =============================================================================

// Create default agent for specific type
export const createDefaultAgent = async (payload: CreateDefaultAgentPayload): Promise<Agent> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.post<CommonResponse<Agent>>('/agents/create-default', payload)
  );
};

// Create custom agent with configuration
export const createCustomAgent = async (payload: CreateCustomAgentPayload): Promise<Agent> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.post<CommonResponse<Agent>>('/agents/create-custom', payload)
  );
};

// Get default configuration template for agent type
export const getDefaultTemplate = async (agent_type: AgentType): Promise<DefaultConfigTemplate> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.get<CommonResponse<DefaultConfigTemplate>>(`/agents/templates/${agent_type}`)
  );
};

// =============================================================================
// MODELS AND PROVIDERS
// =============================================================================

// Get available models from all providers
export const getAvailableModels = async (): Promise<AvailableModelsResponse> => {
  return handleRequiredApiCall(async () => 
    axiosInstance.get<CommonResponse<AvailableModelsResponse>>('/agents/models/available')
  );
};

// =============================================================================
// LEGACY FUNCTIONS (for backward compatibility - will be deprecated)
// =============================================================================

/**
 * @deprecated Use createDefaultAgent instead
 * Legacy function for creating default agents with old signature
 */
export const createDefaultAgentLegacy = async (
  agent_type: AgentType, 
  custom_name?: string
): Promise<Agent> => {
  return createDefaultAgent({ agent_type, custom_name });
};

// =============================================================================
// USAGE EXAMPLES AND DOCUMENTATION
// =============================================================================

/*
Example usage:

// 1. Create a new chat agent
const newAgent = await createAgent({
  name: "My Chat Assistant",
  description: "A helpful chat assistant",
  agent_type: AgentType.CHAT
});

// 2. Update an agent
const updatedAgent = await updateAgent(agent.id, {
  name: "Updated Agent Name",
  is_active: true
});

// 3. Chat with an agent
const chatResponse = await chatWithAgent(agent.id, {
  message: "Hello, how can you help me?",
  conversation_id: "conv-123",
  streaming: false
});

// 4. Get agent memory
const memory = await getAgentMemory(agent.id, {
  memory_type: "conversation",
  page: 1,
  page_size: 20
});

// 5. Get available models
const models = await getAvailableModels();

// 6. Create default agent for specific type
const defaultAgent = await createDefaultAgent({
  agent_type: AgentType.ANALYSIS,
  custom_name: "My Analysis Agent"
});

// 7. Create custom agent with configuration
const customAgent = await createCustomAgent({
  name: "Custom AI Assistant",
  description: "A specialized assistant",
  config: {
    name: "Custom Config",
    agent_type: "custom",
    model_provider: ModelProvider.OPENAI,
    model_name: "gpt-4",
    temperature: 0.7,
    max_tokens: 2048,
    system_prompt: "You are a helpful assistant..."
  }
});

// 8. Get agent capabilities
const capabilities = await getAgentCapabilities(agent.id);

// 9. Test an agent
const testResult = await testAgent(agent.id, {
  test_message: "This is a test message"
});

// 10. Clear agent memory
await clearAgentMemory(agent.id, {
  memory_type: "conversation"
});

Error handling is automatically managed by the apiHandler utility.
All functions will throw appropriate ApiException errors with meaningful messages.

The following endpoints match the backend routes:
- POST /agents/ - createAgent
- GET /agents/ - getUserAgents
- GET /agents/{agent_id} - getAgentById
- PUT /agents/{agent_id} - updateAgent
- DELETE /agents/{agent_id} - deleteAgent
- POST /agents/{agent_id}/toggle - toggleAgent
- POST /agents/{agent_id}/chat - chatWithAgent
- GET /agents/{agent_id}/memory - getAgentMemory
- POST /agents/{agent_id}/memory/clear - clearAgentMemory
- POST /agents/{agent_id}/test - testAgent
- GET /agents/{agent_id}/capabilities - getAgentCapabilities
- POST /agents/create-default - createDefaultAgent
- POST /agents/create-custom - createCustomAgent
- GET /agents/models/available - getAvailableModels
- GET /agents/templates/{agent_type} - getDefaultTemplate
*/