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

export interface Holding {
    symbol: string
    name: string
    shares: number
    price: number
    costBasisPerShare: number  // NEW: Per-share cost basis
    value: number
    costBasis: number          // NEW: Total cost basis
    change: number
    changePercent: number
    gainLoss: number           // NEW: Total gain/loss in dollars
    gainLossPercent: number    // NEW: Total gain/loss percentage
}

export interface BrokerGroup {
    brokerId: number
    brokerName: string
    displayName: string        // e.g., "Fidelity Investments"
    accountNumber: string
    irisAccountNumber?: string // NEW
    irisAccountId?: string     // NEW
    portfolioId: number
    portfolioName: string
    totalValue: number
    totalCost: number
    gainLoss: number
    gainLossPercent: number
    cashBalance: number        // NEW (matches backend JSON)
    buyingPower: number        // NEW
    holdings: Holding[]
}

export interface Portfolio {
    // Overall metrics
    totalValue: number
    cashBalance: number        // NEW
    totalCost: number          // NEW
    totalGainLoss: number      // NEW
    totalGainLossPercent: number // NEW

    // Formatted P/L strings (e.g., "$+1,234.56 (5.67%)")
    todayPL: string            // CHANGED: now string, not number
    ytdPL: string              // NEW
    overallPL: string          // NEW

    // Raw values for calculations
    todayPLValue: number       // NEW: raw Today's P/L value
    todayPLPercent: number
    ytdPLValue: number         // NEW: raw YTD P/L value
    ytdPLPercent: number       // NEW

    // Broker-grouped holdings
    brokerGroups: BrokerGroup[] // NEW: Main way to access holdings

    // Legacy flat holdings (for backward compatibility)
    holdings: Holding[]
    allocation: AllocationData[]
    performance: PerformanceData[]
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
