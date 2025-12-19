'use client'

import { useRef, useEffect } from 'react'
import { useAuth } from '@/app/context/AuthContext'
import { useChat } from '@/hooks/useChat'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import TypingIndicator from './TypingIndicator'

interface ChatPanelProps {
    onViewChange: (view: 'portfolio' | 'analysis' | 'insights') => void
}

export default function ChatPanel({ onViewChange }: ChatPanelProps) {
    const { user } = useAuth()
    const { messages, isLoading, sendMessage } = useChat([], user?.id || '')
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    return (
        <div className="h-full flex flex-col">
            {/* Chat Header */}
            <div className="glass-card border-b border-white/10 px-4 py-3">
                <div className="flex justify-between items-center mb-2">
                    <div>
                        <h2 className="font-semibold">Chat with IRIS</h2>
                        <p className="text-xs text-gray-400">AI-powered investment advisor</p>
                    </div>
                </div>
                <div className="flex gap-2 text-xs">
                    <button onClick={() => onViewChange('portfolio')} className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">Portfolio</button>
                    <button onClick={() => onViewChange('analysis')} className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">Analysis</button>
                    <button onClick={() => onViewChange('insights')} className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">Insights</button>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                ))}
                {isLoading && <TypingIndicator />}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-white/10">
                <ChatInput onSend={sendMessage} isLoading={isLoading} />
            </div>
        </div>
    )
}
