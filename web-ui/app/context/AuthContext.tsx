"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

// Define User Type
export interface User {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    kyc_status: 'PENDING' | 'VERIFIED' | 'REJECTED';
    kyc_step: number;
    kyc_data: string; // JSON string
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (token: string, user: User) => void;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    login: () => { },
    logout: () => { },
    refreshUser: async () => { },
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        // Check local storage for session
        const storedUser = localStorage.getItem('iris_user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
        setLoading(false);
    }, []);

    const login = (token: string, newUser: User) => {
        // In MVP we don't strictly use token, but we should store it if API required it.
        // We'll store user object directly for contexts.
        localStorage.setItem('iris_user', JSON.stringify(newUser));
        setUser(newUser);

        // Route based on KYC
        if (newUser.kyc_status === 'PENDING') {
            router.push('/onboarding');
        } else {
            router.push('/');
        }
    };

    const logout = () => {
        localStorage.removeItem('iris_user');
        setUser(null);
        router.push('/auth/login');
    };

    const refreshUser = async () => {
        // Re-fetch user status if needed, but for MVP we rely on local state update
        // or could call an API endpoint /auth/me
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
