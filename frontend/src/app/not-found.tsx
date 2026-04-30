'use client';

import Link from 'next/link';

export default function NotFound() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 relative overflow-hidden">
            {/* Background Decoration */}
            <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-[128px] opacity-60 animate-pulse"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-200 rounded-full mix-blend-multiply filter blur-[128px] opacity-60 animate-pulse delay-700"></div>
            </div>

            <div className="relative z-10 text-center px-6">
                <div className="mb-8 relative inline-block">
                    <div className="text-[150px] font-bold text-[#4F86ED] opacity-10 leading-none select-none">404</div>
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-24 w-24 text-[#4F86ED]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                </div>

                <h1 className="text-4xl font-bold text-slate-900 mb-4 tracking-tight">Page Not Found</h1>
                <p className="text-lg text-slate-500 mb-8 max-w-md mx-auto">
                    The page you are looking for doesn't exist or has been moved.
                </p>

                <Link
                    href="/dashboard/files"
                    className="inline-flex items-center gap-2 px-8 py-3 bg-[#4F86ED] hover:bg-[#3A6BC7] text-white font-bold rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 hover:-translate-y-1"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
                    </svg>
                    Back to Dashboard
                </Link>
            </div>
        </div>
    );
}
