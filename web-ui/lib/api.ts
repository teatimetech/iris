import axios from 'axios'
import type { ChatRequest, ChatResponse } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

export const sendChatMessage = async (userId: string, prompt: string): Promise<string> => {
    try {
        const request: ChatRequest = { user_id: userId, prompt }
        const response = await api.post<ChatResponse>('/v1/chat', request)
        return response.data.response
    } catch (error) {
        console.error('Chat API error:', error)
        throw new Error('Failed to get response from AI. Please try again.')
    }
}

export const checkHealth = async (): Promise<boolean> => {
    try {
        const response = await api.get('/health')
        return response.data.status === 'healthy'
    } catch (error) {
        return false
    }
}

export const getPortfolio = async (userId: string): Promise<any> => {
    try {
        const response = await api.get(`/v1/portfolio/${userId}`)
        return response.data
    } catch (error) {
        console.error('Portfolio API error:', error)
        throw new Error('Failed to fetch portfolio data. Please try again.')
    }
}

export default api
