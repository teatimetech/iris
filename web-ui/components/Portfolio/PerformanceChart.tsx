'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { PerformanceData } from '@/lib/types'

interface PerformanceChartProps {
    data: PerformanceData[]
}

export default function PerformanceChart({ data }: PerformanceChartProps) {
    return (
        <div className="glass-card p-6">
            <h3 className="text-lg font-semibold mb-4">Performance (30 Days)</h3>
            <ResponsiveContainer width="100%" height={250}>
                <LineChart data={data || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                    <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} tickFormatter={(value) => value.slice(5)} />
                    <YAxis stroke="#9ca3af" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} />
                    <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}
