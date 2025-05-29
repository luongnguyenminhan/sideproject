import type { 
  WebSocketOptions, 
  WebSocketResponse, 
  ChatWebSocketMessage, 
  PingWebSocketMessage 
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

  constructor(options: WebSocketOptions) {
    this.options = options
    this.url = this.buildWebSocketUrl(options.conversationId, options.token)
  }

  private buildWebSocketUrl(conversationId: string, token: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NEXT_PUBLIC_WS_HOST || 'localhost:8000'
    return `${protocol}//${host}/api/v1/chat/ws/${conversationId}?token=${encodeURIComponent(token)}`
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = (event) => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          this.startPingInterval()
          this.options.onOpen?.(event)
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data: WebSocketResponse = JSON.parse(event.data)
            console.log('WebSocket message received:', data)
            this.options.onMessage?.(data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason)
          this.stopPingInterval()
          this.options.onClose?.(event)

          // Auto-reconnect unless manually closed
          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }

        this.ws.onerror = (event) => {
          console.error('WebSocket error:', event)
          this.options.onError?.(event)
          reject(new Error('WebSocket connection failed'))
        }

      } catch (error) {
        console.error('Error creating WebSocket:', error)
        reject(error)
      }
    })
  }

  private scheduleReconnect(): void {
    setTimeout(() => {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      this.connect().catch(() => {
        // Reconnect failed, will try again if attempts < max
      })
    }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts)) // Exponential backoff
  }

  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      this.ping()
    }, 30000) // Send ping every 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  sendMessage(content: string, apiKey?: string): void {
    if (!this.isConnected()) {
      console.error('WebSocket is not connected')
      return
    }

    const message: ChatWebSocketMessage = {
      type: 'chat_message',
      content,
      ...(apiKey && { api_key: apiKey })
    }

    this.send(message)
  }

  ping(): void {
    if (!this.isConnected()) {
      return
    }

    const pingMessage: PingWebSocketMessage = {
      type: 'ping'
    }

    this.send(pingMessage)
  }

  private send(message: object): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  disconnect(): void {
    this.isManualClose = true
    this.stopPingInterval()
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect')
      this.ws = null
    }
  }

  // Update options (useful for changing handlers)
  updateOptions(newOptions: Partial<WebSocketOptions>): void {
    this.options = { ...this.options, ...newOptions }
  }
}

// WebSocket Manager for handling multiple connections
export class WebSocketManager {
  private connections: Map<string, ChatWebSocket> = new Map()

  createConnection(connectionId: string, options: WebSocketOptions): ChatWebSocket {
    // Close existing connection if any
    this.closeConnection(connectionId)

    const ws = new ChatWebSocket(options)
    this.connections.set(connectionId, ws)
    return ws
  }

  getConnection(connectionId: string): ChatWebSocket | undefined {
    return this.connections.get(connectionId)
  }

  closeConnection(connectionId: string): void {
    const connection = this.connections.get(connectionId)
    if (connection) {
      connection.disconnect()
      this.connections.delete(connectionId)
    }
  }

  closeAllConnections(): void {
    this.connections.forEach((connection, id) => {
      connection.disconnect()
    })
    this.connections.clear()
  }

  isConnected(connectionId: string): boolean {
    const connection = this.connections.get(connectionId)
    return connection ? connection.isConnected() : false
  }
}

// Singleton instance
export const webSocketManager = new WebSocketManager()

// Hook-like function for easier integration with React components
export function createChatWebSocket(options: WebSocketOptions): ChatWebSocket {
  return new ChatWebSocket(options)
}
