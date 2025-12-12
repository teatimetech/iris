'use client'

import { useState, FormEvent } from 'react'

interface ChatInputProps {
    onSend: (message: string) => void
    isLoading: boolean
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
    const [input, setInput] = useState('')

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault()
        if (input.trim() && !isLoading) {
            onSend(input.trim())
            setInput('')
        }
    }

    return (
        <form onSubmit={handleSubmit} className="flex gap-2">
            <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about stocks, portfolio, or investment strategies..."
                className="flex-1 glass px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
            />
            <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl font-medium text-sm hover:shadow-lg hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
                {isLoading ? '...' : 'Send'}
            </button>
        </form>
    )
}
