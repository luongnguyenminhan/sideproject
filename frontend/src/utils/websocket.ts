import type { 
  WebSocketOptions, 
  WebSocketResponse, 
  ChatWebSocketMessage, 
  PingWebSocketMessage,
} from '@/types/chat.type'

// Legacy WebSocket class (v1)
export class ChatWebSocket {
  private ws: WebSocket | null = null
  private url: string
  private options: WebSocketOptions
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private pingInterval: NodeJS.Timeout | null = null
  private isManualClose = false
  private isConnecting = false

  constructor(options: WebSocketOptions) {
    this.options = options
    this.url = this.buildWebSocketUrl(options.conversationId, options.token)
  }

  private buildWebSocketUrl(conversationId: string, token: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const basePath = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('http://', '').replace('https://', '').replace('/api', '').replace('/v1', '') || 'localhost:8000'

    // Build query parameters
    const params = new URLSearchParams()
    params.append('token', token)
    
    // Add authorization token if available
    if (this.options.authorizationToken) {
      params.append('authorization_token', this.options.authorizationToken)
    }

    // Match the backend WebSocket route: /api/v1/chat/ws/{conversation_id}
    return `${protocol}//${basePath}/api/v1/chat/ws/${conversationId}?${params.toString()}`
  }

  async connect(): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return
    }

    this.isConnecting = true
    
    try {
      console.log(`[ChatWebSocket] Connecting to: ${this.url}`)
      
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = (event) => {
        console.log('[ChatWebSocket] Connection opened')
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.startPingInterval()
        
        if (this.options.onOpen) {
          this.options.onOpen(event)
        }
      }

      this.ws.onmessage = (event) => {
        try {
          console.log('[ChatWebSocket] Raw message received:', event.data)
          const data: WebSocketResponse = JSON.parse(event.data)
          console.log('[ChatWebSocket] Parsed message:', data)
          console.log('[ChatWebSocket] Message type:', data.type)
          
          if (data.type === 'survey_data') {
            console.log('[ChatWebSocket] Survey data details:')
            console.log('- Data field exists:', !!data.data)
            console.log('- Data is array:', Array.isArray(data.data))
            console.log('- Data length:', Array.isArray(data.data) ? data.data.length : 'N/A')
            console.log('- Full data object:', JSON.stringify(data, null, 2))
          }
          
          if (this.options.onMessage) {
            this.options.onMessage(data)
          }
        } catch (error) {
          console.error('[ChatWebSocket] Error parsing message:', error)
          console.error('[ChatWebSocket] Raw message that failed:', event.data)
        }
      }

      this.ws.onclose = (event) => {
        console.log(`[ChatWebSocket] Connection closed. Code: ${event.code}, Reason: ${event.reason}`)
        this.isConnecting = false
        this.stopPingInterval()
        
        if (this.options.onClose) {
          this.options.onClose(event)
        }

        // Auto-reconnect if not manually closed
        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = (event) => {
        console.error('[ChatWebSocket] WebSocket error:', event)
        this.isConnecting = false
        
        if (this.options.onError) {
          this.options.onError(event)
        }
      }

    } catch (error) {
      console.error('[ChatWebSocket] Failed to create WebSocket connection:', error)
      this.isConnecting = false
      throw error
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1) // Exponential backoff
    
    console.log(`[ChatWebSocket] Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`)
    
    setTimeout(() => {
      if (!this.isManualClose) {
        this.connect().catch(error => {
          console.error('[ChatWebSocket] Reconnect attempt failed:', error)
        })
      }
    }, delay)
  }

  private startPingInterval(): void {
    this.stopPingInterval()
    
    // Send ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendPing()
      }
    }, 30000)
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  sendMessage(content: string, apiKey?: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('[ChatWebSocket] Cannot send message: WebSocket not connected')
      return
    }

    const message: ChatWebSocketMessage = {
      type: 'chat_message',
      content: content.trim(),
      ...(apiKey && { api_key: apiKey })
    }

    console.log('[ChatWebSocket] Sending message:', { type: message.type, contentLength: content.length })
    this.ws.send(JSON.stringify(message))
  }

  sendRawMessage(messageData: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('[ChatWebSocket] Cannot send raw message: WebSocket not connected')
      return
    }

    console.log('[ChatWebSocket] Sending raw message')
    this.ws.send(messageData)
  }

  sendPing(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return
    }

    const pingMessage: PingWebSocketMessage = {
      type: 'ping'
    }

    console.log('[ChatWebSocket] Sending ping')
    this.ws.send(JSON.stringify(pingMessage))
  }

  close(): void {
    console.log('[ChatWebSocket] Manually closing connection')
    this.isManualClose = true
    this.stopPingInterval()
    
    if (this.ws) {
      this.ws.close(1000, 'Manual close')
      this.ws = null
    }
  }

  getConnectionState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  updateToken(newToken: string, newAuthorizationToken?: string): void {
    console.log('[ChatWebSocket] Updating tokens and reconnecting')
    this.options.token = newToken
    if (newAuthorizationToken !== undefined) {
      this.options.authorizationToken = newAuthorizationToken
    }
    this.url = this.buildWebSocketUrl(this.options.conversationId, newToken)
    
    // Reconnect with new tokens
    this.close()
    this.isManualClose = false
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('[ChatWebSocket] Failed to reconnect with new tokens:', error)
      })
    }, 1000)
  }
}

// New WebSocket v2 class for n8n integration
export class ChatWebSocketV2 {
  private ws: WebSocket | null = null
  private url: string
  private options: WebSocketOptions
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private pingInterval: NodeJS.Timeout | null = null
  private isManualClose = false
  private isConnecting = false

  constructor(options: WebSocketOptions) {
    this.options = options
    this.url = this.buildWebSocketV2Url(options.conversationId, options.token)
  }

  private buildWebSocketV2Url(conversationId: string, token: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const basePath = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('http://', '').replace('https://', '').replace('/api', '').replace('/v1', '') || 'localhost:8000'

    // Build query parameters
    const params = new URLSearchParams()
    params.append('token', token)
    
    // Add authorization token if available
    if (this.options.authorizationToken) {
      params.append('authorization_token', this.options.authorizationToken)
    }

    // Match the backend WebSocket v2 route: /api/v2/chat/ws/{conversation_id}
    return `${protocol}//${basePath}/api/v2/chat/ws/${conversationId}?${params.toString()}`
  }

  async connect(): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return
    }

    this.isConnecting = true
    
    try {
      console.log(`[ChatWebSocketV2] Connecting to: ${this.url}`)
      
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = (event) => {
        console.log('[ChatWebSocketV2] Connection opened')
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.startPingInterval()
        
        if (this.options.onOpen) {
          this.options.onOpen(event)
        }
      }

      this.ws.onmessage = (event) => {
        try {
          console.log('[ChatWebSocketV2] Raw message received:', event.data)
          const data: WebSocketResponse = JSON.parse(event.data)
          console.log('[ChatWebSocketV2] Parsed message:', data)
          console.log('[ChatWebSocketV2] Message type:', data.type)
          
          if (this.options.onMessage) {
            this.options.onMessage(data)
          }
        } catch (error) {
          console.error('[ChatWebSocketV2] Error parsing message:', error)
          console.error('[ChatWebSocketV2] Raw message that failed:', event.data)
        }
      }

      this.ws.onclose = (event) => {
        console.log(`[ChatWebSocketV2] Connection closed. Code: ${event.code}, Reason: ${event.reason}`)
        this.isConnecting = false
        this.stopPingInterval()
        
        if (this.options.onClose) {
          this.options.onClose(event)
        }

        // Auto-reconnect if not manually closed
        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = (event) => {
        console.error('[ChatWebSocketV2] WebSocket error:', event)
        this.isConnecting = false
        
        if (this.options.onError) {
          this.options.onError(event)
        }
      }

    } catch (error) {
      console.error('[ChatWebSocketV2] Failed to create WebSocket connection:', error)
      this.isConnecting = false
      throw error
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`[ChatWebSocketV2] Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`)
    
    setTimeout(() => {
      if (!this.isManualClose) {
        this.connect().catch(error => {
          console.error('[ChatWebSocketV2] Reconnect attempt failed:', error)
        })
      }
    }, delay)
  }

  private startPingInterval(): void {
    this.stopPingInterval()
    
    // Send ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendPing()
      }
    }, 30000)
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  sendMessage(content: string, apiKey?: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('[ChatWebSocketV2] Cannot send message: WebSocket not connected')
      return
    }

    const message: ChatWebSocketMessage = {
      type: 'chat_message',
      content: content.trim(),
      ...(apiKey && { api_key: apiKey })
    }

    console.log('[ChatWebSocketV2] Sending message:', { type: message.type, contentLength: content.length })
    this.ws.send(JSON.stringify(message))
  }

  sendRawMessage(messageData: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('[ChatWebSocketV2] Cannot send raw message: WebSocket not connected')
      return
    }

    console.log('[ChatWebSocketV2] Sending raw message')
    this.ws.send(messageData)
  }

  sendPing(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return
    }

    const pingMessage: PingWebSocketMessage = {
      type: 'ping'
    }

    console.log('[ChatWebSocketV2] Sending ping')
    this.ws.send(JSON.stringify(pingMessage))
  }

  close(): void {
    console.log('[ChatWebSocketV2] Manually closing connection')
    this.isManualClose = true
    this.stopPingInterval()
    
    if (this.ws) {
      this.ws.close(1000, 'Manual close')
      this.ws = null
    }
  }

  getConnectionState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  updateToken(newToken: string, newAuthorizationToken?: string): void {
    console.log('[ChatWebSocketV2] Updating tokens and reconnecting')
    this.options.token = newToken
    if (newAuthorizationToken !== undefined) {
      this.options.authorizationToken = newAuthorizationToken
    }
    this.url = this.buildWebSocketV2Url(this.options.conversationId, newToken)
    
    // Reconnect with new tokens
    this.close()
    this.isManualClose = false
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('[ChatWebSocketV2] Failed to reconnect with new tokens:', error)
      })
    }, 1000)
  }
}

// WebSocket connection states for reference
export const WebSocketStates = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3
} as const

// Helper function to create and manage WebSocket connection (legacy v1)
export function createChatWebSocket(options: WebSocketOptions): ChatWebSocket {
  return new ChatWebSocket(options)
}

// Helper function to create and manage WebSocket v2 connection (n8n integration)
export function createChatWebSocketV2(options: WebSocketOptions): ChatWebSocketV2 {
  return new ChatWebSocketV2(options)
}

// Helper function to check if browser supports WebSocket
export function isWebSocketSupported(): boolean {
  return typeof WebSocket !== 'undefined'
}
