'use client'

import { useState } from 'react'
import { useAuth } from '@/app/context/AuthContext'
import { usePortfolio } from '@/hooks/usePortfolio'
import { useChat } from '@/hooks/useChat'
import LoadingSkeleton from '../Portfolio/LoadingSkeleton'
import ErrorDisplay from '../Common/ErrorDisplay'
import { motion } from 'framer-motion'

export default function InsightsView() {
    const { user } = useAuth()
    const { data: portfolio, error, isLoading } = usePortfolio(user?.id.toString() || '')
    const { messages, isLoading: isChatLoading, sendMessage } = useChat([], user?.id.toString() || '')
    const [hasGenerated, setHasGenerated] = useState(false)

    if (isLoading) return <LoadingSkeleton />
    if (error) return <ErrorDisplay message={error.message} />
    if (!portfolio) return <ErrorDisplay message="No data" />

    const handleGenerate = () => {
        const summary = `Total Value: $${portfolio.totalValue}. Top Holdings: ${portfolio.holdings.slice(0, 3).map(h => h.symbol).join(', ')}.`
        sendMessage(`Generate 3 concise investment insights for this portfolio: ${summary}`)
        setHasGenerated(true)
    }

    const aiMessages = messages.filter(m => m.role === 'assistant')
    const latestInsight = aiMessages.length > 0 ? aiMessages[aiMessages.length - 1] : null

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">AI Insights</h2>
                {!hasGenerated && (
                    <button
                        onClick={handleGenerate}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
                        disabled={isChatLoading}
                    >
                        {isChatLoading ? 'Generating...' : 'Generate Analysis'}
                    </button>
                )}
            </div>

            {!hasGenerated && !isChatLoading && (
                <div className="glass-card p-12 text-center">
                    <p className="text-gray-400">Click generate to get AI-powered insights for your portfolio.</p>
                </div>
            )}

            {isChatLoading && <LoadingSkeleton />}

            {hasGenerated && latestInsight && !isChatLoading && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card p-6 border-l-4 border-blue-500"
                >
                    <h3 className="text-lg font-semibold mb-4 text-gradient">Strategic Analysis</h3>
                    <div className="prose prose-invert max-w-none">
                        <p className="whitespace-pre-wrap">{latestInsight.content}</p>
                    </div>
                </motion.div>
            )}
        </div>
    )
}
