'use client'

import type { Portfolio } from '@/lib/types'

interface PortfolioSummaryProps {
    portfolio: Portfolio
}

export default function PortfolioSummary({ portfolio }: PortfolioSummaryProps) {
    // Identify Core (Alpaca) vs External
    // Identify Core (Alpaca/IRIS) vs External
    const coreGroup = portfolio.brokerGroups?.find(g => g.brokerName === 'alpaca' || g.displayName.includes('IRIS Core'))
    // Fallback if no specific core group found, maybe sum everything? 
    // But requirement says Core is focus.

    // If we have legacy data structure without brokerGroups, handle gracefully?
    // portfolio.brokerGroups assumes it's there.
    const externalGroups = portfolio.brokerGroups?.filter(g => g !== coreGroup) || []

    const coreValue = coreGroup?.totalValue || 0
    const corePL = coreGroup?.gainLoss || 0
    const corePLPct = coreGroup?.gainLossPercent || 0

    return (
        <div className="space-y-6">
            {/* Core Portfolio Section */}
            <div className="glass-card p-6">
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h2 className="text-2xl font-bold">Your IRIS Core Portfolio</h2>
                        {coreGroup && (
                            <div className="text-xs text-gray-500 font-mono mt-1 space-x-3">
                                <span>Account #: {coreGroup.irisAccountNumber || 'N/A'}</span>
                                <span className="text-gray-600">|</span>
                                <span>ID: {coreGroup.irisAccountId || 'N/A'}</span>
                            </div>
                        )}
                    </div>
                    <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs font-mono">MANAGED</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <p className="text-sm text-gray-400 mb-1">Portfolio Value</p>
                        <p className="text-3xl font-bold text-white">${coreValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    </div>

                    <div>
                        <p className="text-sm text-gray-400 mb-1">Buying Power (Cash)</p>
                        <p className="text-2xl font-bold text-blue-400">${(coreGroup?.cashBalance || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                    </div>

                    <div>
                        <p className="text-sm text-gray-400 mb-1">Today's P/L</p>
                        <p className={`text-2xl font-bold ${portfolio.todayPLValue >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {portfolio.todayPL}
                        </p>
                    </div>

                    <div>
                        <p className="text-sm text-gray-400 mb-1">Gain/Loss</p>
                        <p className={`text-2xl font-bold ${corePL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            ${Math.abs(corePL).toLocaleString('en-US', { minimumFractionDigits: 2 })} ({corePLPct >= 0 ? '+' : ''}{corePLPct.toFixed(2)}%)
                        </p>
                    </div>
                </div>
            </div>

            {/* External Accounts Section */}
            {externalGroups.length > 0 && (
                <div className="glass-card p-6">
                    <h2 className="text-xl font-bold mb-4 text-gray-300">External Accounts</h2>
                    <div className="space-y-4">
                        {externalGroups.map((group) => (
                            <div key={group.brokerName + group.portfolioName} className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                                <div>
                                    <p className="font-semibold">{group.displayName}</p>
                                    <p className="text-sm text-gray-500">{group.portfolioName} • {group.accountNumber}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-xl font-mono">${group.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                                    <p className={`text-sm ${group.gainLoss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        {group.gainLoss >= 0 ? '+' : ''}{group.gainLossPercent.toFixed(2)}%
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Net Worth Section */}
            <div className="glass-card p-6 bg-gradient-to-r from-gray-900 to-gray-800 border-t-2 border-green-500/30">
                <div className="flex justify-between items-end">
                    <div>
                        <p className="text-sm text-gray-400 uppercase tracking-wider">Total Net Worth</p>
                        <p className="text-xs text-gray-500">Includes IRIS Core + All Connected Accounts</p>
                    </div>
                    <div className="text-right">
                        <p className="text-4xl font-bold text-green-400">${portfolio.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                        <p className="text-sm text-gray-400">Total Gain: {portfolio.overallPL}</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
