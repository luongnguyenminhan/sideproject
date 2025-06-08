import type { 
  WebSocketOptions, 
  WebSocketResponse, 
  ChatWebSocketMessage, 
  PingWebSocketMessage,
} from '@/types/chat.type'

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
    const protocol = window.location.protocol === 'https:' ? 'ws:' : 'ws:'
    const basePath = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('http://', '').replace('https://', '').replace('/api', '') || '160.191.88.194:11111'
    
    // Match the backend WebSocket route: /api/v1/chat/ws/{conversation_id}
    return `${protocol}//${basePath}/api/v1/chat/ws/${conversationId}?token=${encodeURIComponent(token)}`
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
          const data: WebSocketResponse = JSON.parse(event.data)
          console.log('[ChatWebSocket] Message received:', data.type)
          
          if (this.options.onMessage) {
            this.options.onMessage(data)
          }
        } catch (error) {
          console.error('[ChatWebSocket] Error parsing message:', error)
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

  updateToken(newToken: string): void {
    console.log('[ChatWebSocket] Updating token and reconnecting')
    this.options.token = newToken
    this.url = this.buildWebSocketUrl(this.options.conversationId, newToken)
    
    // Reconnect with new token
    this.close()
    this.isManualClose = false
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('[ChatWebSocket] Failed to reconnect with new token:', error)
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

// Helper function to create and manage WebSocket connection
export function createChatWebSocket(options: WebSocketOptions): ChatWebSocket {
  return new ChatWebSocket(options)
}

// Helper function to check if browser supports WebSocket
export function isWebSocketSupported(): boolean {
  return typeof WebSocket !== 'undefined'
}
