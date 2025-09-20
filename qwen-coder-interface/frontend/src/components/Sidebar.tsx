import React, { useState, useEffect } from 'react'
import { 
  Folder, 
  FolderOpen, 
  File, 
  ChevronRight, 
  ChevronDown,
  RefreshCw,
  Plus,
  Trash2
} from 'lucide-react'
import toast from 'react-hot-toast'
import { terminalApi, filesApi } from '../services/api'
import { useStore } from '../store/appStore'

interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
  size?: number
  modified?: string
}

export default function Sidebar() {
  const [fileTree, setFileTree] = useState<FileNode | null>(null)
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)
  const { addOpenFile, currentFile, theme } = useStore()

  useEffect(() => {
    loadFileTree()
  }, [])

  const loadFileTree = async () => {
    setLoading(true)
    try {
      const tree = await terminalApi.getFileTree('.', 5)
      setFileTree(tree)
    } catch (error) {
      toast.error('Failed to load file tree')
      console.error('File tree error:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleDir = (path: string) => {
    setExpandedDirs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(path)) {
        newSet.delete(path)
      } else {
        newSet.add(path)
      }
      return newSet
    })
  }

  const handleFileClick = async (node: FileNode) => {
    if (node.type === 'directory') {
      toggleDir(node.path)
    } else {
      try {
        const fileData = await filesApi.read(node.path)
        addOpenFile(node.path)
        toast.success(`Opened ${node.name}`)
      } catch (error) {
        toast.error(`Failed to open ${node.name}`)
        console.error('File open error:', error)
      }
    }
  }

  const handleDelete = async (node: FileNode, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm(`Delete ${node.name}?`)) return
    
    try {
      await filesApi.delete(node.path)
      toast.success(`Deleted ${node.name}`)
      loadFileTree()
    } catch (error) {
      toast.error(`Failed to delete ${node.name}`)
      console.error('Delete error:', error)
    }
  }

  const renderNode = (node: FileNode, level: number = 0) => {
    const isExpanded = expandedDirs.has(node.path)
    const isDirectory = node.type === 'directory'
    const isSelected = currentFile === node.path

    return (
      <div key={node.path}>
        <div
          className={`
            flex items-center px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer
            ${isSelected ? 'bg-qwen-primary bg-opacity-20' : ''}
          `}
          style={{ paddingLeft: `${level * 12 + 8}px` }}
          onClick={() => handleFileClick(node)}
        >
          {isDirectory && (
            isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
          )}
          
          {isDirectory ? (
            isExpanded ? <FolderOpen size={16} className="ml-1 text-yellow-600" /> 
                       : <Folder size={16} className="ml-1 text-yellow-600" />
          ) : (
            <File size={16} className="ml-3 text-gray-500" />
          )}
          
          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 flex-1 truncate">
            {node.name}
          </span>
          
          {!isDirectory && (
            <button
              onClick={(e) => handleDelete(node, e)}
              className="opacity-0 hover:opacity-100 p-1 hover:bg-red-500 hover:text-white rounded"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
        
        {isDirectory && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="h-14 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4">
        <h2 className="font-semibold text-gray-900 dark:text-white">Files</h2>
        <button
          onClick={loadFileTree}
          disabled={loading}
          className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>
      
      {/* File Tree */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center text-gray-500">
            Loading files...
          </div>
        ) : fileTree ? (
          <div className="py-2">
            {renderNode(fileTree)}
          </div>
        ) : (
          <div className="p-4 text-center text-gray-500">
            No files found
          </div>
        )}
      </div>
      
      {/* Footer */}
      <div className="h-12 border-t border-gray-200 dark:border-gray-700 flex items-center justify-center">
        <button className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
          Project Settings
        </button>
      </div>
    </div>
  )
}