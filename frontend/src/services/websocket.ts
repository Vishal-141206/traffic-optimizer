import { useTrafficStore } from '@/store/trafficStore'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

type MessageHandler = (data: any) => void

class WebSocketService {
  private socket: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private messageHandlers: Map<string, MessageHandler[]> = new Map()
  private isConnecting = false

  connect(endpoint: string = '/ws/dashboard'): void {
    if (this.socket?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }

    this.isConnecting = true
    const url = `${WS_BASE_URL}${endpoint}`
    
    try {
      this.socket = new WebSocket(url)
      
      this.socket.onopen = () => {
        console.log('🔌 WebSocket connected')
        this.isConnecting = false
        this.reconnectAttempts = 0
        useTrafficStore.getState().setConnected(true)
        
        // Send initial ping
        this.send({ type: 'ping' })
      }

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.socket.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason)
        this.isConnecting = false
        useTrafficStore.getState().setConnected(false)
        this.attemptReconnect(endpoint)
      }

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnecting = false
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.isConnecting = false
    }
  }

  private handleMessage(message: any): void {
    const { type, data, timestamp } = message
    
    // Update last update timestamp
    if (timestamp) {
      useTrafficStore.getState().setLastUpdate(timestamp)
    }

    // Route to appropriate handler based on message type
    switch (type) {
      case 'connected':
        console.log('✅ WebSocket handshake complete')
        break
        
      case 'pong':
        // Heartbeat response
        break
        
      case 'traffic_update':
        useTrafficStore.getState().handleTrafficUpdate(data)
        break
        
      case 'signal_update':
        useTrafficStore.getState().handleSignalUpdate(data)
        break
        
      case 'emergency_alert':
        useTrafficStore.getState().handleEmergencyAlert(data)
        break
        
      default:
        console.log('Unknown message type:', type)
    }

    // Call registered handlers
    const handlers = this.messageHandlers.get(type) || []
    handlers.forEach((handler) => handler(data))
    
    // Also call 'all' handlers
    const allHandlers = this.messageHandlers.get('*') || []
    allHandlers.forEach((handler) => handler(message))
  }

  private attemptReconnect(endpoint: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    console.log(`Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`)

    setTimeout(() => {
      this.connect(endpoint)
    }, this.reconnectDelay)
  }

  send(data: any): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }

  subscribe(type: string, handler: MessageHandler): () => void {
    const handlers = this.messageHandlers.get(type) || []
    handlers.push(handler)
    this.messageHandlers.set(type, handlers)

    // Return unsubscribe function
    return () => {
      const currentHandlers = this.messageHandlers.get(type) || []
      const index = currentHandlers.indexOf(handler)
      if (index > -1) {
        currentHandlers.splice(index, 1)
      }
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.messageHandlers.clear()
  }

  get isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN
  }

  // Specific subscription methods
  subscribeToTraffic(handler: MessageHandler): () => void {
    return this.subscribe('traffic_update', handler)
  }

  subscribeToSignals(handler: MessageHandler): () => void {
    return this.subscribe('signal_update', handler)
  }

  subscribeToEmergencies(handler: MessageHandler): () => void {
    return this.subscribe('emergency_alert', handler)
  }

  subscribeToAll(handler: MessageHandler): () => void {
    return this.subscribe('*', handler)
  }

  // Send subscription request for specific intersection
  subscribeToIntersection(intersectionId: number): void {
    this.send({
      type: 'subscribe',
      intersection_id: intersectionId,
    })
  }

  // Request immediate update
  requestUpdate(): void {
    this.send({ type: 'request_update' })
  }

  // Ping to keep connection alive
  ping(): void {
    this.send({ type: 'ping' })
  }
}

// Singleton instance
export const wsService = new WebSocketService()

// React hook for WebSocket
export function useWebSocket(endpoint?: string) {
  const isConnected = useTrafficStore((state) => state.isConnected)

  const connect = () => wsService.connect(endpoint)
  const disconnect = () => wsService.disconnect()
  const send = (data: any) => wsService.send(data)
  const subscribe = (type: string, handler: MessageHandler) =>
    wsService.subscribe(type, handler)

  return {
    isConnected,
    connect,
    disconnect,
    send,
    subscribe,
    subscribeToTraffic: wsService.subscribeToTraffic.bind(wsService),
    subscribeToSignals: wsService.subscribeToSignals.bind(wsService),
    subscribeToEmergencies: wsService.subscribeToEmergencies.bind(wsService),
    subscribeToIntersection: wsService.subscribeToIntersection.bind(wsService),
    requestUpdate: wsService.requestUpdate.bind(wsService),
  }
}
