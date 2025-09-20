import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  // Theme
  theme: 'light' | 'dark'
  toggleTheme: () => void
  
  // Session
  sessionId: string | null
  setSessionId: (id: string) => void
  
  // Files
  openFiles: string[]
  currentFile: string | null
  addOpenFile: (path: string) => void
  removeOpenFile: (path: string) => void
  setCurrentFile: (path: string | null) => void
  
  // Terminal
  terminalHistory: string[]
  addToTerminalHistory: (command: string) => void
  
  // Settings
  fontSize: number
  setFontSize: (size: number) => void
  autoSave: boolean
  toggleAutoSave: () => void
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Theme
      theme: 'dark',
      toggleTheme: () => set((state) => ({ 
        theme: state.theme === 'dark' ? 'light' : 'dark' 
      })),
      
      // Session
      sessionId: null,
      setSessionId: (id) => set({ sessionId: id }),
      
      // Files
      openFiles: [],
      currentFile: null,
      addOpenFile: (path) => set((state) => ({
        openFiles: state.openFiles.includes(path) 
          ? state.openFiles 
          : [...state.openFiles, path],
        currentFile: path
      })),
      removeOpenFile: (path) => set((state) => ({
        openFiles: state.openFiles.filter(f => f !== path),
        currentFile: state.currentFile === path 
          ? state.openFiles[0] || null 
          : state.currentFile
      })),
      setCurrentFile: (path) => set({ currentFile: path }),
      
      // Terminal
      terminalHistory: [],
      addToTerminalHistory: (command) => set((state) => ({
        terminalHistory: [...state.terminalHistory, command].slice(-100)
      })),
      
      // Settings
      fontSize: 14,
      setFontSize: (size) => set({ fontSize: size }),
      autoSave: false,
      toggleAutoSave: () => set((state) => ({ 
        autoSave: !state.autoSave 
      })),
    }),
    {
      name: 'qwen-coder-storage',
    }
  )
)