"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import Link from 'next/link';

export default function SignUpPage() {
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        email: '',
        password: ''
    });

    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { login } = useAuth();
    const router = useRouter();

    // Use relative path to leverage Next.js rewrites
    const API_URL = "/api/auth";

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError('');

        try {
            const res = await axios.post(`${API_URL}/signup`, {
                first_name: formData.firstName,
                last_name: formData.lastName,
                email: formData.email,
                password: formData.password
            });
            // Auto login after signup
            login("mock-token", res.data.user);
        } catch (err: any) {
            // Check if email already exists (409 Conflict)
            if (err.response?.status === 409) {
                setError('Email already registered. Redirecting to login...');
                setTimeout(() => {
                    router.push('/auth/login');
                }, 2000);
            } else {
                setError(err.response?.data?.error || 'Signup failed.');
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-900 via-slate-900 to-black p-4">
            <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]"></div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md relative z-10"
            >
                <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-8 shadow-2xl">
                    <div className="mb-8 text-center">
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-teal-400 bg-clip-text text-transparent mb-2">
                            Join IRIS
                        </h1>
                        <p className="text-gray-400">Start your intelligent investment journey</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div className="p-3 rounded-lg bg-red-500/20 border border-red-500/50 text-red-200 text-sm text-center">
                                {error}
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">First Name</label>
                                <input
                                    type="text"
                                    onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                                    className="w-full px-4 py-3 rounded-lg bg-black/30 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all"
                                    placeholder="Jane"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Last Name</label>
                                <input
                                    type="text"
                                    onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                                    className="w-full px-4 py-3 rounded-lg bg-black/30 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all"
                                    placeholder="Doe"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                            <input
                                type="email"
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                className="w-full px-4 py-3 rounded-lg bg-black/30 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all"
                                placeholder="jane@example.com"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
                            <input
                                type="password"
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                className="w-full px-4 py-3 rounded-lg bg-black/30 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all"
                                placeholder="Create a password"
                                required
                            />
                        </div>

                        <div className="pt-2">
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="w-full py-3 px-4 rounded-lg bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-500 hover:to-teal-500 text-white font-semibold shadow-lg shadow-green-900/20 transform hover:-translate-y-0.5 transition-all"
                            >
                                {isSubmitting ? 'Creating Account...' : 'Sign Up'}
                            </button>
                        </div>
                    </form>

                    <div className="mt-6 text-center text-sm text-gray-400">
                        Already have an account?{' '}
                        <Link href="/auth/login" className="text-green-400 hover:text-green-300 font-medium transition-colors">
                            Sign in
                        </Link>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
