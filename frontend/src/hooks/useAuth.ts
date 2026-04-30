'use client';

import { useState } from 'react';
import api from '@/lib/api';
import { LoginData, RegisterData } from '@/types';

export function useAuth() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const login = async (data: LoginData) => {
        setLoading(true);
        setError(null);
        try {
            // OAuth2 password flow expects form data
            const formData = new URLSearchParams();
            formData.append('username', data.username);
            formData.append('password', data.password);

            const response = await api.post('/auth/login', formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });

            localStorage.setItem('access_token', response.data.access_token);
            return response.data;
        } catch (err: any) {
            let message = 'Login failed';
            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                message = Array.isArray(detail)
                    ? detail.map((d: any) => d.msg).join(', ')
                    : typeof detail === 'object'
                        ? JSON.stringify(detail)
                        : String(detail);
            }
            setError(message);
            throw new Error(message);
        } finally {
            setLoading(false);
        }
    };

    const register = async (data: RegisterData) => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.post('/auth/register', data);
            return response.data;
        } catch (err: any) {
            let message = 'Registration failed';
            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                message = Array.isArray(detail)
                    ? detail.map((d: any) => d.msg).join(', ')
                    : typeof detail === 'object'
                        ? JSON.stringify(detail)
                        : String(detail);
            }
            setError(message);
            throw new Error(message);
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    };

    const isAuthenticated = () => {
        if (typeof window === 'undefined') return false;
        return !!localStorage.getItem('access_token');
    };

    return {
        login,
        register,
        logout,
        isAuthenticated,
        loading,
        error,
    };
}
