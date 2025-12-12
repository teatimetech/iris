import useSWR from 'swr'
import { getPortfolio } from '@/lib/api'
import type { Portfolio } from '@/lib/types'

interface UsePortfolioReturn {
    data: Portfolio | undefined
    error: Error | undefined
    isLoading: boolean
    mutate: () => void
}

/**
 * Custom SWR hook for fetching portfolio data
 * Automatically revalidates on focus and interval
 */
export function usePortfolio(userId: string): UsePortfolioReturn {
    const { data, error, isLoading, mutate } = useSWR<Portfolio>(
        userId ? `/v1/portfolio/${userId}` : null,
        () => getPortfolio(userId),
        {
            revalidateOnFocus: true,
            revalidateOnReconnect: true,
            refreshInterval: 30000,
            dedupingInterval: 5000,
        }
    )

    return {
        data,
        error,
        isLoading,
        mutate,
    }
}
