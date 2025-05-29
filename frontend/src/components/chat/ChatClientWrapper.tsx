'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { ChatInterface } from './ChatInterface'
import { ConversationSidebar } from './ConversationSidebar'
import { FileSidebar } from './FileSidebar'
import { MobileSidebar } from './MobileSidebar'
import { Button } from '@/components/ui/button'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faBars } from '@fortawesome/free-solid-svg-icons'
import chatApi from '@/apis/chatApi'
import { ChatWebSocket, createChatWebSocket } from '@/utils/websocket'
import { getErrorMessage, isApiException } from '@/utils/apiHandler'
import Cookies from 'js-cookie'
import type { 
  Conversation, 
  Message, 
  ChatFile, 
  ApiKey,
  WebSocketResponse,
  AssistantMessageChunkResponse,
  AssistantMessageCompleteResponse,
  UserMessageResponse,
  AssistantTypingResponse,
  ErrorWebSocketResponse
} from '@/types/chat.type'

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
  }
}

export function ChatClientWrapper({ translations }: ChatClientWrapperProps) {
  // State management
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [files, setFiles] = useState<ChatFile[]>([])
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  
  // Refs
  const webSocketRef = useRef<ChatWebSocket | null>(null)
  const streamingMessageRef = useRef<string>('')
  const streamingMessageIdRef = useRef<string | null>(null)

  // Load initial data
  useEffect(() => {
    loadConversations()
    loadFiles()
    loadApiKeys()
  }, [])

  // WebSocket setup when active conversation changes
  useEffect(() => {
    if (activeConversation) {
      setupWebSocket(activeConversation.id)
      loadMessages(activeConversation.id)
    } else {
      disconnectWebSocket()
    }

    return () => {
      disconnectWebSocket()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeConversation])

  // API calls
  const loadConversations = async () => {
    try {
      setIsLoading(true)
      const response = await chatApi.getConversations({ page: 1, page_size: 50 })
      if (response?.items) {
        setConversations(response.items)
      }
    } catch (error) {
      console.error('Error loading conversations:', error)
      setError(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  const loadMessages = async (conversationId: string) => {
    try {
      const response = await chatApi.getConversationMessages(conversationId, 1, 50)
      if (response?.data?.items) {
        // Reverse to show oldest first
        setMessages(response.data.items.reverse())
      }
    } catch (error) {
      console.error('Error loading messages:', error)
      setError(getErrorMessage(error))
    }
  }

  const loadFiles = async () => {
    try {
      const response = await chatApi.getFiles({ page: 1, page_size: 50 })
      if (response?.items) {
        setFiles(response.items)
      }
    } catch (error) {
      console.error('Error loading files:', error)
    }
  }

  const loadApiKeys = async () => {
    try {
      const response = await chatApi.getApiKeys()
      if (response) {
        setApiKeys(response)
      }
    } catch (error) {
      console.error('Error loading API keys:', error)
    }
  }

  // WebSocket management
  const setupWebSocket = (conversationId: string) => {
    disconnectWebSocket()

    const token = Cookies.get('access_token')
    if (!token) {
      setError('No authentication token found')
      return
    }

    const ws = createChatWebSocket({
      conversationId,
      token,
      onMessage: handleWebSocketMessage,
      onError: handleWebSocketError,
      onClose: handleWebSocketClose,
      onOpen: handleWebSocketOpen
    })

    webSocketRef.current = ws
    ws.connect().catch((error) => {
      console.error('WebSocket connection failed:', error)
      setError('Failed to connect to chat service')
    })
  }

  const disconnectWebSocket = () => {
    if (webSocketRef.current) {
      webSocketRef.current.disconnect()
      webSocketRef.current = null
    }
    setIsConnected(false)
  }

  // WebSocket event handlers
  const handleWebSocketOpen = () => {
    setIsConnected(true)
    setError(null)
  }

  const handleWebSocketClose = () => {
    setIsConnected(false)
  }

  const handleWebSocketError = (error: Event) => {
    console.error('WebSocket error:', error)
    setError('Connection error occurred')
    setIsConnected(false)
  }

  const handleWebSocketMessage = (message: WebSocketResponse) => {
    switch (message.type) {
      case 'user_message':
        handleUserMessage(message as UserMessageResponse)
        break
      
      case 'assistant_typing':
        handleAssistantTyping(message as AssistantTypingResponse)
        break
      
      case 'assistant_message_chunk':
        handleAssistantMessageChunk(message as AssistantMessageChunkResponse)
        break
      
      case 'assistant_message_complete':
        handleAssistantMessageComplete(message as AssistantMessageCompleteResponse)
        break
      
      case 'error':
        handleWebSocketErrorMessage(message as ErrorWebSocketResponse)
        break
      
      case 'pong':
        // Handle ping response
        console.log('Received pong from server')
        break
      
      default:
        console.log('Unknown message type:', message.type)
    }
  }

  const handleUserMessage = (message: UserMessageResponse) => {
    setMessages(prev => [...prev, message.message])
    // Update conversation's last activity and message count
    setConversations(prev => 
      prev.map(conv => 
        conv.id === message.message.conversation_id 
          ? { ...conv, message_count: conv.message_count + 1, last_activity: message.message.timestamp }
          : conv
      )
    )
  }

  const handleAssistantTyping = (message: AssistantTypingResponse) => {
    setIsTyping(message.status)
  }

  const handleAssistantMessageChunk = (message: AssistantMessageChunkResponse) => {
    streamingMessageRef.current += message.chunk
    
    // Update or create streaming message in the UI
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1]
      
      if (streamingMessageIdRef.current && lastMessage?.id === streamingMessageIdRef.current) {
        // Update existing streaming message
        return prev.map((msg, index) => 
          index === prev.length - 1 
            ? { ...msg, content: streamingMessageRef.current }
            : msg
        )
      } else {
        // Create new streaming message
        const streamingMessage: Message = {
          id: `streaming-${Date.now()}`,
          conversation_id: activeConversation?.id || '',
          user_id: '',
          role: 'assistant',
          content: streamingMessageRef.current,
          timestamp: new Date().toISOString(),
          create_date: new Date().toISOString(),
          update_date: new Date().toISOString()
        }
        streamingMessageIdRef.current = streamingMessage.id
        return [...prev, streamingMessage]
      }
    })
  }

  const handleAssistantMessageComplete = (message: AssistantMessageCompleteResponse) => {
    // Replace streaming message with final message
    setMessages(prev => {
      const filteredMessages = prev.filter(msg => !msg.id.startsWith('streaming-'))
      return [...filteredMessages, message.message]
    })
    
    // Reset streaming state
    streamingMessageRef.current = ''
    streamingMessageIdRef.current = null
    setIsTyping(false)
    
    // Update conversation
    setConversations(prev => 
      prev.map(conv => 
        conv.id === message.message.conversation_id 
          ? { ...conv, message_count: conv.message_count + 1, last_activity: message.message.timestamp }
          : conv
      )
    )
  }

  const handleWebSocketErrorMessage = (message: ErrorWebSocketResponse) => {
    setError(message.message)
    setIsTyping(false)
  }

  // Event handlers
  const handleSendMessage = useCallback((content: string) => {
    if (!webSocketRef.current || !webSocketRef.current.isConnected()) {
      setError('Not connected to chat service')
      return
    }

    // Get default API key
    const defaultApiKey = apiKeys.find(key => key.is_default)
    webSocketRef.current.sendMessage(content, defaultApiKey?.id)
  }, [apiKeys])

  const handleSelectConversation = (id: string) => {
    const conversation = conversations.find(c => c.id === id)
    if (conversation) {
      setActiveConversation(conversation)
      setMessages([])
      setError(null)
    }
  }

  const handleCreateConversation = async () => {
    try {
      const newConversation = await chatApi.createConversation({
        name: `New Conversation ${new Date().toLocaleTimeString()}`
      })
      
      if (newConversation) {
        setConversations(prev => [newConversation, ...prev])
        setActiveConversation(newConversation)
        setMessages([])
      }
    } catch (error) {
      console.error('Error creating conversation:', error)
      setError(getErrorMessage(error))
    }
  }

  const handleUpdateConversationName = async (id: string, name: string) => {
    try {
      const updatedConversation = await chatApi.updateConversation(id, { name })
      
      if (updatedConversation) {
        setConversations(prev => 
          prev.map(conv => conv.id === id ? updatedConversation : conv)
        )
        
        if (activeConversation?.id === id) {
          setActiveConversation(updatedConversation)
        }
      }
    } catch (error) {
      console.error('Error updating conversation:', error)
      setError(getErrorMessage(error))
    }
  }

  const handleDeleteConversation = async (id: string) => {
    try {
      await chatApi.deleteConversation(id)
      
      setConversations(prev => prev.filter(conv => conv.id !== id))
      
      if (activeConversation?.id === id) {
        setActiveConversation(null)
        setMessages([])
      }
    } catch (error) {
      console.error('Error deleting conversation:', error)
      setError(getErrorMessage(error))
    }
  }

  const handleUploadFiles = async (uploadFiles: File[]) => {
    try {
      const uploadedFiles = await chatApi.uploadFiles(uploadFiles, activeConversation?.id)
      
      if (uploadedFiles) {
        setFiles(prev => [...uploadedFiles, ...prev])
      }
    } catch (error) {
      console.error('Error uploading files:', error)
      setError(getErrorMessage(error))
    }
  }

  const handleDeleteFile = async (id: string) => {
    try {
      await chatApi.deleteFile(id)
      setFiles(prev => prev.filter(file => file.id !== id))
    } catch (error) {
      console.error('Error deleting file:', error)
      setError(getErrorMessage(error))
    }
  }

  // Transform data for components
  const transformedConversations = conversations.map(conv => ({
    id: conv.id,
    name: conv.name,
    messages: [], // We load messages separately
    lastActivity: new Date(conv.last_activity)
  }))

  const transformedMessages = messages.map(msg => ({
    id: msg.id,
    role: msg.role as 'user' | 'assistant',
    content: msg.content,
    timestamp: new Date(msg.timestamp)
  }))

  const transformedFiles = files.map(file => ({
    id: file.id,
    name: file.name,
    size: file.size,
    type: file.type,
    uploadDate: new Date(file.upload_date)
  }))

  const currentConversation = activeConversation ? {
    id: activeConversation.id,
    name: activeConversation.name,
    messages: transformedMessages,
    lastActivity: new Date(activeConversation.last_activity)
  } : undefined

  return (
    <div className="flex h-full">
      {/* Mobile Menu Button */}
      <div className="md:hidden fixed top-4 left-4 z-50">
        <Button
          onClick={() => setIsMobileSidebarOpen(true)}
          size="sm"
          variant="outline"
          className="bg-[color:var(--card)] border-[color:var(--border)]"
        >
          <FontAwesomeIcon icon={faBars} />
        </Button>
      </div>

      {/* Desktop Conversation Sidebar */}
      <div className="hidden md:block w-80 border-r border-[color:var(--border)]">
        <ConversationSidebar
          conversations={transformedConversations}
          activeConversationId={activeConversation?.id || ''}
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
          conversation={currentConversation}
          onSendMessage={handleSendMessage}
          translations={translations}
        />
      </div>

      {/* Desktop File Sidebar */}
      <div className="hidden lg:block w-80 border-l border-[color:var(--border)]">
        <FileSidebar
          uploadedFiles={transformedFiles}
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
        conversations={transformedConversations}
        activeConversationId={activeConversation?.id || ''}
        onSelectConversation={handleSelectConversation}
        onCreateConversation={handleCreateConversation}
        onUpdateConversationName={handleUpdateConversationName}
        onDeleteConversation={handleDeleteConversation}
        uploadedFiles={transformedFiles}
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

      {/* Connection Status */}
      {error && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {error}
        </div>
      )}
      
      {!isConnected && activeConversation && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-yellow-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          Connecting to chat service...
        </div>
      )}
    </div>
  )
}
