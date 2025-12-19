"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { useRouter } from 'next/navigation';

export default function OnboardingPage() {
    const { user, login } = useAuth();
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    const [formData, setFormData] = useState({
        dob: '',
        phonenumber: '',
        street: '',
        city: '',
        state: '',
        zip: '',
        country: 'USA',
        taxId: ''
    });

    const API_URL = "http://localhost:8080/v1/auth";

    // Load initial state
    React.useEffect(() => {
        if (user) {
            if (user.kyc_step && user.kyc_step > 1) {
                setStep(user.kyc_step);
            }
            if (user.kyc_data) {
                try {
                    const savedData = JSON.parse(user.kyc_data);
                    setFormData(prev => ({ ...prev, ...savedData }));
                } catch (e) {
                    console.error("Failed to parse saved KYC data", e);
                }
            }
        }
    }, [user]);

    const updateField = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const saveProgress = async (nextStep: number) => {
        setIsSaving(true);
        try {
            await axios.post(`${API_URL}/onboarding/step`, {
                user_id: user?.id,
                step: nextStep,
                data: formData
            });
            // Update local user context if possible, but for now just move ui
            setStep(nextStep);
        } catch (err) {
            console.error("Failed to save progress", err);
            // Allow moving forward even if save fails? Maybe warn user.
            setStep(nextStep);
        } finally {
            setIsSaving(false);
        }
    };

    const handleSubmit = async () => {
        setIsSubmitting(true);
        try {
            const payload = {
                user_id: user?.id,
                tax_id: formData.taxId,
                date_of_birth: formData.dob,
                street_address: [formData.street],
                city: formData.city,
                state: formData.state,
                postal_code: formData.zip,
                country: formData.country,
                phone: formData.phonenumber,
                funding_source: ["employment_income"]
            };

            await axios.post(`${API_URL}/onboarding`, payload);

            // Upgrade local user status
            const updatedUser = { ...user!, kyc_status: 'VERIFIED' as const };
            login("mock-token", updatedUser);

            router.push('/');
        } catch (err) {
            console.error("KYC Failed", err);
            alert("Verification failed. Please check your details (Sandbox Note: Ensure TaxID is not 666-...)");
            setIsSubmitting(false);
        }
    };

    // Steps Content
    const renderStep = () => {
        switch (step) {
            case 1:
                return (
                    <div key="step1" className="space-y-4">
                        <h2 className="text-xl font-semibold text-white">Identity Verification</h2>
                        <p className="text-sm text-gray-400">We are required to verify your identity.</p>

                        <div>
                            <label className="text-xs text-gray-500 uppercase">Date of Birth</label>
                            <input type="date" value={formData.dob} onChange={e => updateField('dob', e.target.value)}
                                className="w-full mt-1 px-4 py-2 rounded bg-black/30 border border-white/10 text-white focus:border-blue-500 outline-none" />
                        </div>
                        <div>
                            <label className="text-xs text-gray-500 uppercase">Tax ID / SSN</label>
                            <input type="text" placeholder="XXX-XX-XXXX" value={formData.taxId} onChange={e => updateField('taxId', e.target.value)}
                                className="w-full mt-1 px-4 py-2 rounded bg-black/30 border border-white/10 text-white focus:border-blue-500 outline-none" />
                        </div>
                        <div className="pt-4 flex justify-end">
                            <button onClick={() => saveProgress(2)} disabled={isSaving} className="px-6 py-2 bg-blue-600 rounded-full hover:bg-blue-500 transition-colors flex items-center gap-2">
                                {isSaving ? 'Saving...' : 'Next'}
                            </button>
                        </div>
                    </div>
                );
            case 2:
                return (
                    <div key="step2" className="space-y-4">
                        <h2 className="text-xl font-semibold text-white">Contact Details</h2>
                        <div className="grid grid-cols-1 gap-4">
                            <input type="text" placeholder="Street Address" value={formData.street} onChange={e => updateField('street', e.target.value)}
                                className="w-full px-4 py-2 rounded bg-black/30 border border-white/10 text-white outline-none" />

                            <div className="grid grid-cols-2 gap-2">
                                <input type="text" placeholder="City" value={formData.city} onChange={e => updateField('city', e.target.value)}
                                    className="w-full px-4 py-2 rounded bg-black/30 border border-white/10 text-white outline-none" />
                                <input type="text" placeholder="State" value={formData.state} onChange={e => updateField('state', e.target.value)}
                                    className="w-full px-4 py-2 rounded bg-black/30 border border-white/10 text-white outline-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <input type="text" placeholder="Zip Code" value={formData.zip} onChange={e => updateField('zip', e.target.value)}
                                    className="w-full px-4 py-2 rounded bg-black/30 border border-white/10 text-white outline-none" />
                                <input type="text" placeholder="Phone" value={formData.phonenumber} onChange={e => updateField('phonenumber', e.target.value)}
                                    className="w-full px-4 py-2 rounded bg-black/30 border border-white/10 text-white outline-none" />
                            </div>
                        </div>
                        <div className="pt-4 flex justify-between">
                            <button onClick={() => saveProgress(1)} disabled={isSaving} className="text-gray-400 hover:text-white">Back</button>
                            <button onClick={() => saveProgress(3)} disabled={isSaving} className="px-6 py-2 bg-blue-600 rounded-full hover:bg-blue-500 transition-colors">
                                {isSaving ? 'Saving...' : 'Next'}
                            </button>
                        </div>
                    </div>
                );
            case 3:
                return (
                    <div key="step3" className="space-y-4">
                        <h2 className="text-xl font-semibold text-white">Review & Submit</h2>
                        <div className="bg-white/5 p-4 rounded-lg text-sm text-gray-300 space-y-2">
                            <p><strong>DOB:</strong> {formData.dob}</p>
                            <p><strong>SSN:</strong> {formData.taxId}</p>
                            <p><strong>Address:</strong> {formData.street}, {formData.city}, {formData.state}</p>
                            <p className="text-xs mt-2 opacity-70">By clicking submit, you agree to the Terms of Service and Brokerage Agreement.</p>
                        </div>

                        <div className="pt-4 flex justify-between items-center">
                            <button onClick={() => saveProgress(2)} disabled={isSaving} className="text-gray-400 hover:text-white">Back</button>
                            <button onClick={handleSubmit} disabled={isSubmitting} className="px-8 py-2 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full hover:from-green-400 hover:to-emerald-500 transition-all font-semibold shadow-lg shadow-green-900/40">
                                {isSubmitting ? 'Creating Account...' : 'Open Account'}
                            </button>
                        </div>
                    </div>
                );
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-900 p-4">
            <div className="absolute inset-0 bg-gradient-to-b from-slate-900 to-black pointer-events-none"></div>

            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-lg relative z-10"
            >
                <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl overflow-hidden">
                    {/* Progress Bar */}
                    <div className="flex items-center gap-2 mb-8">
                        <div className={`h-1 flex-1 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]`}></div>
                        <div className={`h-1 flex-1 rounded-full transition-all duration-300 ${step >= 2 ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]' : 'bg-white/10'}`}></div>
                        <div className={`h-1 flex-1 rounded-full transition-all duration-300 ${step >= 3 ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]' : 'bg-white/10'}`}></div>
                    </div>

                    <AnimatePresence mode="wait">
                        <motion.div
                            key={step}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ duration: 0.2 }}
                        >
                            {renderStep()}
                        </motion.div>
                    </AnimatePresence>
                </div>
            </motion.div>
        </div>
    );
}
