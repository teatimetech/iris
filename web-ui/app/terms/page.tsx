import React from 'react';
import Header from '@/components/Layout/Header';
import Footer from '@/components/Layout/Footer';

export default function TermsPage() {
    return (
        <div className="min-h-screen flex flex-col bg-slate-900 text-white">
            <Header />
            <main className="flex-1 max-w-4xl mx-auto py-20 px-6">
                <h1 className="text-3xl font-bold mb-8">Terms of Service</h1>
                <div className="space-y-6 text-gray-300 leading-relaxed">
                    <p>Welcome to IRIS. By using our services, you agree to these Terms of Service.</p>

                    <h2 className="text-xl font-semibold text-white mt-8">Investment Risks</h2>
                    <p>Investing involves risk, including the possible loss of principal. IRIS provides AI-driven insights but does not guarantee specific investment outcomes.</p>

                    <h2 className="text-xl font-semibold text-white mt-8">User Responsibilities</h2>
                    <p>You are responsible for maintaining the confidentiality of your account and for all activities that occur under your account.</p>

                    <h2 className="text-xl font-semibold text-white mt-8">Service Availability</h2>
                    <p>We strive to ensure our services are available 24/7, but we cannot guarantee uninterrupted access.</p>
                </div>
            </main>
            <Footer />
        </div>
    );
}
