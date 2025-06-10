/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react-hooks/exhaustive-deps */
'use client'

import chatApi from '@/apis/chatApi'
import { Button } from '@/components/ui/button'
import { useTranslation } from '@/contexts/TranslationContext'
import {
  type ChatState,
  type Message,
  type WebSocketResponse,
  convertToUIConversation,
  convertToUIFile,
  convertToUIMessage
} from '@/types/chat.type'
import { getErrorMessage } from '@/utils/apiHandler'
import { ChatWebSocket, createChatWebSocket } from '@/utils/websocket'
import { faChevronRight, faRobot, faTimes } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { useCallback, useEffect, useState } from 'react'
import { AgentManagement } from './AgentManagement'
import { ChatInterface } from './ChatInterface'
import { ConversationSidebar } from './ConversationSidebar'
import { FileSidebar } from './FileSidebar'
import { MobileSidebar } from './MobileSidebar'
import { SystemPromptEditor } from './SystemPromptEditor'

export function ChatClientWrapper() {
  const { t } = useTranslation()
  const [state, setState] = useState<ChatState>({
    conversations: [],
    activeConversationId: null,
    messages: [],
    isLoading: false,
    isTyping: false,
    error: null,
    uploadedFiles: [],
    wsToken: null
  })

  // Enhanced state for API key management
  const [conversationFiles, setConversationFiles] = useState<Record<string, any[]>>({})
  const [, setEditingConversation] = useState<string | null>(null)
  const [fileLoadingStates, setFileLoadingStates] = useState<Record<string, boolean>>({})

  const [websocket, setWebsocket] = useState<ChatWebSocket | null>(null)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  // Agent management state
  const [currentAgent, setCurrentAgent] = useState<{
    model_name: string;
    provider: string;
    temperature: number;
    max_tokens: number;
  } | null>(null)
  const [agentStatus, setAgentStatus] = useState<'loading' | 'error' | 'success' | 'none'>('none')
  const [isAgentManagementOpen, setIsAgentManagementOpen] = useState(false)
  const [isSystemPromptEditorOpen, setIsSystemPromptEditorOpen] = useState(false)
  const [editingConversationSystemPrompt, setEditingConversationSystemPrompt] = useState<string | null>(null)

  // Sidebar collapse states
  const [isConversationSidebarCollapsed, setIsConversationSidebarCollapsed] = useState(false)
  const [isFileSidebarCollapsed, setIsFileSidebarCollapsed] = useState(false)

  // Load initial data
  useEffect(() => {
    loadConversations()
    loadFiles()
    loadCurrentAgent()
  }, [])
  
  // Load files when active conversation changes
  useEffect(() => {
    if (state.activeConversationId) {
      loadConversationFiles(state.activeConversationId)
    }
  }, [state.activeConversationId])

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketResponse) => {
    console.log('[ChatClientWrapper] Received WebSocket message:', message.type)
    
    switch (message.type) {
      case 'user_message':
        // Skip processing user messages since we already added them locally
        // This prevents duplicate user messages
        console.log('[ChatClientWrapper] Skipping user_message - already added locally')
        break

      case 'assistant_typing':
        setState(prev => ({
          ...prev,
          isTyping: message.status || false
        }))
        break

      case 'assistant_message_chunk':
        if (message.chunk) {
          setState(prev => {
            const lastMessage = prev.messages[prev.messages.length - 1]
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
              // Update existing streaming message
              const updatedMessages = [...prev.messages]
              updatedMessages[updatedMessages.length - 1] = {
                ...lastMessage,
                content: lastMessage.content + message.chunk
              }
              return { 
                ...prev, 
                messages: updatedMessages,
                isTyping: false // Hide typing indicator when we start receiving actual content
              }
            } else {
              // Create new streaming message
              const streamingMessage: Message = {
                id: `assistant-streaming-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                role: 'assistant',
                content: message.chunk || '',
                timestamp: new Date(),
                isStreaming: true
              }
              return { 
                ...prev, 
                messages: [...prev.messages, streamingMessage],
                isTyping: false // Hide typing indicator when we start receiving actual content
              }
            }
          })
        }
        break

      case 'assistant_message_complete':
        if (message.message) {
          setState(prev => {
            const newMessage: Message = {
              id: message.message!.id || '',
              role: 'assistant',
              content: message.message!.content,
              timestamp: new Date(message.message!.timestamp || Date.now()),
              model_used: message.message!.model_used,
              response_time_ms: message.message!.response_time_ms,
              isStreaming: false
            }
            
            // Replace streaming message or add new one
            const messages = [...prev.messages]
            const lastMessage = messages[messages.length - 1]
            if (lastMessage && lastMessage.isStreaming) {
              messages[messages.length - 1] = newMessage
            } else {
              messages.push(newMessage)
            }
            
            return {
              ...prev,
              messages,
              isTyping: false
            }
          })
        }
        break

      case 'error':
        setState(prev => ({
          ...prev,
          error: message.error || 'An error occurred',
          isTyping: false
        }))
        break

      case 'pong':
        console.log('[ChatClientWrapper] Received pong from server')
        break
    }
  }, [])

  // Load conversations
  const loadConversations = async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }))
      const response = await chatApi.getConversations()
      
      if (response && response.items) {
        const conversations = response.items.map(convertToUIConversation)
        setState(prev => ({ 
          ...prev, 
          conversations,
          isLoading: false
        }))
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
      setState(prev => ({ 
        ...prev, 
        error: getErrorMessage(error),
        isLoading: false
      }))
    }
  }

  // Load files
  const loadFiles = async () => {
    try {
      const response = await chatApi.getFiles()
      if (response && response.items) {
        const files = response.items.map(convertToUIFile)
        setState(prev => ({ ...prev, uploadedFiles: files }))
      }
    } catch (error) {
      console.error('Failed to load files:', error)
    }
  }

  // Load current agent configuration
  const loadCurrentAgent = async () => {
    try {
      setAgentStatus('loading')
      const response = await chatApi.getCurrentAgent()
      if (response) {
        const agentConfig = {
          model_name: response.model_name,
          provider: response.model_provider,
          temperature: response.temperature,
          max_tokens: response.max_tokens,
        }
        setCurrentAgent(agentConfig)
        setAgentStatus('success')
      }
    } catch (error) {
      console.error('Failed to load current agent:', error)
      setAgentStatus('error')
    }
  }

  // Load files for specific conversation
  const loadConversationFiles = async (conversationId: string) => {
    if (conversationFiles[conversationId]) {
      // Files already loaded for this conversation
      setState(prev => ({ 
        ...prev, 
        uploadedFiles: conversationFiles[conversationId] 
      }))
      return
    }

    try {
      setFileLoadingStates(prev => ({ ...prev, [conversationId]: true }))
      
      // Call API to get files by conversation
      const response = await chatApi.getFiles({ 
        conversation_id: conversationId,
        page_size: 50 
      })
      
      if (response && response.items) {
        const files = response.items.map(convertToUIFile)
        
        // Cache files for this conversation
        setConversationFiles(prev => ({ 
          ...prev, 
          [conversationId]: files 
        }))
        
        setState(prev => ({ 
          ...prev, 
          uploadedFiles: files 
        }))
      }
    } catch (error) {
      console.error('Failed to load conversation files:', error)
    } finally {
      setFileLoadingStates(prev => ({ ...prev, [conversationId]: false }))
    }
  }

  // Create new conversation
  const handleCreateConversation = async () => {
    try {
      const newConversation = await chatApi.createConversation({
        name: `New Chat ${state.conversations.length + 1}`
      })
      
      if (newConversation) {
        const conversation = convertToUIConversation(newConversation)
        setState(prev => ({
          ...prev,
          conversations: [conversation, ...prev.conversations],
          activeConversationId: conversation.id,
          messages: []
        }))
        
        // Setup WebSocket for new conversation
        await setupWebSocket(conversation.id)
      }
    } catch (error) {
      console.error('Failed to create conversation:', error)
      setState(prev => ({ ...prev, error: getErrorMessage(error) }))
    }
  }

  // Select conversation
  const handleSelectConversation = async (conversationId: string) => {
    setState(prev => ({ 
      ...prev, 
      activeConversationId: conversationId,
      messages: [],
      isLoading: true
    }))

    try {
      // Load messages for the conversation
      const response = await chatApi.getConversationMessages(conversationId)
      if (response && response.items) {
        const messages = response.items.map(convertToUIMessage)
        setState(prev => ({ 
          ...prev, 
          messages,
          isLoading: false
        }))
      }

      // Setup WebSocket
      await setupWebSocket(conversationId)
    } catch (error) {
      console.error('Failed to load conversation messages:', error)
      setState(prev => ({ 
        ...prev, 
        error: getErrorMessage(error),
        isLoading: false
      }))
    }
  }

  // Setup WebSocket connection
  const setupWebSocket = async (conversationId: string) => {
    try {
      // Close existing connection
      if (websocket) {
        websocket.close()
      }      // Get WebSocket token
      console.log('[setupWebSocket] Requesting WebSocket token for conversation:', conversationId)
      const tokenResponse = await chatApi.getWebSocketToken({ conversation_id: conversationId })
      console.log('[setupWebSocket] Token response received:', tokenResponse)
      
      if (tokenResponse && tokenResponse.token) {
        console.log('[setupWebSocket] Token extracted:', tokenResponse.token)
        setState(prev => ({ ...prev, wsToken: tokenResponse.token }))

        // Create WebSocket connection
        const ws = createChatWebSocket({
          conversationId,
          token: tokenResponse.token,
          onMessage: handleWebSocketMessage,
          onError: (error) => {
            console.error('[ChatClientWrapper] WebSocket error:', error)
            setState(prev => ({ 
              ...prev, 
              error: 'WebSocket connection error',
              isTyping: false
            }))
          },
          onClose: (event) => {
            console.log('[ChatClientWrapper] WebSocket closed:', event.code, event.reason)
          },          onOpen: () => {
            console.log('[ChatClientWrapper] WebSocket connected')
            setState(prev => ({ ...prev, error: null }))
          }
        })

        await ws.connect()
        setWebsocket(ws)
      } else {
        console.error('[setupWebSocket] No token received or token is undefined:', tokenResponse)
        setState(prev => ({ 
          ...prev, 
          error: 'Failed to get WebSocket authentication token',
          isTyping: false
        }))
      }
    } catch (error) {
      console.error('Failed to setup WebSocket:', error)
      setState(prev => ({ 
        ...prev, 
        error: getErrorMessage(error),
        isTyping: false
      }))
    }
  }

  // Send message with validation flow
  const handleSendMessage = async (content: string) => {
    // Validation chain
    if (!state.activeConversationId) {
      setState(prev => ({ 
        ...prev, 
        error: 'Please select a conversation first' 
      }))
      return
    }

    if (!websocket || !websocket.isConnected()) {
      setState(prev => ({ 
        ...prev, 
        error: 'WebSocket not connected. Please try again.' 
      }))
      return
    }

    try {
      // Clear any previous errors and set loading state
      setState(prev => ({ 
        ...prev, 
        error: null,
        isLoading: true
      }))
      
      // Add user message immediately to UI with unique ID
      const userMessage: Message = {
        id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'user',
        content,
        timestamp: new Date()
      }
      
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: false,
        isTyping: true // Show typing indicator immediately after user sends message
      }))

      // Send via WebSocket for real-time streaming
      console.log('[ChatClientWrapper] Sending WebSocket message:', content)
      websocket.sendMessage(content)
      
    } catch (error) {
      console.error('Failed to send message:', error)
      setState(prev => ({ 
        ...prev, 
        error: getErrorMessage(error),
        isLoading: false,
        isTyping: false
      }))
    }
  }

  // Update conversation name with optimistic UI
  const handleUpdateConversationName = async (id: string, name: string) => {
    setEditingConversation(id)
    
    // Optimistic update
    const originalConversations = state.conversations
    setState(prev => ({
      ...prev,
      conversations: prev.conversations.map(conv =>
        conv.id === id ? { ...conv, name } : conv
      )
    }))

    try {
      await chatApi.updateConversation(id, { name })
    } catch (error) {
      console.error('Failed to update conversation:', error)
      // Revert optimistic update
      setState(prev => ({ 
        ...prev, 
        conversations: originalConversations,
        error: getErrorMessage(error) 
      }))
    } finally {
      setEditingConversation(null)
    }
  }

  // Delete conversation
  const handleDeleteConversation = async (id: string) => {
    try {
      await chatApi.deleteConversation(id)
      setState(prev => ({
        ...prev,
        conversations: prev.conversations.filter(conv => conv.id !== id),
        activeConversationId: prev.activeConversationId === id ? null : prev.activeConversationId,
        messages: prev.activeConversationId === id ? [] : prev.messages
      }))

      if (websocket && state.activeConversationId === id) {
        websocket.close()
        setWebsocket(null)
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      setState(prev => ({ ...prev, error: getErrorMessage(error) }))
    }
  }

  // Upload files with conversation association
  const handleUploadFiles = async (files: File[]) => {
    try {
      const response = await chatApi.uploadFiles(files, state.activeConversationId || undefined)
      if (response && response.uploaded_files) {
        const newFiles = response.uploaded_files.map(convertToUIFile)
        
        // Update conversation-specific file cache
        if (state.activeConversationId) {
          setConversationFiles(prev => ({
            ...prev,
            [state.activeConversationId!]: [
              ...(prev[state.activeConversationId!] || []),
              ...newFiles
            ]
          }))
        }
        
        setState(prev => ({
          ...prev,
          uploadedFiles: [...prev.uploadedFiles, ...newFiles]
        }))
      }
    } catch (error) {
      console.error('Failed to upload files:', error)
      setState(prev => ({ ...prev, error: getErrorMessage(error) }))
    }
  }

  // Delete file with UI updates
  const handleDeleteFile = async (id: string) => {
    try {
      await chatApi.deleteFile(id)
      
      // Update conversation file cache
      setConversationFiles(prev => {
        const updated = { ...prev }
        Object.keys(updated).forEach(convId => {
          updated[convId] = updated[convId].filter(file => file.id !== id)
        })
        return updated
      })
      
      setState(prev => ({
        ...prev,
        uploadedFiles: prev.uploadedFiles.filter(file => file.id !== id)
      }))
    } catch (error) {
      console.error('Failed to delete file:', error)
      setState(prev => ({ ...prev, error: getErrorMessage(error) }))
    }
  }

  // Handle agent updates from AgentManagement component
  const handleAgentUpdate = useCallback((updatedAgent: {
    model_name: string;
    provider: string;
    temperature: number;
    max_tokens: number;
  }) => {
    setCurrentAgent(updatedAgent)
    setAgentStatus('success')
  }, [])

  // Handle system prompt updates for conversations
  const handleUpdateConversationSystemPrompt = async (conversationId: string, systemPrompt: string) => {
    try {
      await chatApi.updateConversation(conversationId, { system_prompt: systemPrompt })
      setState(prev => ({
        ...prev,
        conversations: prev.conversations.map(conv =>
          conv.id === conversationId ? { ...conv, systemPrompt } : conv
        )
      }))
      setIsSystemPromptEditorOpen(false)
      setEditingConversationSystemPrompt(null)
    } catch (error) {
      console.error('Failed to update conversation system prompt:', error)
      setState(prev => ({ ...prev, error: getErrorMessage(error) }))
    }
  }

  // Handle opening system prompt editor
  const handleOpenSystemPromptEditor = (conversationId: string) => {
    setEditingConversationSystemPrompt(conversationId)
    setIsSystemPromptEditorOpen(true)
  }

  // Get current conversation system prompt
  const getCurrentConversationSystemPrompt = () => {
    if (!editingConversationSystemPrompt) return ''
    const conversation = state.conversations.find(c => c.id === editingConversationSystemPrompt)
    return conversation?.systemPrompt || ''
  }

  // Sidebar toggle handlers
  const handleToggleConversationSidebar = () => {
    setIsConversationSidebarCollapsed(prev => !prev)
  }

  const handleToggleFileSidebar = () => {
    setIsFileSidebarCollapsed(prev => !prev)
  }

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [websocket])

  return (
    <div className="flex h-full">
      {/* Expand button for Conversation Sidebar when collapsed */}
      {isConversationSidebarCollapsed && (
        <div className="hidden md:flex items-center justify-center w-12 border-r border-[color:var(--border)] bg-[color:var(--card)]/50 backdrop-blur-sm hover:bg-[color:var(--accent)]/50 transition-all duration-300">
          <Button
            onClick={handleToggleConversationSidebar}
            size="sm"
            variant="ghost"
            className="h-10 w-10 p-0 hover:bg-[color:var(--accent)] transition-all duration-300 group"
            title={t('chat.tooltips.expandSidebar') || 'Expand sidebar'}
          >
            <FontAwesomeIcon 
              icon={faChevronRight} 
              className="text-sm text-[color:var(--muted-foreground)] group-hover:text-[color:var(--foreground)] transition-colors duration-200" 
            />
          </Button>
        </div>
      )}

      {/* Desktop Conversation Sidebar */}
      <div className={`hidden md:block border-r border-[color:var(--border)] transition-all duration-300 ease-in-out ${
        isConversationSidebarCollapsed ? 'w-0 overflow-hidden' : 'w-80'
      }`}>
        <ConversationSidebar
          conversations={state.conversations}
          activeConversationId={state.activeConversationId || ''}
          onSelectConversation={handleSelectConversation}
          onCreateConversation={handleCreateConversation}
          onUpdateConversationName={handleUpdateConversationName}
          onDeleteConversation={handleDeleteConversation}
          onOpenSystemPromptEditor={handleOpenSystemPromptEditor}
          currentAgent={currentAgent}
          agentStatus={agentStatus === 'none' ? undefined : agentStatus}
          onOpenAgentManagement={() => setIsAgentManagementOpen(true)}
          isCollapsed={isConversationSidebarCollapsed}
          onToggleCollapse={handleToggleConversationSidebar}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatInterface
          conversation={state.conversations.find(conv => conv.id === state.activeConversationId) || null}
          activeConversationId={state.activeConversationId}
          messages={state.messages}
          isLoading={state.isLoading}
          isTyping={state.isTyping}
          error={state.error}
          onSendMessage={handleSendMessage}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
          isConversationSidebarCollapsed={isConversationSidebarCollapsed}
          isFileSidebarCollapsed={isFileSidebarCollapsed}
          onToggleConversationSidebar={handleToggleConversationSidebar}
          onToggleFileSidebar={handleToggleFileSidebar}
        />
      </div>

      {/* Desktop File Sidebar */}
      <div className={`hidden lg:block border-l border-[color:var(--border)] transition-all duration-300 ease-in-out ${
        isFileSidebarCollapsed ? 'w-0 overflow-hidden' : 'w-80'
      }`}>
        <FileSidebar
          uploadedFiles={state.uploadedFiles}
          isLoading={fileLoadingStates[state.activeConversationId || ''] || false}
          conversationId={state.activeConversationId}
          onDeleteFile={handleDeleteFile}
          onUploadFiles={handleUploadFiles}
          isCollapsed={isFileSidebarCollapsed}
          onToggleCollapse={handleToggleFileSidebar}
        />
      </div>

      {/* Mobile Sidebar */}
      <MobileSidebar
        isOpen={isMobileSidebarOpen}
        onClose={() => setIsMobileSidebarOpen(false)}
        conversations={state.conversations}
        activeConversationId={state.activeConversationId || ''}
        onSelectConversation={handleSelectConversation}
        onCreateConversation={handleCreateConversation}
        onUpdateConversationName={handleUpdateConversationName}
        onDeleteConversation={handleDeleteConversation}
        uploadedFiles={state.uploadedFiles}
        onDeleteFile={handleDeleteFile}
        onUploadFiles={handleUploadFiles}
      />

      {/* Agent Management Modal */}
      {isAgentManagementOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[color:var(--card)] rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-[color:var(--border)]">
              <div className="flex items-center gap-2">
                <FontAwesomeIcon icon={faRobot} className="text-[color:var(--primary)]" />
                <h2 className="text-lg font-semibold text-[color:var(--foreground)]">
                  {t('chat.agentManagement.title')}
                </h2>
              </div>
              <Button
                onClick={() => setIsAgentManagementOpen(false)}
                variant="outline"
                className="text-[color:var(--foreground)] hover:bg-[color:var(--accent)]"
                size="sm"
              >
                <FontAwesomeIcon icon={faTimes} />
              </Button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[80vh] min-w-[80%] justify-center items-center">
              <AgentManagement onAgentUpdate={handleAgentUpdate} />
            </div>
          </div>
        </div>
      )}

      {/* System Prompt Editor Modal */}
      {isSystemPromptEditorOpen && editingConversationSystemPrompt && (
        <SystemPromptEditor
          conversationId={editingConversationSystemPrompt}
          currentPrompt={getCurrentConversationSystemPrompt()}
          onSave={handleUpdateConversationSystemPrompt}
          onCancel={() => {
            setIsSystemPromptEditorOpen(false)
            setEditingConversationSystemPrompt(null)
          }}
          isOpen={isSystemPromptEditorOpen}
        />
      )}
    </div>
  )
}
