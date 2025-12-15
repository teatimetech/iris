'use client'

import { usePortfolio } from '@/hooks/usePortfolio'
import PortfolioSummary from '../Portfolio/PortfolioSummary'
import HoldingsTable from '../Portfolio/HoldingsTable'
import AssetAllocation from '../Portfolio/AssetAllocation'
import PerformanceChart from '../Portfolio/PerformanceChart'
import LoadingSkeleton from '../Portfolio/LoadingSkeleton'
import ErrorDisplay from '../Common/ErrorDisplay'
import AnalysisView from '../Views/AnalysisView'
import InsightsView from '../Views/InsightsView'

interface ContentAreaProps {
    view: 'portfolio' | 'analysis' | 'insights'
}

export default function ContentArea({ view }: ContentAreaProps) {
    const { data: portfolio, error, isLoading, mutate } = usePortfolio('test-user')

    if (view === 'analysis') return <AnalysisView />
    if (view === 'insights') return <InsightsView />

    if (view === 'portfolio') {
        if (isLoading) {
            return (
                <div className="h-full overflow-y-auto p-6">
                    <LoadingSkeleton />
                </div>
            )
        }

        if (error) {
            return (
                <div className="h-full overflow-y-auto p-6 flex items-center justify-center">
                    <ErrorDisplay
                        message={error.message || 'Failed to load portfolio data'}
                        onRetry={mutate}
                    />
                </div>
            )
        }

        if (!portfolio) {
            return (
                <div className="h-full overflow-y-auto p-6 flex items-center justify-center">
                    <ErrorDisplay message="No portfolio data available" />
                </div>
            )
        }

        return (
            <div className="h-full overflow-y-auto p-6 space-y-6">
                <PortfolioSummary portfolio={portfolio} />

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <AssetAllocation data={portfolio.allocation} />
                    <PerformanceChart data={portfolio.performance} />
                </div>

                <HoldingsTable portfolio={portfolio} />
            </div>
        )
    }

    return null
}
