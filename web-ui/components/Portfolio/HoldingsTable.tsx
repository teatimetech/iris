'use client'

import type { Holding } from '@/lib/types'

interface HoldingsTableProps {
    holdings: Holding[]
}

export default function HoldingsTable({ holdings }: HoldingsTableProps) {
    return (
        <div className="glass-card p-6">
            <h3 className="text-lg font-semibold mb-4">Holdings</h3>
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-white/10">
                            <th className="text-left py-3 px-2 font-medium text-gray-400">Symbol</th>
                            <th className="text-left py-3 px-2 font-medium text-gray-400">Name</th>
                            <th className="text-right py-3 px-2 font-medium text-gray-400">Shares</th>
                            <th className="text-right py-3 px-2 font-medium text-gray-400">Price</th>
                            <th className="text-right py-3 px-2 font-medium text-gray-400">Value</th>
                            <th className="text-right py-3 px-2 font-medium text-gray-400">Change</th>
                        </tr>
                    </thead>
                    <tbody>
                        {holdings.map((holding) => (
                            <tr key={holding.symbol} className="border-b border-white/5 hover:bg-white/5 transition">
                                <td className="py-3 px-2 font-semibold text-blue-400">{holding.symbol}</td>
                                <td className="py-3 px-2 text-gray-300">{holding.name}</td>
                                <td className="py-3 px-2 text-right">{holding.shares}</td>
                                <td className="py-3 px-2 text-right font-mono">${holding.price.toFixed(2)}</td>
                                <td className="py-3 px-2 text-right font-mono">${holding.value.toLocaleString()}</td>
                                <td className={`py-3 px-2 text-right font-mono ${holding.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {holding.change >= 0 ? '+' : ''}{holding.changePercent.toFixed(2)}%
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
