"use client";

import { useAuth } from '@/app/context/AuthContext';
import Link from 'next/link';
import { useState } from 'react';

export default function Header() {
    const { user, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <header className="glass-card border-b border-white/10 px-6 py-4 sticky top-0 z-50">
            <div className="flex items-center justify-between">
                <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                        <span className="text-xl font-bold text-white">I</span>
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-gradient bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">IRIS</h1>
                        <p className="hidden sm:block text-xs text-gray-400">Intelligent Retirement Investment System</p>
                    </div>
                </Link>

                <div className="flex items-center gap-4">
                    {user ? (
                        <div className="flex items-center gap-4">
                            <div className="text-right hidden sm:block">
                                <p className="text-sm font-medium text-white">{user.first_name} {user.last_name}</p>
                                <p className="text-xs text-gray-400">{user.email}</p>
                            </div>
                            <div className="relative group">
                                <button className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-500 to-orange-500 flex items-center justify-center shadow-md ring-2 ring-white/10 hover:ring-white/30 transition-all">
                                    <span className="text-sm font-bold text-white">
                                        {user.first_name?.[0]}{user.last_name?.[0]}
                                    </span>
                                </button>
                                {/* Dropdown */}
                                <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-white/10 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all transform origin-top-right">
                                    <div className="py-1">
                                        <div className="px-4 py-2 border-b border-white/5 sm:hidden">
                                            <p className="text-sm text-white">{user.first_name}</p>
                                            <p className="text-xs text-gray-400 truncate">{user.email}</p>
                                        </div>
                                        <button
                                            onClick={logout}
                                            className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-white transition-colors"
                                        >
                                            Sign Out
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center gap-3">
                            <Link href="/auth/login" className="text-sm font-medium text-gray-300 hover:text-white transition-colors px-3 py-2">
                                Log In
                            </Link>
                            <Link href="/auth/signup" className="text-sm font-medium bg-white text-black px-4 py-2 rounded-full hover:bg-gray-200 transition-colors shadow-lg shadow-white/10">
                                Sign Up
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </header>
    )
}
