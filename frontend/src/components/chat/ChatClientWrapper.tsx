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
import type { Question } from '@/types/question.types'
import { getErrorMessage } from '@/utils/apiHandler'
import { ChatWebSocket, ChatWebSocketV2, createChatWebSocket, createChatWebSocketV2 } from '@/utils/websocket'
import { faRobot, faTimes } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { useCallback, useEffect, useState } from 'react'
import Cookies from 'js-cookie'
import { AgentManagement } from './AgentManagement'
import { ChatInterface } from './chat-interface'
import { ConversationSidebar } from './ConversationSidebar'
import { FileSidebar } from './FileSidebar'
import { MobileSidebar } from './MobileSidebar'
import { SystemPromptEditor } from './SystemPromptEditor'
import { CVModal } from '@/components/chat/CVModal'
import { ResizableChatLayout } from './ResizableChatLayout'

interface ChatClientWrapperProps {
  conversationId?: string
  useWebSocketV2?: boolean // New prop to choose WebSocket version
}

export default function ChatClientWrapper({ 
  useWebSocketV2 = false // Default to v1 for backward compatibility
}: ChatClientWrapperProps) {
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
  const [isCVUploading, setIsCVUploading] = useState(false)
  const [cvModalVisible, setCvModalVisible] = useState(false)
  const [cvData, setCvData] = useState<any>(null)

  // Survey state management
  const [surveyModalVisible, setSurveyModalVisible] = useState(false)
  const [surveyData, setSurveyData] = useState<Question[]>([])
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [surveyTitle, setSurveyTitle] = useState('Survey Form')
  const [surveyConversationId, setSurveyConversationId] = useState<string | null>(null)

  // Updated websocket state to handle both v1 and v2
  const [websocket, setWebsocket] = useState<ChatWebSocket | ChatWebSocketV2 | null>(null)
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

  // Clear survey data when conversation changes or no conversation is active
  useEffect(() => {
    if (!state.activeConversationId || (surveyConversationId && surveyConversationId !== state.activeConversationId)) {
      // Clear survey data if no conversation is active or if we switched to a different conversation
      setSurveyData([])
      setSurveyModalVisible(false)
      setSurveyConversationId(null)
      setSurveyTitle('Survey Form')
    }
    // Don't auto-close survey if we have data for the current conversation
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
              const updatedContent = lastMessage.content + message.chunk
              updatedMessages[updatedMessages.length - 1] = {
                ...lastMessage,
                content: updatedContent
              }
              
              // Check if we've received the survey token during streaming
              const hasSurveyToken = updatedContent.includes('</survey>')
              if (hasSurveyToken) {
                console.log('[ChatClientWrapper] Survey token detected during streaming!')
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
            
            // Check if message contains survey token
            const hasSurveyToken = message.message!.content.includes('</survey>')
            console.log('[ChatClientWrapper] Message contains survey token:', hasSurveyToken)
            
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

      case 'survey_data':
        console.log('[ChatClientWrapper] Raw survey data received:')
        console.log('- Message object:', message)
        console.log('- Data field:', message.data)
        console.log('- Data type:', typeof message.data)
        console.log('- Is array:', Array.isArray(message.data))
        
        if (message.data) {
          console.log('- Data length:', Array.isArray(message.data) ? message.data.length : 'Not an array')
          console.log('- First item:', Array.isArray(message.data) && message.data.length > 0 ? message.data[0] : 'No items')
          console.log('- Data structure:', JSON.stringify(message.data, null, 2))
        }
        
        if (message.data && Array.isArray(message.data)) {
          // Validate survey data structure
          const validQuestions = message.data.filter((item: any) => {
            const isValid = item && 
                           typeof item.Question === 'string' && 
                           typeof item.Question_type === 'string' &&
                           (item.Question_data === null || Array.isArray(item.Question_data))
            if (!isValid) {
              console.warn('[ChatClientWrapper] Invalid question item:', item)
            }
            return isValid
          })
          
          console.log(`[ChatClientWrapper] Validated ${validQuestions.length}/${message.data.length} questions`)
          
          if (validQuestions.length > 0) {
            // Always process survey data when received
            const receivedConversationId = message.conversation_id || state.activeConversationId
            
            console.log('[ChatClientWrapper] Processing survey data for conversation:', receivedConversationId)
  

            // Set survey data and track which conversation it belongs to
            setSurveyData(validQuestions)
            setSurveyConversationId(receivedConversationId)
            setSurveyTitle(receivedConversationId ? `Survey - ${receivedConversationId}` : 'Career Survey')
            
            console.log('[ChatClientWrapper] Survey state updated:', {
              questionsCount: validQuestions.length,
              conversationId: receivedConversationId,
              title: receivedConversationId ? `Survey - ${receivedConversationId}` : 'Career Survey'
            })
            
            // Auto-open survey panel when survey data is received (only if it's for current conversation)
            if (receivedConversationId === state.activeConversationId) {
              setSurveyModalVisible(true)
              console.log('[ChatClientWrapper] Survey panel auto-opened for current conversation')
            } else {
              console.log('[ChatClientWrapper] Survey data received but not auto-opening (different conversation)')
            }
          } else {
            console.error('[ChatClientWrapper] No valid questions found in survey data')
          }
        } else {
          console.error('[ChatClientWrapper] Invalid survey data format - expected array but got:', typeof message.data)
        }
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
      }
      
      // Get authorization token from cookies using js-cookie
      const authorizationToken = Cookies.get('access_token')
      
      console.log('[setupWebSocket] Authorization token:', authorizationToken ? authorizationToken.substring(0, 20) + '...' : 'Not found')
      console.log(`[setupWebSocket] Using WebSocket ${useWebSocketV2 ? 'V2 (n8n)' : 'V1 (agent)'}`)
      
      // Get WebSocket token
      console.log('[setupWebSocket] Requesting WebSocket token for conversation:', conversationId)
      const tokenResponse = await chatApi.getWebSocketToken({ conversation_id: conversationId })
      console.log('[setupWebSocket] Token response received:', tokenResponse)
      
      if (tokenResponse && tokenResponse.token) {
        console.log('[setupWebSocket] Token extracted:', tokenResponse.token)
        setState(prev => ({ ...prev, wsToken: tokenResponse.token }))

        // Create WebSocket connection with both tokens
        const ws = useWebSocketV2 
          ? createChatWebSocketV2({
              conversationId,
              token: tokenResponse.token,
              authorizationToken, // Pass the authorization token
              onMessage: handleWebSocketMessage,
              onError: (error) => {
                console.error('[ChatClientWrapper] WebSocket V2 error:', error)
                setState(prev => ({ 
                  ...prev, 
                  error: 'WebSocket V2 connection error',
                  isTyping: false
                }))
              },
              onClose: (event) => {
                console.log('[ChatClientWrapper] WebSocket V2 closed:', event.code, event.reason)
              },
              onOpen: () => {
                console.log('🚀 [ChatClientWrapper] WebSocket V2 (n8n) connected successfully!')
                setState(prev => ({ ...prev, error: null }))
              }
            })
          : createChatWebSocket({
              conversationId,
              token: tokenResponse.token,
              authorizationToken, // Pass the authorization token
              onMessage: handleWebSocketMessage,
              onError: (error) => {
                console.error('[ChatClientWrapper] WebSocket V1 error:', error)
                setState(prev => ({ 
                  ...prev, 
                  error: 'WebSocket V1 connection error',
                  isTyping: false
                }))
              },
              onClose: (event) => {
                console.log('[ChatClientWrapper] WebSocket V1 closed:', event.code, event.reason)
              },
              onOpen: () => {
                console.log('🔗 [ChatClientWrapper] WebSocket V1 (agent) connected successfully!')
                setState(prev => ({ ...prev, error: null }))
              }
            })

        await ws.connect()
        setWebsocket(ws)
        
        // Log connection success
        console.log(`✅ WebSocket ${useWebSocketV2 ? 'V2 (n8n)' : 'V1 (agent)'} setup completed for conversation: ${conversationId}`)
      } else {
        console.error('[setupWebSocket] No token received or token is undefined:', tokenResponse)
        setState(prev => ({ 
          ...prev, 
          error: 'Failed to get WebSocket authentication token',
          isTyping: false
        }))
      }
    } catch (error) {
      console.error(`Failed to setup WebSocket ${useWebSocketV2 ? 'V2' : 'V1'}:`, error)
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

  // Upload CV with conversation association
  const handleUploadCV = async (file: File) => {
    try {
      setIsCVUploading(true)
      
      const response = await chatApi.uploadCV(file, state.activeConversationId || undefined)
      if (response) {
        // Show success message with detailed CV summary
        const cvAnalysis = response.cv_analysis_result
        const personalInfo = cvAnalysis?.personal_information
        
        setState(prev => ({ 
          ...prev, 
          error: null
        }))
        
        // Enhanced logging with detailed CV analysis results
        console.log('CV uploaded and analyzed successfully:', {
          personalInfo: {
            name: personalInfo?.full_name,
            email: personalInfo?.email,
            phone: personalInfo?.phone_number
          },
          summary: {
            skillsCount: response.skills_count,
            experienceCount: response.experience_count,
            cvSummary: response.cv_summary?.substring(0, 100) + '...'
          },
          fileInfo: {
            filePath: response.file_path,
            cvFileUrl: response.cv_file_url
          }
        })
        
        // Store CV data and show modal
        setCvData(response)
        setCvModalVisible(true)
        
        // Show success notification
        console.log('✅ CV Analysis completed:', {
          personal_info: personalInfo,
          skills_count: response.skills_count,
          experience_count: response.experience_count,
          cv_summary: response.cv_summary
        })
      }
    } catch (error) {
      console.error('❌ CV upload failed:', error)
      setState(prev => ({ 
        ...prev, 
        error: 'Failed to upload CV. Please try again.' 
      }))
    } finally {
      setIsCVUploading(false)
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

  // Handle survey modal toggle
  const handleToggleSurveyModal = () => {
    setSurveyModalVisible(prev => {
      const newState = !prev
      
      // Auto collapse file sidebar when survey opens
      if (newState === true) {
        setIsFileSidebarCollapsed(true)
      }
      
      // If closing the survey, also clear the conversation ID
      if (prev === true) {
        setSurveyConversationId(null)
      }
      return newState
    })
  }

  // Handle opening survey panel manually
  const handleOpenSurvey = () => {
    console.log('[ChatClientWrapper] handleOpenSurvey called:', {
      surveyDataLength: surveyData.length,
      surveyConversationId,
      activeConversationId: state.activeConversationId,
      surveyModalVisible,
      surveyDataContent: surveyData.slice(0, 2) // Show first 2 questions for debugging
    })
    
    // Auto collapse file sidebar when survey opens
    setIsFileSidebarCollapsed(true)
    
    // Always open survey panel - SurveyPanelWrapper will handle fetching data
    setSurveyModalVisible(true)
    console.log('[ChatClientWrapper] Survey panel opened - SurveyPanelWrapper will handle data fetching')
  }

  const handleOpenCVModal = async (conversationId: string) => {
    try {
      const response = await chatApi.getCVMetadata(conversationId)
      if (response) {
        setCvData(response)
        setCvModalVisible(true)
      } else {
        // No CV data found
        setState(prev => ({ 
          ...prev, 
          error: t('chat.noCVDataFound') || 'No CV data found for this conversation'
        }))
      }
    } catch (error) {
      console.error('Failed to load CV metadata:', error)
      setState(prev => ({ 
        ...prev, 
        error: getErrorMessage(error)
      }))
    }
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

  // Keyboard shortcuts for survey panel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (surveyModalVisible && e.key === 'Escape') {
        setSurveyModalVisible(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [surveyModalVisible])

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [websocket])

  return (
    <div className="flex h-full chat-container">

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
          onOpenCVModal={handleOpenCVModal}
          currentAgent={currentAgent}
          agentStatus={agentStatus === 'none' ? undefined : agentStatus}
          onOpenAgentManagement={() => setIsAgentManagementOpen(true)}
          isCollapsed={isConversationSidebarCollapsed}
          onToggleCollapse={handleToggleConversationSidebar}
        />
      </div>

      {/* Main Content Area with Resizable Chat + Survey */}
      <div className="flex-1 min-w-0 flex flex-col">
        <ResizableChatLayout
          isSurveyOpen={surveyModalVisible}
          onSurveyClose={() => {
            setSurveyModalVisible(false)
            setSurveyConversationId(null)
          }}
          websocket={websocket}
          conversationId={state.activeConversationId || undefined}
          onSurveyComplete={async (answers) => {
            console.log('[ChatClientWrapper] Survey completed with answers:', answers)
            // Note: WebSocket sending is now handled by SurveyContainer/SurveyPanel
            // No need to duplicate WebSocket logic here
          }}
          onSendToChat={async (message: string, isAIResponse?: boolean) => {
            console.log('[ChatClientWrapper] Sending survey message to chat:', { message, isAIResponse })
            
            // Add message to chat interface
            if (state.activeConversationId) {
              const newMessage = {
                id: Date.now().toString(),
                role: isAIResponse ? 'assistant' : 'user',
                content: message,
                timestamp: new Date(),
                conversation_id: state.activeConversationId
              }
              
              // Update messages state to show the message immediately
              setState(prev => ({
                ...prev,
                messages: [...prev.messages, newMessage as any]
              }))
              
              console.log('[ChatClientWrapper] Message added to chat interface')
            }
          }}
          fallbackQuestions={surveyData}
        >
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
            onToggleSurvey={handleToggleSurveyModal}
            onOpenSurvey={handleOpenSurvey}
            isSurveyOpen={surveyModalVisible}
          />
        </ResizableChatLayout>
      </div>

      {/* Desktop File Sidebar - show when survey is closed */}
      {!surveyModalVisible && state.activeConversationId && (
        <div className={`hidden lg:block border-l border-[color:var(--border)] transition-all duration-300 ease-in-out ${
          isFileSidebarCollapsed ? 'w-0 overflow-hidden' : 'w-80'
        }`}>
            <FileSidebar
              uploadedFiles={state.uploadedFiles}
              isLoading={fileLoadingStates.files || false}
              conversationId={state.activeConversationId}
              onDeleteFile={handleDeleteFile}
              onUploadFiles={handleUploadFiles}
              onUploadCV={handleUploadCV}
              isCVUploading={isCVUploading}
              hasSurveyData={surveyData.length > 0}
              onOpenSurvey={handleOpenSurvey}
              onClose={() => setIsFileSidebarCollapsed(true)}
            />
        </div>
      )}

      {/* DEBUG: WebSocket V2 Testing Panel */}
      {process.env.NODE_ENV === 'development' && state.activeConversationId && (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 bg-[color:var(--card)] border border-[color:var(--border)] rounded-lg p-4 shadow-lg max-w-sm">
          <div className="text-sm font-semibold text-[color:var(--foreground)] mb-2">
            🧪 WebSocket {useWebSocketV2 ? 'V2 (n8n)' : 'V1 (Agent)'} Test Panel
          </div>
          
          <div className="text-xs text-[color:var(--muted-foreground)] space-y-1">
            <div>Status: {websocket?.isConnected() ? '🟢 Connected' : '🔴 Disconnected'}</div>
            <div>Conversation: {state.activeConversationId?.substring(0, 8)}...</div>
            <div>Version: {useWebSocketV2 ? 'V2 (n8n)' : 'V1 (Agent)'}</div>
          </div>
          
          <div className="flex flex-col gap-1">
            <Button
              onClick={() => {
                console.log('[DEBUG] WebSocket Test - Current State:', {
                  isConnected: websocket?.isConnected(),
                  hasWebSocket: !!websocket,
                  connectionState: websocket?.getConnectionState(),
                  version: useWebSocketV2 ? 'V2' : 'V1',
                  activeConversationId: state.activeConversationId,
                  wsToken: state.wsToken
                })
              }}
              className="bg-blue-500 hover:bg-blue-600 text-white text-xs px-2 py-1 rounded"
              size="sm"
            >
              🔍 Log WebSocket State
            </Button>
            
            <Button
              onClick={() => {
                if (websocket?.isConnected()) {
                  const testMessage = `Test message from WebSocket ${useWebSocketV2 ? 'V2' : 'V1'} at ${new Date().toLocaleTimeString()}`
                  websocket.sendMessage(testMessage)
                  console.log(`[DEBUG] Sent test message via WebSocket ${useWebSocketV2 ? 'V2' : 'V1'}:`, testMessage)
                } else {
                  console.error('[DEBUG] Cannot send test message - WebSocket not connected')
                }
              }}
              className="bg-green-500 hover:bg-green-600 text-white text-xs px-2 py-1 rounded"
              size="sm"
            >
              📤 Send Test Message
            </Button>
            
            <Button
              onClick={() => {
                if (websocket?.isConnected()) {
                  websocket.sendPing()
                  console.log(`[DEBUG] Sent ping via WebSocket ${useWebSocketV2 ? 'V2' : 'V1'}`)
                } else {
                  console.error('[DEBUG] Cannot send ping - WebSocket not connected')
                }
              }}
              className="bg-orange-500 hover:bg-orange-600 text-white text-xs px-2 py-1 rounded"
              size="sm"
            >
              🏓 Send Ping
            </Button>
            
            <Button
              onClick={() => {
                if (state.activeConversationId) {
                  setupWebSocket(state.activeConversationId)
                  console.log(`[DEBUG] Reconnecting WebSocket ${useWebSocketV2 ? 'V2' : 'V1'}`)
                }
              }}
              className="bg-purple-500 hover:bg-purple-600 text-white text-xs px-2 py-1 rounded"
              size="sm"
            >
              🔄 Reconnect
            </Button>
          </div>
        </div>
      )}
     
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
        onUploadCV={handleUploadCV}
        isCVUploading={isCVUploading}
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

      {/* CV Modal */}
      <CVModal
        isVisible={cvModalVisible}
        onClose={() => {
          setCvModalVisible(false)
          setCvData(null)
        }}
        cvData={cvData}
      />
    </div>
  )
}
