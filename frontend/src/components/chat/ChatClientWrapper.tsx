'use client'

import { useState, useEffect, useCallback } from 'react'
import { ChatInterface } from './ChatInterface'
import { ConversationSidebar } from './ConversationSidebar'
import { FileSidebar } from './FileSidebar'
import { MobileSidebar } from './MobileSidebar'
import chatApi from '@/apis/chatApi'
import { createChatWebSocket, ChatWebSocket } from '@/utils/websocket'
import { 
  type Message, 
  type ChatState,
  type WebSocketResponse,
  convertToUIMessage,
  convertToUIFile,
  convertToUIConversation
} from '@/types/chat.type'
import { getErrorMessage } from '@/utils/apiHandler'

interface ChatClientWrapperProps {
  translations: {
    welcomeTitle: string
    welcomeDescription: string
    addApiKey: string
    enterApiKey: string
    apiKeySet: string
    resetApiKey: string
    noMessages: string
    startConversation: string
    typeMessage: string
    conversations: string
    newConversation: string
    noConversationsYet: string
    createFirstChat: string
    messages: string
    uploadedFiles: string
    noFilesUploaded: string
    uploadFilesDescription: string
    chats: string
    files: string
    download: string
    delete: string
    openMenu?: string
    typing?: string
    sending?: string
  }
}

export function ChatClientWrapper({ translations }: ChatClientWrapperProps) {
  const [state, setState] = useState<ChatState>({
    conversations: [],
    activeConversationId: null,
    messages: [],
    isLoading: false,
    isTyping: false,
    error: null,
    uploadedFiles: [],
    apiKeys: [],
    wsToken: null
  })

  const [websocket, setWebsocket] = useState<ChatWebSocket | null>(null)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  // Load initial data
  useEffect(() => {
    loadConversations()
    loadFiles()
    loadApiKeys()
  }, [])

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketResponse) => {
    console.log('[ChatClientWrapper] Received WebSocket message:', message.type)
    
    switch (message.type) {
      case 'user_message':
        if (message.message) {
          const newMessage: Message = {
            id: message.message.id || '',
            role: 'user',
            content: message.message.content,
            timestamp: new Date(message.message.timestamp || Date.now())
          }
          setState(prev => ({
            ...prev,
            messages: [...prev.messages, newMessage]
          }))
        }
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
              return { ...prev, messages: updatedMessages }
            } else {
              // Create new streaming message
              const streamingMessage: Message = {
                id: `streaming-${Date.now()}`,
                role: 'assistant',
                content: message.chunk || '',
                timestamp: new Date(),
                isStreaming: true
              }
              return { ...prev, messages: [...prev.messages, streamingMessage] }
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

  // Load API keys
  const loadApiKeys = async () => {
    try {
      const apiKeys = await chatApi.getApiKeys()
      if (apiKeys) {
        setState(prev => ({ ...prev, apiKeys }))
      }
    } catch (error) {
      console.error('Failed to load API keys:', error)
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
              error: 'WebSocket connection error'
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
          error: 'Failed to get WebSocket authentication token'
        }))
      }
    } catch (error) {
      console.error('Failed to setup WebSocket:', error)
      setState(prev => ({ 
        ...prev, 
        error: getErrorMessage(error)
      }))
    }
  }

  // Send message
  const handleSendMessage = async (content: string) => {
    if (!state.activeConversationId) return

    try {
      setState(prev => ({ ...prev, isLoading: true }))

      if (websocket && websocket.isConnected()) {
        // Send via WebSocket for real-time streaming
        const defaultApiKey = state.apiKeys.find(key => key.is_default)
        websocket.sendMessage(content, defaultApiKey?.masked_key)
      } else {
        // Fallback to HTTP API
        const response = await chatApi.sendMessage({
          conversation_id: state.activeConversationId,
          content,
          api_key: state.apiKeys.find(key => key.is_default)?.masked_key
        })

        if (response) {
          const userMessage = convertToUIMessage(response.user_message)
          const aiMessage = convertToUIMessage(response.ai_message)
          
          setState(prev => ({
            ...prev,
            messages: [...prev.messages, userMessage, aiMessage]
          }))
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      setState(prev => ({ 
        ...prev, 
        error: getErrorMessage(error)
      }))
    } finally {
      setState(prev => ({ ...prev, isLoading: false }))
    }
  }

  // Update conversation name
  const handleUpdateConversationName = async (id: string, name: string) => {
    try {
      await chatApi.updateConversation(id, { name })
      setState(prev => ({
        ...prev,
        conversations: prev.conversations.map(conv =>
          conv.id === id ? { ...conv, name } : conv
        )
      }))
    } catch (error) {
      console.error('Failed to update conversation:', error)
      setState(prev => ({ ...prev, error: getErrorMessage(error) }))
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

  // Upload files
  const handleUploadFiles = async (files: File[]) => {
    try {
      const response = await chatApi.uploadFiles(files, state.activeConversationId || undefined)
      if (response && response.uploaded_files) {
        const newFiles = response.uploaded_files.map(convertToUIFile)
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

  // Delete file
  const handleDeleteFile = async (id: string) => {
    try {
      await chatApi.deleteFile(id)
      setState(prev => ({
        ...prev,
        uploadedFiles: prev.uploadedFiles.filter(file => file.id !== id)
      }))
    } catch (error) {
      console.error('Failed to delete file:', error)
      setState(prev => ({ ...prev, error: getErrorMessage(error) }))
    }
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
      {/* Desktop Conversation Sidebar */}
      <div className="hidden md:block w-80 border-r border-[color:var(--border)]">
        <ConversationSidebar
          conversations={state.conversations}
          activeConversationId={state.activeConversationId || ''}
          onSelectConversation={handleSelectConversation}
          onCreateConversation={handleCreateConversation}
          onUpdateConversationName={handleUpdateConversationName}
          onDeleteConversation={handleDeleteConversation}
          translations={{
            conversations: translations.conversations,
            newConversation: translations.newConversation,
            noConversationsYet: translations.noConversationsYet,
            createFirstChat: translations.createFirstChat,
            messages: translations.messages
          }}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <ChatInterface
          conversation={state.conversations.find(conv => conv.id === state.activeConversationId) || null}
          activeConversationId={state.activeConversationId}
          messages={state.messages}
          isLoading={state.isLoading}
          isTyping={state.isTyping}
          error={state.error}
          onSendMessage={handleSendMessage}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
          translations={{
            welcomeTitle: translations.welcomeTitle,
            welcomeDescription: translations.welcomeDescription,
            addApiKey: translations.addApiKey,
            enterApiKey: translations.enterApiKey,
            apiKeySet: translations.apiKeySet,
            resetApiKey: translations.resetApiKey,
            noMessages: translations.noMessages,
            startConversation: translations.startConversation,
            typeMessage: translations.typeMessage,
            typing: translations.typing || 'AI is typing...',
            sending: translations.sending || 'Sending...',
            openMenu: translations.openMenu || 'Menu'
          }}
        />
      </div>

      {/* Desktop File Sidebar */}
      <div className="hidden lg:block w-80 border-l border-[color:var(--border)]">
        <FileSidebar
          uploadedFiles={state.uploadedFiles}
          onDeleteFile={handleDeleteFile}
          onUploadFiles={handleUploadFiles}
          translations={{
            uploadedFiles: translations.uploadedFiles,
            noFilesUploaded: translations.noFilesUploaded,
            uploadFilesDescription: translations.uploadFilesDescription,
            download: translations.download,
            delete: translations.delete
          }}
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
        translations={{
          conversations: translations.conversations,
          newConversation: translations.newConversation,
          noConversationsYet: translations.noConversationsYet,
          createFirstChat: translations.createFirstChat,
          messages: translations.messages,
          uploadedFiles: translations.uploadedFiles,
          noFilesUploaded: translations.noFilesUploaded,
          uploadFilesDescription: translations.uploadFilesDescription,
          chats: translations.chats,
          files: translations.files,
          download: translations.download,
          delete: translations.delete
        }}
      />
    </div>
  )
}
