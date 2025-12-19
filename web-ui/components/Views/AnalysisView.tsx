'use client'

import { useAuth } from '@/app/context/AuthContext'
import { usePortfolio } from '@/hooks/usePortfolio'
import LoadingSkeleton from '../Portfolio/LoadingSkeleton'
import ErrorDisplay from '../Common/ErrorDisplay'

export default function AnalysisView() {
    const { user } = useAuth()
    const { data: portfolio, error, isLoading, mutate } = usePortfolio(user?.id.toString() || '')

    if (isLoading) return <LoadingSkeleton />
    if (error) return <ErrorDisplay message={error.message} onRetry={mutate} />
    if (!portfolio) return <ErrorDisplay message="No portfolio data available" />

    // Mock risk calculation based on allocation
    const riskScore = 7.5 // Out of 10
    const riskLevel = 'High Growth'

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            <h2 className="text-2xl font-bold mb-6">Portfolio Analysis</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Risk Score Card */}
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-2">Risk Meter</h3>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-3xl font-bold text-gradient">{riskScore}/10</p>
                            <p className="text-sm text-gray-400">{riskLevel}</p>
                        </div>
                        <div className="h-16 w-16 rounded-full border-4 border-blue-500 flex items-center justify-center">
                            <span className="text-xs">Aggressive</span>
                        </div>
                    </div>
                </div>

                {/* Diversification Score */}
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-2">Diversification</h3>
                    <p className="text-3xl font-bold text-green-400">Good</p>
                    <p className="text-sm text-gray-400">Exposure across 3 sectors</p>
                </div>

                {/* Sharpe Ratio (Mock) */}
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-2">Sharpe Ratio</h3>
                    <p className="text-3xl font-bold">1.8</p>
                    <p className="text-sm text-gray-400">Last 12 months</p>
                </div>
            </div>

            {/* Sector Breakdown Detail */}
            <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4">Sector Breakdown</h3>
                <div className="space-y-4">
                    {(portfolio.allocation || []).map((sector) => (
                        <div key={sector.name} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: sector.color }} />
                                <span>{sector.name}</span>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="w-48 h-2 bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full"
                                        style={{ width: `${sector.value}%`, backgroundColor: sector.color }}
                                    />
                                </div>
                                <span className="w-12 text-right">{sector.value}%</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Top Movers Mock */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-4 text-green-400">Top Performers</h3>
                    <ul className="space-y-2">
                        {(portfolio.holdings || []).filter(h => h.changePercent > 0).slice(0, 3).map(h => (
                            <li key={h.symbol} className="flex justify-between">
                                <span>{h.name}</span>
                                <span className="text-green-400">+{h.changePercent}%</span>
                            </li>
                        ))}
                    </ul>
                </div>
                <div className="glass-card p-6">
                    <h3 className="text-lg font-semibold mb-4 text-red-400">Underperformers</h3>
                    <ul className="space-y-2">
                        {(portfolio.holdings || []).filter(h => h.changePercent < 0).length > 0 ? (
                            (portfolio.holdings || []).filter(h => h.changePercent < 0).slice(0, 3).map(h => (
                                <li key={h.symbol} className="flex justify-between">
                                    <span>{h.name}</span>
                                    <span className="text-red-400">{h.changePercent}%</span>
                                </li>
                            ))
                        ) : (
                            <p className="text-gray-400 text-sm">No assets underperforming today.</p>
                        )}
                    </ul>
                </div>
            </div>
        </div>
    )
}
