import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from './context/AuthContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'IRIS - Intelligent Retirement Investment System',
    description: 'AI-powered financial advisor',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body className={`${inter.className} bg-slate-900 text-white min-h-screen`}>
                <AuthProvider>
                    {children}
                </AuthProvider>
            </body>
        </html>
    )
}
