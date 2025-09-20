import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const chatApi = {
  generate: async (data: {
    message: string
    session_id?: string
    context?: any[]
    max_tokens?: number
    temperature?: number
    top_p?: number
  }) => {
    const response = await api.post('/api/chat/generate', data)
    return response.data
  },

  analyzeCode: async (data: {
    code: string
    analysis_type: string
    session_id?: string
  }) => {
    const response = await api.post('/api/chat/analyze-code', data)
    return response.data
  },

  getCompletions: async (data: {
    code: string
    position: { line: number; column: number }
    num_suggestions?: number
  }) => {
    const response = await api.post('/api/chat/complete', data)
    return response.data
  },

  getContext: async (sessionId: string, limit?: number) => {
    const response = await api.get(`/api/chat/sessions/${sessionId}/context`, {
      params: { limit }
    })
    return response.data
  },

  clearSession: async (sessionId: string) => {
    const response = await api.delete(`/api/chat/sessions/${sessionId}`)
    return response.data
  },
}

export const terminalApi = {
  execute: async (data: {
    command: string
    session_id?: string
    working_dir?: string
    env?: Record<string, string>
    timeout?: number
  }) => {
    const response = await api.post('/api/terminal/execute', data)
    return response.data
  },

  createSession: async (sessionId?: string) => {
    const response = await api.post('/api/terminal/session/create', { session_id: sessionId })
    return response.data
  },

  killSession: async (sessionId: string) => {
    const response = await api.delete(`/api/terminal/session/${sessionId}`)
    return response.data
  },

  getFileTree: async (path: string = '.', maxDepth: number = 3) => {
    const response = await api.get('/api/terminal/file-tree', {
      params: { path, max_depth: maxDepth }
    })
    return response.data
  },
}

export const filesApi = {
  read: async (path: string) => {
    const response = await api.post('/api/files/read', { path })
    return response.data
  },

  write: async (data: { path: string; content: string }) => {
    const response = await api.post('/api/files/write', {
      path: data.path,
      content: data.content,
      operation: 'write'
    })
    return response.data
  },

  delete: async (path: string) => {
    const response = await api.post('/api/files/delete', { path })
    return response.data
  },

  rename: async (oldPath: string, newPath: string) => {
    const response = await api.post('/api/files/rename', {
      old_path: oldPath,
      new_path: newPath
    })
    return response.data
  },

  list: async (path: string = '.', showHidden: boolean = false) => {
    const response = await api.get('/api/files/list', {
      params: { path, show_hidden: showHidden }
    })
    return response.data
  },

  upload: async (file: File, path: string = '.') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('path', path)

    const response = await api.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectTimeout: NodeJS.Timeout | null = null
  private messageHandlers: Map<string, (data: any) => void> = new Map()

  connect(sessionId: string) {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/${sessionId}`
    
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const handler = this.messageHandlers.get(data.type)
        if (handler) {
          handler(data)
        }
      } catch (error) {
        console.error('WebSocket message error:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.reconnect(sessionId)
    }
  }

  private reconnect(sessionId: string) {
    if (this.reconnectTimeout) return
    
    this.reconnectTimeout = setTimeout(() => {
      console.log('Reconnecting WebSocket...')
      this.connect(sessionId)
      this.reconnectTimeout = null
    }, 3000)
  }

  on(type: string, handler: (data: any) => void) {
    this.messageHandlers.set(type, handler)
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

export default api