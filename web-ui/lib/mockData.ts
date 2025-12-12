import type { Portfolio } from './types'

// Mock portfolio data - replace with real API call later
export const getMockPortfolio = (): Portfolio => {
    return {
        totalValue: 125450.32,
        todayPL: 2340.12,
        todayPLPercent: 1.9,
        holdings: [
            {
                symbol: 'NVDA',
                name: 'NVIDIA Corporation',
                shares: 50,
                price: 495.22,
                value: 24761.00,
                change: 12.45,
                changePercent: 2.58,
            },
            {
                symbol: 'AAPL',
                name: 'Apple Inc.',
                shares: 100,
                price: 185.92,
                value: 18592.00,
                change: -1.23,
                changePercent: -0.66,
            },
            {
                symbol: 'MSFT',
                name: 'Microsoft Corporation',
                shares: 75,
                price: 378.91,
                value: 28418.25,
                change: 5.67,
                changePercent: 1.52,
            },
            {
                symbol: 'TSLA',
                name: 'Tesla, Inc.',
                shares: 40,
                price: 242.64,
                value: 9705.60,
                change: -3.21,
                changePercent: -1.31,
            },
            {
                symbol: 'GOOGL',
                name: 'Alphabet Inc.',
                shares: 120,
                price: 140.93,
                value: 16911.60,
                change: 2.34,
                changePercent: 1.69,
            },
        ],
        allocation: [
            { name: 'Technology', value: 65, color: '#3b82f6' },
            { name: 'Healthcare', value: 15, color: '#10b981' },
            { name: 'Finance', value: 12, color: '#f59e0b' },
            { name: 'Consumer', value: 8, color: '#ef4444' },
        ],
        performance: Array.from({ length: 30 }, (_, i) => ({
            date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            value: 120000 + Math.random() * 8000 + i * 200,
        })),
    }
}
