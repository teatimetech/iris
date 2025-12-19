import React from 'react';
import Header from '@/components/Layout/Header';
import Footer from '@/components/Layout/Footer';

export default function PrivacyPage() {
    return (
        <div className="min-h-screen flex flex-col bg-slate-900 text-white">
            <Header />
            <main className="flex-1 max-w-4xl mx-auto py-20 px-6">
                <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>
                <div className="space-y-6 text-gray-300 leading-relaxed">
                    <p>At IRIS, we take your privacy seriously. This Privacy Policy explains how we collect, use, and protect your personal information.</p>

                    <h2 className="text-xl font-semibold text-white mt-8">Data Collection</h2>
                    <p>We collect information you provide directly to us, such as when you create an account, update your profile, or use our financial advisory services.</p>

                    <h2 className="text-xl font-semibold text-white mt-8">Data Usage</h2>
                    <p>We use your information to provide personalized investment insights, manage your portfolio, and improve our AI algorithms.</p>

                    <h2 className="text-xl font-semibold text-white mt-8">Security</h2>
                    <p>We implement industry-standard security measures to protect your financial data and personal information.</p>
                </div>
            </main>
            <Footer />
        </div>
    );
}
