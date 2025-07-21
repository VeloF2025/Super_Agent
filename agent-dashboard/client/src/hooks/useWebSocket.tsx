import { useState, useEffect, useCallback, useRef } from 'react'

interface WebSocketOptions {
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: (data: any) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export default function useWebSocket(url: string, options: WebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)
  const ws = useRef<WebSocket | null>(null)
  const reconnectCount = useRef(0)
  const reconnectTimeout = useRef<NodeJS.Timeout>()

  const {
    onOpen,
    onClose,
    onError,
    onMessage,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10
  } = options

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        reconnectCount.current = 0
        onOpen?.()
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        onClose?.()

        // Attempt to reconnect
        if (reconnectCount.current < maxReconnectAttempts) {
          reconnectTimeout.current = setTimeout(() => {
            console.log(`Reconnecting... (attempt ${reconnectCount.current + 1})`)
            reconnectCount.current++
            connect()
          }, reconnectInterval)
        }
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        onError?.(error)
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          onMessage?.(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [url, onOpen, onClose, onError, onMessage, reconnectInterval, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current)
    }
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
  }, [])

  const sendMessage = useCallback((data: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data))
    } else {
      console.error('WebSocket is not connected')
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect
  }
}