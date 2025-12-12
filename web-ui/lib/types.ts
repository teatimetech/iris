export interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
}

export interface ChatRequest {
    user_id: string
    prompt: string
}

export interface ChatResponse {
    response: string
}

export interface Portfolio {
    totalValue: number
    todayPL: number
    todayPLPercent: number
    holdings: Holding[]
    allocation: AllocationData[]
    performance: PerformanceData[]
}

export interface Holding {
    symbol: string
    name: string
    shares: number
    price: number
    value: number
    change: number
    changePercent: number
}

export interface AllocationData {
    name: string
    value: number
    color: string
}

export interface PerformanceData {
    date: string
    value: number
}
