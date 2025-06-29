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
import { ChatWebSocket, createChatWebSocket } from '@/utils/websocket'
import { faChevronRight, faRobot, faTimes } from '@fortawesome/free-solid-svg-icons'
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
import { SurveyPanel } from './SurveyPanel'

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
  const [isCVUploading, setIsCVUploading] = useState(false)
  const [cvModalVisible, setCvModalVisible] = useState(false)
  const [cvData, setCvData] = useState<any>(null)

  // Survey state management
  const [surveyModalVisible, setSurveyModalVisible] = useState(false)
  const [surveyData, setSurveyData] = useState<Question[]>([])
  const [surveyTitle, setSurveyTitle] = useState('Survey Form')
  const [surveyConversationId, setSurveyConversationId] = useState<string | null>(null)

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
            
            // Add survey message to chat
            const surveyMessage: Message = {
              id: `survey_${Date.now()}`,
              content: 'Survey questions generated! Click the "Survey" button to complete the interactive survey.',
              role: 'assistant',
              timestamp: new Date(),
              survey_data: validQuestions // Store the validated survey questions
            }
            
            setState(prev => ({
              ...prev,
              messages: [...prev.messages, surveyMessage],
              isTyping: false
            }))

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
      
      // Get WebSocket token
      console.log('[setupWebSocket] Requesting WebSocket token for conversation:', conversationId)
      const tokenResponse = await chatApi.getWebSocketToken({ conversation_id: conversationId })
      console.log('[setupWebSocket] Token response received:', tokenResponse)
      
      if (tokenResponse && tokenResponse.token) {
        console.log('[setupWebSocket] Token extracted:', tokenResponse.token)
        setState(prev => ({ ...prev, wsToken: tokenResponse.token }))

        // Create WebSocket connection with both tokens
        const ws = createChatWebSocket({
          conversationId,
          token: tokenResponse.token,
          authorizationToken, // Pass the authorization token
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
          },
          onOpen: () => {
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
      // If closing the survey, also clear the conversation ID
      if (prev === true) {
        setSurveyConversationId(null)
      }
      return !prev
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
    
    if (surveyData.length > 0) {
      // If we have survey data, always try to open it
      if (surveyConversationId === state.activeConversationId || !surveyConversationId) {
        setSurveyModalVisible(true)
        console.log('[ChatClientWrapper] Survey panel opened manually - data available for current conversation')
      } else {
        console.log('[ChatClientWrapper] Survey data exists but for different conversation:', {
          surveyConversationId,
          activeConversationId: state.activeConversationId
        })
        // Still try to open it as user explicitly requested
        setSurveyModalVisible(true)
      }
    } else {
      console.log('[ChatClientWrapper] No survey data available to open. Trying to fetch or show empty state.')
      // Try to open empty survey panel or show a message
      setSurveyModalVisible(true)
    }
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
          onOpenCVModal={handleOpenCVModal}
          currentAgent={currentAgent}
          agentStatus={agentStatus === 'none' ? undefined : agentStatus}
          onOpenAgentManagement={() => setIsAgentManagementOpen(true)}
          isCollapsed={isConversationSidebarCollapsed}
          onToggleCollapse={handleToggleConversationSidebar}
        />
      </div>

      {/* Main Chat Area - adjusts width based on survey state */}
      <div className={`flex flex-col min-w-0 transition-all duration-300 ease-in-out ${
        surveyModalVisible && surveyData.length > 0
          ? 'w-1/2' // 50% when survey is open
          : 'flex-1' // full width when survey is closed
      }`}>
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
        hasSurveyData={surveyData.length > 0}
        isSurveyOpen={surveyModalVisible}
        />
      </div>

      {/* DEBUG: Survey State Logging */}
      {state.activeConversationId && (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
          <Button
            onClick={() => {
              console.log('[DEBUG] Current Survey State:', {
                surveyDataLength: surveyData.length,
                surveyConversationId,
                activeConversationId: state.activeConversationId,
                surveyModalVisible,
                surveyData: surveyData.slice(0, 1),
                surveyDataFull: surveyData
              })
            }}
            className="bg-blue-500 hover:bg-blue-600 text-white text-xs px-3 py-1 rounded shadow-lg"
          >
            🔍 Log Survey State
          </Button>
          <Button
            onClick={() => {
              console.log('[DEBUG] WebSocket State:', {
                isConnected: websocket?.isConnected(),
                hasWebSocket: !!websocket,
                connectionState: websocket?.getConnectionState()
              })
            }}
            className="bg-purple-500 hover:bg-purple-600 text-white text-xs px-3 py-1 rounded shadow-lg"
          >
            🌐 Log WebSocket State
          </Button>
        </div>
      )}

      {/* Survey Panel - 50% width when active */}
      {surveyModalVisible && surveyData.length > 0 && (
        <div className="w-1/2 border-l border-[color:var(--border)] hidden lg:block">
          <SurveyPanel
            isOpen={surveyModalVisible}
            onClose={() => {
              setSurveyModalVisible(false)
              setSurveyConversationId(null)
            }}
            questions={surveyData}
            title={surveyTitle}
            websocket={websocket}
            conversationId={state.activeConversationId || undefined}
            onSurveyComplete={async (answers) => {
              console.log('[ChatClientWrapper] Survey completed with answers:', answers)
              
              // Send survey response back via WebSocket if connected
              if (websocket && websocket.isConnected()) {
                try {
                  const surveyResponse = {
                    type: 'survey_response',
                    answers: answers,
                    conversation_id: state.activeConversationId,
                    timestamp: new Date().toISOString()
                  }
                  
                  websocket.sendRawMessage(JSON.stringify(surveyResponse))
                  console.log('[ChatClientWrapper] Survey response sent via WebSocket')
                } catch (error) {
                  console.error('[ChatClientWrapper] Failed to send survey response:', error)
                }
              }
            }}
          />
        </div>
      )}

      {/* Desktop File Sidebar - always show but adjust position based on survey state */}
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
          isCollapsed={isFileSidebarCollapsed}
          onToggleCollapse={handleToggleFileSidebar}
          hasSurveyData={surveyData.length > 0}
          onOpenSurvey={handleOpenSurvey}
        />
      </div>

      {/* Expand button for File Sidebar when collapsed */}
      {isFileSidebarCollapsed && (
        <div className="hidden lg:flex items-center justify-center w-12 border-l border-[color:var(--border)] bg-[color:var(--card)]/50 backdrop-blur-sm hover:bg-[color:var(--accent)]/50 transition-all duration-300">
          <Button
            onClick={handleToggleFileSidebar}
            size="sm"
            variant="ghost"
            className="h-10 w-10 p-0 hover:bg-[color:var(--accent)] transition-all duration-300 group rotate-180"
            title={t('chat.tooltips.expandSidebar') || 'Expand file sidebar'}
          >
            <FontAwesomeIcon 
              icon={faChevronRight} 
              className="text-sm text-[color:var(--muted-foreground)] group-hover:text-[color:var(--foreground)] transition-colors duration-200" 
            />
          </Button>
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
