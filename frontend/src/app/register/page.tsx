
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { RegisterData } from '@/types';
import { useToast } from '@/context/ToastContext';

export default function RegisterPage() {
    const router = useRouter();
    const { register, loading, error, isAuthenticated } = useAuth();
    const { showToast } = useToast();
    const [formData, setFormData] = useState<RegisterData>({
        full_name: '',
        username: '',
        email: '',
        mobile: '',
        age: 0,
        gender: '',
        address: '',
        password: '',
    });
    const [confirmPassword, setConfirmPassword] = useState('');
    const [formError, setFormError] = useState('');
    const [mobileError, setMobileError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated()) {
            router.push('/dashboard/files');
        }
    }, [isAuthenticated, router]);

    // Validates mobile: 10-digit Indian number (starts 6-9) OR international E.164 (+<digits>)
    const validateMobile = (value: string): string => {
        if (!value) return 'Mobile number is required';
        const indian = /^[6-9]\d{9}$/.test(value);
        const intl = /^\+[1-9]\d{7,14}$/.test(value);
        if (!indian && !intl)
            return 'Enter a valid 10-digit mobile number (e.g. 9876543210) or international format (+1234567890)';
        return '';
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setFormError('');

        const mobileErr = validateMobile(formData.mobile);
        if (mobileErr) {
            setMobileError(mobileErr);
            return;
        }

        if (formData.password !== confirmPassword) {
            setFormError('Passwords do not match');
            return;
        }

        if (formData.age < 1 || formData.age > 150) {
            setFormError('Please enter a valid age');
            return;
        }

        try {
            await register({
                ...formData,
                age: Number(formData.age),
                mobile: String(formData.mobile)
            });
            showToast('Registration successful! Please login.', 'success');
            router.push('/login?registered=true');
        } catch (err: any) {
            showToast(err.message || 'Registration failed', 'error');
        }
    };

    return (
        <div className="h-screen flex bg-white font-sans text-slate-800 overflow-hidden">
            {/* Left Side - Illustration (Fixed) - Reduced width to 40% */}
            <div className="hidden lg:flex lg:w-5/12 items-center justify-center p-8 bg-slate-50 relative overflow-hidden h-full border-r border-slate-100">
                {/* Abstract Background Decoration */}
                <div className="absolute top-0 left-0 w-full h-full">
                    <div className="absolute top-10 left-10 w-32 h-32 bg-blue-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
                    <div className="absolute top-10 right-10 w-32 h-32 bg-teal-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse delay-700"></div>
                    <div className="absolute -bottom-8 left-20 w-32 h-32 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse delay-1000"></div>
                </div>

                <div className="relative z-10 max-w-lg text-center">
                    <div className="mb-6 mx-auto w-48 h-48 relative drop-shadow-2xl">
                        <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
                            <circle cx="100" cy="100" r="90" fill="white" />
                            <path d="M70 140V100L100 70L130 100V140H110V115H90V140H70Z" fill="#4F86ED" fillOpacity="0.1" stroke="#4F86ED" strokeWidth="4" strokeLinejoin="round" />
                            <circle cx="100" cy="50" r="15" fill="#F59E0B" />
                            <rect x="85" y="150" width="30" height="4" rx="2" fill="#E2E8F0" />
                            <path d="M40 100L160 100" stroke="#E2E8F0" strokeWidth="2" strokeDasharray="4 4" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-3 tracking-tight">Join Dischargo</h2>
                    <p className="text-slate-500">
                        Create an account to access the Intelligent Multi-Agent Discharge Analysis System.
                    </p>
                </div>
            </div>

            {/* Right Side - Register Form (Scrollable) - Increased width to 60% */}
            <div className="w-full lg:w-7/12 h-full overflow-y-auto flex items-center justify-center p-6 lg:p-10 relative bg-white custom-scrollbar">
                <div className="w-full max-w-xl space-y-6">
                    {/* Logo/Brand (Mobile only) */}
                    <div className="lg:hidden text-center">
                        <span className="text-2xl font-bold text-[#4F86ED]">Dischargo</span>
                    </div>

                    <div className="space-y-2">
                        <h1 className="text-3xl font-bold text-slate-900">Create Account</h1>
                        <p className="text-slate-500">Enter your details to register</p>
                    </div>

                    <form onSubmit={handleSubmit} className="mt-8 space-y-5">
                        {(error || formError) && (
                            <div className="p-4 bg-red-50 text-red-600 text-sm rounded-xl flex items-center gap-3 border border-red-100 animate-fade-in-down">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                                {error || formError}
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Full Name</label>
                                <input
                                    type="text"
                                    className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-sm"
                                    placeholder="John Doe"
                                    value={formData.full_name}
                                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Username</label>
                                <input
                                    type="text"
                                    className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-sm"
                                    placeholder="johndoe"
                                    value={formData.username}
                                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Email</label>
                            <input
                                type="email"
                                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-sm"
                                placeholder="john@example.com"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                required
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                            <div className="md:col-span-1">
                                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Age</label>
                                <input
                                    type="number"
                                    className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-sm"
                                    placeholder="25"
                                    value={formData.age || ''}
                                    onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || 0 })}
                                    required
                                    min="1"
                                    max="120"
                                />
                            </div>
                            <div className="md:col-span-2">
                                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Gender</label>
                                <div className="relative">
                                    <select
                                        className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-sm appearance-none"
                                        value={formData.gender}
                                        onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                                        required
                                    >
                                        <option value="">Select Gender</option>
                                        <option value="male">Male</option>
                                        <option value="female">Female</option>
                                        <option value="other">Other</option>
                                    </select>
                                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Mobile</label>
                            <input
                                type="tel"
                                className={`w-full px-4 py-2.5 bg-white border rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 transition-all shadow-sm ${mobileError
                                        ? 'border-red-400 focus:ring-red-400/20 focus:border-red-400'
                                        : 'border-slate-200 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED]'
                                    }`}
                                placeholder="9876543210 or +1234567890"
                                value={formData.mobile}
                                maxLength={15}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    setFormData({ ...formData, mobile: val });
                                    setMobileError(validateMobile(val));
                                }}
                                required
                            />
                            {mobileError && (
                                <p className="mt-1.5 text-xs text-red-500 flex items-center gap-1">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                    {mobileError}
                                </p>
                            )}
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-slate-700 mb-1.5">Address</label>
                            <input
                                type="text"
                                className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-sm"
                                placeholder="Street address, City..."
                                value={formData.address}
                                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Password</label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        className="w-full pl-4 pr-12 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-sm"
                                        placeholder="••••••••"
                                        value={formData.password}
                                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 focus:outline-none transition-colors"
                                    >
                                        {showPassword ? (
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                            </svg>
                                        ) : (
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Confirm</label>
                                <div className="relative">
                                    <input
                                        type={showConfirmPassword ? "text" : "password"}
                                        className="w-full pl-4 pr-12 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-sm"
                                        placeholder="••••••••"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 focus:outline-none transition-colors"
                                    >
                                        {showConfirmPassword ? (
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                            </svg>
                                        ) : (
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="pt-2">
                            <button
                                type="submit"
                                className="w-full bg-[#4F86ED] hover:bg-[#3A6BC7] text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Creating Account...
                                    </>
                                ) : (
                                    'Create Account'
                                )}
                            </button>
                        </div>
                    </form>

                    <div className="mt-8 text-center text-sm text-slate-500">
                        Already have an account?{' '}
                        <Link href="/login" className="text-[#4F86ED] hover:text-[#3A6BC7] font-bold transition-colors">
                            Sign In
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
