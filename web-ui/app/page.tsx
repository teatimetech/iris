'use client'

import { useState } from 'react'
import Header from '@/components/Layout/Header'
import ChatPanel from '@/components/Chat/ChatPanel'
import ContentArea from '@/components/Layout/ContentArea'

export default function Home() {
    const [currentView, setCurrentView] = useState<'portfolio' | 'analysis' | 'insights'>('portfolio')

    return (
        <div className="h-screen flex flex-col overflow-hidden">
            <Header />

            <main className="flex-1 flex flex-col md:flex-row overflow-hidden">
                {/* Chat Panel - Top (Mobile) / Left (Desktop) */}
                <div className="w-full h-[40vh] md:h-full md:w-2/5 lg:w-2/5 border-b md:border-b-0 md:border-r border-white/10">
                    <ChatPanel onViewChange={setCurrentView} />
                </div>

                {/* Content Area - Bottom (Mobile) / Right (Desktop) */}
                <div className="w-full flex-1 md:w-3/5 lg:w-3/5 overflow-hidden">
                    <ContentArea view={currentView} />
                </div>
            </main>
        </div>
    )
}
