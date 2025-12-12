export default function LoadingSkeleton() {
    return (
        <div className="animate-pulse space-y-6">
            {/* Summary Cards Skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="glass-card p-6 h-24 bg-white/5"></div>
                <div className="glass-card p-6 h-24 bg-white/5"></div>
                <div className="glass-card p-6 h-24 bg-white/5"></div>
            </div>

            {/* Charts Skeleton */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card p-6 h-64 bg-white/5"></div>
                <div className="glass-card p-6 h-64 bg-white/5"></div>
            </div>

            {/* Table Skeleton */}
            <div className="glass-card p-6 h-96 bg-white/5"></div>
        </div>
    )
}
