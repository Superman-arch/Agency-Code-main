import React, { useEffect, useRef } from 'react'
import { Terminal as XTerm } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import 'xterm/css/xterm.css'
import { terminalApi } from '../services/api'
import { useStore } from '../store/appStore'

export default function Terminal() {
  const terminalRef = useRef<HTMLDivElement>(null)
  const xtermRef = useRef<XTerm | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  const { sessionId } = useStore()

  useEffect(() => {
    if (!terminalRef.current) return

    // Create terminal instance
    const term = new XTerm({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'JetBrains Mono, Fira Code, monospace',
      theme: {
        background: '#1e1e2e',
        foreground: '#cdd6f4',
        cursor: '#f5e0dc',
        black: '#45475a',
        red: '#f38ba8',
        green: '#a6e3a1',
        yellow: '#f9e2af',
        blue: '#89b4fa',
        magenta: '#f5c2e7',
        cyan: '#94e2d5',
        white: '#bac2de',
        brightBlack: '#585b70',
        brightRed: '#f38ba8',
        brightGreen: '#a6e3a1',
        brightYellow: '#f9e2af',
        brightBlue: '#89b4fa',
        brightMagenta: '#f5c2e7',
        brightCyan: '#94e2d5',
        brightWhite: '#a6adc8'
      }
    })

    // Add addons
    const fitAddon = new FitAddon()
    const webLinksAddon = new WebLinksAddon()
    
    term.loadAddon(fitAddon)
    term.loadAddon(webLinksAddon)
    
    // Open terminal
    term.open(terminalRef.current)
    fitAddon.fit()

    // Store refs
    xtermRef.current = term
    fitAddonRef.current = fitAddon

    // Welcome message
    term.writeln('Welcome to Qwen Coder Terminal')
    term.writeln('Type commands to execute them on the server')
    term.write('\r\n$ ')

    // Command buffer
    let commandBuffer = ''
    let historyIndex = -1
    const commandHistory: string[] = []

    // Handle input
    term.onData((data) => {
      const code = data.charCodeAt(0)

      // Handle special keys
      if (code === 13) { // Enter
        if (commandBuffer.trim()) {
          commandHistory.push(commandBuffer)
          historyIndex = commandHistory.length
          
          // Execute command
          executeCommand(commandBuffer)
          commandBuffer = ''
        } else {
          term.write('\r\n$ ')
        }
      } else if (code === 127) { // Backspace
        if (commandBuffer.length > 0) {
          commandBuffer = commandBuffer.slice(0, -1)
          term.write('\b \b')
        }
      } else if (code === 3) { // Ctrl+C
        commandBuffer = ''
        term.write('^C\r\n$ ')
      } else if (code === 27) { // Escape sequences (arrows)
        // Handle arrow keys for history
        if (data === '\x1b[A' && historyIndex > 0) { // Up arrow
          // Clear current line
          term.write('\r\x1b[K$ ')
          historyIndex--
          commandBuffer = commandHistory[historyIndex]
          term.write(commandBuffer)
        } else if (data === '\x1b[B' && historyIndex < commandHistory.length - 1) { // Down arrow
          term.write('\r\x1b[K$ ')
          historyIndex++
          commandBuffer = commandHistory[historyIndex]
          term.write(commandBuffer)
        }
      } else if (code >= 32) { // Printable characters
        commandBuffer += data
        term.write(data)
      }
    })

    // Execute command function
    const executeCommand = async (command: string) => {
      term.write('\r\n')
      
      try {
        const result = await terminalApi.execute({
          command,
          session_id: sessionId || 'default',
          working_dir: '.'
        })

        if (result.success) {
          if (result.output) {
            term.write(result.output.replace(/\n/g, '\r\n'))
          }
        } else {
          term.write(`\x1b[31mError: ${result.error || 'Command failed'}\x1b[0m`)
        }
      } catch (error) {
        term.write(`\x1b[31mError: Failed to execute command\x1b[0m`)
        console.error('Terminal error:', error)
      }
      
      term.write('\r\n$ ')
    }

    // Handle resize
    const handleResize = () => {
      if (fitAddonRef.current) {
        fitAddonRef.current.fit()
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      term.dispose()
    }
  }, [sessionId])

  return (
    <div 
      ref={terminalRef} 
      className="h-full w-full bg-terminal-bg"
      style={{ padding: '8px' }}
    />
  )
}