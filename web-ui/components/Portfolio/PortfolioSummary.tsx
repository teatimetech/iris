'use client'

import type { Portfolio } from '@/lib/types'

interface PortfolioSummaryProps {
    portfolio: Portfolio
}

export default function PortfolioSummary({ portfolio }: PortfolioSummaryProps) {
    return (
        <div className="glass-card p-6">
            <h2 className="text-2xl font-bold mb-4">Portfolio Overview</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <p className="text-sm text-gray-400 mb-1">Total Value</p>
                    <p className="text-3xl font-bold">${portfolio.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                </div>

                <div>
                    <p className="text-sm text-gray-400 mb-1">Today's P/L</p>
                    <p className={`text-3xl font-bold ${portfolio.todayPL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {portfolio.todayPL >= 0 ? '+' : ''}${portfolio.todayPL.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                </div>

                <div>
                    <p className="text-sm text-gray-400 mb-1">Change</p>
                    <p className={`text-3xl font-bold ${portfolio.todayPLPercent >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {portfolio.todayPLPercent >= 0 ? '+' : ''}{portfolio.todayPLPercent.toFixed(2)}%
                    </p>
                </div>
            </div>
        </div>
    )
}
