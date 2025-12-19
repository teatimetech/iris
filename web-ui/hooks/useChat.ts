import { useState, useCallback } from 'react'
import { sendChatMessage } from '@/lib/api'
import type { Message } from '@/lib/types'

interface UseChatReturn {
    messages: Message[]
    isLoading: boolean
    sendMessage: (content: string) => Promise<void>
}

export function useChat(initialMessages: Message[] = [], userId: string = 'test-user'): UseChatReturn {
    const [messages, setMessages] = useState<Message[]>(initialMessages)
    const [isLoading, setIsLoading] = useState(false)

    const sendMessage = useCallback(async (content: string) => {
        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content,
            timestamp: new Date(),
        }

        setMessages((prev) => [...prev, userMessage])
        setIsLoading(true)

        try {
            const response = await sendChatMessage(userId, content)

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response,
                timestamp: new Date(),
            }

            setMessages((prev) => [...prev, aiMessage])
        } catch (error) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date(),
            }
            setMessages((prev) => [...prev, errorMessage])
        } finally {
            setIsLoading(false)
        }
    }, [])

    return {
        messages,
        isLoading,
        sendMessage,
    }
}
