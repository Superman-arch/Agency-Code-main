import React, { useState, useRef } from 'react'
import Editor from '@monaco-editor/react'
import { Save, Play, FileText, Download, Upload } from 'lucide-react'
import toast from 'react-hot-toast'
import { filesApi } from '../services/api'
import { useStore } from '../store/appStore'

export default function CodeEditor() {
  const [code, setCode] = useState(`# Welcome to Qwen Coder Editor
# Start coding here...

def hello_world():
    print("Hello from Qwen Coder!")
    
if __name__ == "__main__":
    hello_world()
`)
  const [fileName, setFileName] = useState('main.py')
  const [language, setLanguage] = useState('python')
  const editorRef = useRef<any>(null)
  const { theme } = useStore()

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor
    editor.focus()
  }

  const detectLanguage = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase()
    const languageMap: { [key: string]: string } = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'cs': 'csharp',
      'go': 'go',
      'rs': 'rust',
      'rb': 'ruby',
      'php': 'php',
      'swift': 'swift',
      'kt': 'kotlin',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'json': 'json',
      'xml': 'xml',
      'yaml': 'yaml',
      'yml': 'yaml',
      'md': 'markdown',
      'sql': 'sql',
      'sh': 'shell',
      'bash': 'shell'
    }
    return languageMap[ext || ''] || 'plaintext'
  }

  const handleSave = async () => {
    try {
      await filesApi.write({
        path: fileName,
        content: code
      })
      toast.success(`Saved ${fileName}`)
    } catch (error) {
      toast.error('Failed to save file')
      console.error('Save error:', error)
    }
  }

  const handleLoad = async () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.go,.rs,.html,.css,.json,.yaml,.yml'
    
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      const reader = new FileReader()
      reader.onload = (event) => {
        const content = event.target?.result as string
        setCode(content)
        setFileName(file.name)
        setLanguage(detectLanguage(file.name))
        toast.success(`Loaded ${file.name}`)
      }
      reader.readAsText(file)
    }
    
    input.click()
  }

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    a.click()
    URL.revokeObjectURL(url)
    toast.success(`Downloaded ${fileName}`)
  }

  const handleRun = async () => {
    // This would integrate with the terminal service to run the code
    toast.info('Running code in terminal...')
    // Implementation would send code to terminal service
  }

  const handleFileNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newName = e.target.value
    setFileName(newName)
    setLanguage(detectLanguage(newName))
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Toolbar */}
      <div className="h-12 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 bg-gray-50 dark:bg-gray-800">
        <div className="flex items-center space-x-4">
          <FileText className="w-5 h-5 text-gray-500" />
          <input
            type="text"
            value={fileName}
            onChange={handleFileNameChange}
            className="px-2 py-1 text-sm bg-transparent border-b border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-qwen-primary"
          />
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Language: {language}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleLoad}
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="Load file"
          >
            <Upload className="w-4 h-4" />
          </button>
          <button
            onClick={handleSave}
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="Save file"
          >
            <Save className="w-4 h-4" />
          </button>
          <button
            onClick={handleDownload}
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            title="Download file"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={handleRun}
            className="p-2 rounded bg-green-500 hover:bg-green-600 text-white transition-colors"
            title="Run code"
          >
            <Play className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1">
        <Editor
          value={code}
          language={language}
          theme={theme === 'dark' ? 'vs-dark' : 'vs'}
          onChange={(value) => setCode(value || '')}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: 'JetBrains Mono, Fira Code, monospace',
            automaticLayout: true,
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            suggest: {
              showMethods: true,
              showFunctions: true,
              showConstructors: true,
              showFields: true,
              showVariables: true,
              showClasses: true,
              showStructs: true,
              showInterfaces: true,
              showModules: true,
              showProperties: true,
              showEvents: true,
              showOperators: true,
              showUnits: true,
              showValues: true,
              showConstants: true,
              showEnums: true,
              showEnumMembers: true,
              showKeywords: true,
              showWords: true,
              showColors: true,
              showFiles: true,
              showReferences: true,
              showFolders: true,
              showTypeParameters: true,
              showSnippets: true,
            }
          }}
        />
      </div>
    </div>
  )
}