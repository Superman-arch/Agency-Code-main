import React, { useState, useRef, useEffect, ReactNode } from 'react'

interface PanelProps {
  children: ReactNode
  defaultSize?: number
  minSize?: number
  maxSize?: number
}

interface PanelGroupProps {
  children: ReactNode[]
  direction: 'horizontal' | 'vertical'
}

interface PanelResizeHandleProps {
  className?: string
}

export const Panel: React.FC<PanelProps> = ({ 
  children, 
  defaultSize = 50, 
  minSize = 10,
  maxSize = 90 
}) => {
  return (
    <div 
      className="h-full overflow-hidden"
      style={{ flex: `${defaultSize} ${defaultSize} 0%` }}
      data-min-size={minSize}
      data-max-size={maxSize}
    >
      {children}
    </div>
  )
}

export const PanelResizeHandle: React.FC<PanelResizeHandleProps> = ({ className = '' }) => {
  const [isDragging, setIsDragging] = useState(false)

  return (
    <div
      className={`
        ${className}
        ${isDragging ? 'cursor-col-resize' : 'cursor-col-resize hover:bg-qwen-primary'}
        transition-colors select-none
      `}
      onMouseDown={() => setIsDragging(true)}
      onMouseUp={() => setIsDragging(false)}
      onMouseLeave={() => setIsDragging(false)}
    />
  )
}

export const PanelGroup: React.FC<PanelGroupProps> = ({ children, direction }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [sizes, setSizes] = useState<number[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [dragIndex, setDragIndex] = useState<number | null>(null)

  useEffect(() => {
    // Initialize sizes based on default sizes
    const panels = React.Children.toArray(children).filter(
      (child) => React.isValidElement(child) && child.type === Panel
    )
    
    if (panels.length > 0) {
      const initialSizes = panels.map((panel) => {
        if (React.isValidElement(panel)) {
          return panel.props.defaultSize || 50
        }
        return 50
      })
      setSizes(initialSizes)
    }
  }, [children])

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || dragIndex === null || !containerRef.current) return

    const container = containerRef.current
    const rect = container.getBoundingClientRect()
    
    let position: number
    if (direction === 'horizontal') {
      position = ((e.clientX - rect.left) / rect.width) * 100
    } else {
      position = ((e.clientY - rect.top) / rect.height) * 100
    }

    const newSizes = [...sizes]
    const panels = React.Children.toArray(children).filter(
      (child) => React.isValidElement(child) && child.type === Panel
    )

    // Get min/max constraints
    const panel1 = panels[dragIndex] as React.ReactElement
    const panel2 = panels[dragIndex + 1] as React.ReactElement
    
    const minSize1 = panel1.props.minSize || 10
    const maxSize1 = panel1.props.maxSize || 90
    const minSize2 = panel2.props.minSize || 10
    const maxSize2 = panel2.props.maxSize || 90

    // Calculate new sizes
    const totalSize = newSizes[dragIndex] + newSizes[dragIndex + 1]
    let newSize1 = position - newSizes.slice(0, dragIndex).reduce((a, b) => a + b, 0)
    let newSize2 = totalSize - newSize1

    // Apply constraints
    newSize1 = Math.max(minSize1, Math.min(maxSize1, newSize1))
    newSize2 = Math.max(minSize2, Math.min(maxSize2, newSize2))

    // Ensure total size is preserved
    if (newSize1 + newSize2 !== totalSize) {
      const diff = totalSize - (newSize1 + newSize2)
      if (newSize1 < maxSize1) {
        newSize1 += diff
      } else if (newSize2 < maxSize2) {
        newSize2 += diff
      }
    }

    newSizes[dragIndex] = newSize1
    newSizes[dragIndex + 1] = newSize2

    setSizes(newSizes)
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    setDragIndex(null)
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isDragging, dragIndex, sizes, direction])

  const renderChildren = () => {
    const result: ReactNode[] = []
    let panelIndex = 0

    React.Children.forEach(children, (child, index) => {
      if (React.isValidElement(child)) {
        if (child.type === Panel) {
          const size = sizes[panelIndex] || 50
          result.push(
            <div
              key={`panel-${panelIndex}`}
              style={{
                flex: `${size} ${size} 0%`,
                overflow: 'hidden'
              }}
            >
              {child.props.children}
            </div>
          )
          panelIndex++
        } else if (child.type === PanelResizeHandle && panelIndex > 0) {
          result.push(
            <div
              key={`handle-${index}`}
              className={`
                ${child.props.className || ''}
                ${direction === 'horizontal' ? 'w-1 cursor-col-resize' : 'h-1 cursor-row-resize'}
                bg-gray-200 dark:bg-gray-700 hover:bg-qwen-primary transition-colors select-none
              `}
              onMouseDown={() => {
                setIsDragging(true)
                setDragIndex(panelIndex - 1)
              }}
            />
          )
        }
      }
    })

    return result
  }

  return (
    <div
      ref={containerRef}
      className={`
        h-full w-full flex
        ${direction === 'horizontal' ? 'flex-row' : 'flex-col'}
      `}
    >
      {renderChildren()}
    </div>
  )
}