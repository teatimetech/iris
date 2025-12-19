'use client'

import { useState } from 'react'
import { useAuth } from './context/AuthContext';
import { useRouter } from 'next/navigation';
import Header from '@/components/Layout/Header'
import Footer from '@/components/Layout/Footer'
import ChatPanel from '@/components/Chat/ChatPanel'
import ContentArea from '@/components/Layout/ContentArea'
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function Home() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [currentView, setCurrentView] = useState<'portfolio' | 'analysis' | 'insights'>('portfolio');

    // Loading State
    if (loading) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 rounded-full border-4 border-blue-500/30 border-t-blue-500 animate-spin"></div>
                    <p className="text-gray-400 animate-pulse">Initializing IRIS...</p>
                </div>
            </div>
        );
    }

    // Authenticated: Dashboard View
    if (user) {
        return (
            <div className="h-screen flex flex-col overflow-hidden bg-slate-900 text-white">
                <Header />
                <main className="flex-1 flex flex-col md:flex-row overflow-hidden relative">
                    {/* Background Grid */}
                    <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-20 pointer-events-none"></div>

                    {/* Chat Panel */}
                    <div className="w-full h-[40vh] md:h-full md:w-2/5 lg:w-2/5 border-b md:border-b-0 md:border-r border-white/10 relative z-10 bg-slate-900/50 backdrop-blur-sm">
                        <ChatPanel onViewChange={setCurrentView} />
                    </div>

                    {/* Content Area */}
                    <div className="w-full flex-1 md:w-3/5 lg:w-3/5 overflow-hidden relative z-10">
                        <ContentArea view={currentView} />
                    </div>
                </main>
            </div>
        );
    }

    // Unauthenticated: Landing Page View
    return (
        <div className="min-h-screen flex flex-col bg-slate-900 text-white selection:bg-blue-500/30">
            <Header />

            <main className="flex-1 flex flex-col">
                {/* Hero Section */}
                <section className="relative py-20 px-4 md:py-32 overflow-hidden flex items-center justify-center min-h-[80vh]">
                    <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-30"></div>
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-blue-500/20 rounded-full blur-[120px] opacity-50 pointer-events-none"></div>
                    <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-purple-500/20 rounded-full blur-[100px] opacity-30 pointer-events-none"></div>

                    <div className="relative z-10 max-w-5xl mx-auto text-center space-y-8">
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8 }}
                        >
                            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-4">
                                <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                                    Intelligent Wealth
                                </span>
                                <br />
                                <span className="text-4xl md:text-6xl bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                                    Management
                                </span>
                            </h1>
                        </motion.div>

                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, delay: 0.2 }}
                            className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed"
                        >
                            Experience the future of investing with IRIS. An AI-powered advisor that manages your portfolio, balances risk, and helps you achieve your financial goals.
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, delay: 0.4 }}
                            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
                        >
                            <Link href="/auth/signup" className="px-8 py-4 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold text-lg shadow-lg shadow-blue-500/25 transition-all hover:scale-105">
                                Get Started Free
                            </Link>
                            <Link href="/auth/login" className="px-8 py-4 rounded-full bg-white/10 hover:bg-white/20 border border-white/10 backdrop-blur-md text-white font-semibold text-lg transition-all hover:scale-105">
                                Live Demo
                            </Link>
                        </motion.div>
                    </div>
                </section>

                {/* Features Grid */}
                <section className="py-20 px-4 relative z-10 bg-black/20 backdrop-blur-sm">
                    <div className="max-w-7xl mx-auto">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <FeatureCard
                                icon="🤖"
                                title="AI-Driven Insights"
                                description="Get real-time, personalized investment advice based on market trends and your unique risk profile."
                            />
                            <FeatureCard
                                icon="🛡️"
                                title="Risk Balanced"
                                description="Advanced algorithms ensure your portfolio maintains the perfect balance between growth and security."
                            />
                            <FeatureCard
                                icon="⚡"
                                title="Instant Execution"
                                description="Seamlessly execute trades and rebalance your portfolio with a single command to your AI agent."
                            />
                        </div>
                    </div>
                </section>
            </main>

            <Footer />
        </div>
    );
}

function FeatureCard({ icon, title, description }: { icon: string, title: string, description: string }) {
    return (
        <motion.div
            whileHover={{ y: -5 }}
            className="p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md hover:bg-white/10 transition-colors"
        >
            <div className="text-4xl mb-4">{icon}</div>
            <h3 className="text-xl font-semibold mb-2 text-white">{title}</h3>
            <p className="text-gray-400 leading-relaxed">{description}</p>
        </motion.div>
    );
}
