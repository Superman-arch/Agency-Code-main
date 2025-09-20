import React, { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { Toaster } from 'react-hot-toast'
import { useStore } from '../store/appStore'
import Sidebar from '../components/Sidebar'
import ChatPanel from '../components/ChatPanel'
import { Panel, PanelGroup, PanelResizeHandle } from '../components/ResizablePanels'

const CodeEditor = dynamic(() => import('../components/CodeEditor'), { ssr: false })
const Terminal = dynamic(() => import('../components/Terminal'), { ssr: false })

export default function Home() {
  const { theme, toggleTheme } = useStore()
  const [activeTab, setActiveTab] = useState('chat')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-gray-50 dark:bg-gray-900">
      <Toaster position="top-right" />
      
      {/* Sidebar */}
      <div className="w-64 border-r border-gray-200 dark:border-gray-700">
        <Sidebar />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 bg-white dark:bg-gray-800">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Qwen Coder Interface
            </h1>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Powered by Qwen2.5-Coder-7B-Instruct
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 flex">
          <PanelGroup direction="horizontal">
            {/* Chat/Code Panel */}
            <Panel defaultSize={50} minSize={30}>
              <div className="h-full flex flex-col">
                {/* Tabs */}
                <div className="h-10 border-b border-gray-200 dark:border-gray-700 flex">
                  <button
                    onClick={() => setActiveTab('chat')}
                    className={`px-4 py-2 text-sm font-medium ${
                      activeTab === 'chat'
                        ? 'text-qwen-primary border-b-2 border-qwen-primary'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    Chat
                  </button>
                  <button
                    onClick={() => setActiveTab('code')}
                    className={`px-4 py-2 text-sm font-medium ${
                      activeTab === 'code'
                        ? 'text-qwen-primary border-b-2 border-qwen-primary'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    Code Editor
                  </button>
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-hidden">
                  {activeTab === 'chat' ? (
                    <ChatPanel />
                  ) : (
                    <CodeEditor />
                  )}
                </div>
              </div>
            </Panel>

            <PanelResizeHandle className="w-1 bg-gray-200 dark:bg-gray-700 hover:bg-qwen-primary transition-colors" />

            {/* Terminal Panel */}
            <Panel defaultSize={50} minSize={30}>
              <div className="h-full flex flex-col">
                <div className="h-10 border-b border-gray-200 dark:border-gray-700 flex items-center px-4 bg-gray-50 dark:bg-gray-800">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Terminal
                  </span>
                </div>
                <div className="flex-1">
                  <Terminal />
                </div>
              </div>
            </Panel>
          </PanelGroup>
        </div>
      </div>
    </div>
  )
}