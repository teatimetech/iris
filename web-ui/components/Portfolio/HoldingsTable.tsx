'use client'

import type { Portfolio } from '@/lib/types'

interface HoldingsTableProps {
    portfolio: Portfolio
}

export default function HoldingsTable({ portfolio }: HoldingsTableProps) {
    return (
        <div className="glass-card p-6">
            <h3 className="text-lg font-semibold mb-6">Holdings</h3>

            {/* Display holdings grouped by broker */}
            {portfolio.brokerGroups && portfolio.brokerGroups.length > 0 ? (
                portfolio.brokerGroups.map((group, index) => (
                    <div key={group.portfolioId} className={index > 0 ? "mt-8" : ""}>
                        {/* Broker header */}
                        <div className="mb-4 pb-3 border-b border-white/20">
                            <div className="flex justify-between items-center">
                                <div>
                                    <h4 className="text-xl font-bold text-blue-400">{group.displayName}</h4>
                                    <p className="text-sm text-gray-400">{group.portfolioName} • {group.accountNumber}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm text-gray-400">Portfolio Value</p>
                                    <p className="text-xl font-bold">${group.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                                    <p className={`text-sm font-semibold ${group.gainLoss >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                        {group.gainLoss >= 0 ? '+' : ''}${group.gainLoss.toLocaleString('en-US', { minimumFractionDigits: 2 })} ({group.gainLossPercent.toFixed(2)}%)
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Holdings table for this broker */}
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-white/10">
                                        <th className="text-left py-3 px-2 font-medium text-gray-400">Symbol</th>
                                        <th className="text-right py-3 px-2 font-medium text-gray-400">Shares</th>
                                        <th className="text-right py-3 px-2 font-medium text-gray-400">Price</th>
                                        <th className="text-right py-3 px-2 font-medium text-gray-400">Cost Basis</th>
                                        <th className="text-right py-3 px-2 font-medium text-gray-400">Value</th>
                                        <th className="text-right py-3 px-2 font-medium text-gray-400">Gain/Loss</th>
                                        <th className="text-right py-3 px-2 font-medium text-gray-400">Day Change</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {group.holdings.map((holding) => (
                                        <tr key={holding.symbol} className="border-b border-white/5 hover:bg-white/5 transition">
                                            <td className="py-3 px-2 font-semibold text-blue-400">{holding.symbol}</td>
                                            <td className="py-3 px-2 text-right">{holding.shares.toLocaleString()}</td>
                                            <td className="py-3 px-2 text-right font-mono">${holding.price.toFixed(2)}</td>
                                            <td className="py-3 px-2 text-right font-mono text-gray-400">${holding.costBasisPerShare.toFixed(2)}</td>
                                            <td className="py-3 px-2 text-right font-mono">${holding.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                                            <td className={`py-3 px-2 text-right font-mono font-semibold ${holding.gainLoss >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                                {holding.gainLoss >= 0 ? '+' : ''}${holding.gainLoss.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                                <span className="text-xs ml-1">({holding.gainLossPercent.toFixed(2)}%)</span>
                                            </td>
                                            <td className={`py-3 px-2 text-right font-mono ${holding.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                                {holding.change >= 0 ? '+' : ''}{holding.changePercent.toFixed(2)}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ))
            ) : (
                <p className="text-gray-400">No holdings found</p>
            )}

            {/* Overall portfolio total */}
            {portfolio.brokerGroups && portfolio.brokerGroups.length > 1 && (
                <div className="mt-6 pt-4 border-t-2 border-blue-500/50">
                    <div className="flex justify-between items-center">
                        <h4 className="text-xl font-bold">Total IRIS Portfolio</h4>
                        <div className="text-right">
                            <p className="text-2xl font-bold">${portfolio.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                            <p className={`text-lg font-semibold ${portfolio.totalGainLoss >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                {portfolio.totalGainLoss >= 0 ? '+' : ''}${portfolio.totalGainLoss.toLocaleString('en-US', { minimumFractionDigits: 2 })} ({portfolio.totalGainLossPercent.toFixed(2)}%)
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
