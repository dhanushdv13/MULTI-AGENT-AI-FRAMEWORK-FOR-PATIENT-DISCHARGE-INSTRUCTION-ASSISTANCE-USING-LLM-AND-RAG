'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Upload } from '@/types';
import { useToast } from '@/context/ToastContext';

export default function FilesPage() {
    const router = useRouter();
    const { showToast } = useToast();
    const [files, setFiles] = useState<Upload[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = async () => {
        try {
            const response = await api.get('/uploads/');
            setFiles(response.data);
        } catch (err: any) {
            let message = 'Failed to fetch files';
            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                message = Array.isArray(detail)
                    ? detail.map((d: any) => d.msg).join(', ')
                    : typeof detail === 'object'
                        ? JSON.stringify(detail)
                        : String(detail);
            }
            setError(message);
            showToast(message, 'error');
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner" style={{ width: '40px', height: '40px' }} />
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto animate-fade-in-down p-6">
            <div className="mb-8 flex justify-between items-center border-b border-slate-200 pb-6">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 mb-2">
                        Your Documents
                    </h1>
                    <p className="text-slate-500">
                        Manage and analyze your discharge summaries
                    </p>
                </div>
                <button
                    onClick={() => router.push('/dashboard/upload')}
                    className="bg-[#4F86ED] hover:bg-[#3A6BC7] text-white font-semibold py-2.5 px-6 rounded-lg shadow-md shadow-blue-500/20 hover:shadow-lg transition-all hover:-translate-y-0.5 flex items-center gap-2"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                    </svg>
                    Upload New
                </button>
            </div>

            {error && (
                <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 flex items-center gap-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    {error}
                </div>
            )}

            {files.length === 0 ? (
                <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center shadow-sm">
                    <div className="text-6xl mb-4 opacity-50">📋</div>
                    <h2 className="text-xl font-semibold text-slate-800 mb-2">No documents yet</h2>
                    <p className="text-slate-500 mb-8 max-w-sm mx-auto">
                        Upload your first discharge summary to get started with AI analysis.
                    </p>
                    <button
                        onClick={() => router.push('/dashboard/upload')}
                        className="bg-[#4F86ED] hover:bg-[#3A6BC7] text-white font-semibold py-3 px-8 rounded-xl shadow-lg shadow-blue-500/30 hover:shadow-xl transition-all hover:-translate-y-1"
                    >
                        Upload Document
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {files.map((file) => (
                        <div
                            key={file.upload_id}
                            className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col gap-4 group"
                            onClick={() => router.push(`/dashboard/files/${file.upload_id}`)}
                        >
                            <div className="flex justify-between items-start">
                                <div className="text-4xl p-3 bg-blue-50 rounded-2xl group-hover:scale-110 transition-transform duration-300">📄</div>
                                {file.vector_status?.toUpperCase() === "COMPLETED" && (
                                    <div className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full font-bold uppercase tracking-wider">
                                        Ready
                                    </div>
                                )}
                            </div>

                            <div>
                                <h3 className="text-lg font-bold text-slate-800 leading-tight mb-1 line-clamp-1 group-hover:text-[#4F86ED] transition-colors">
                                    {file.filename}
                                </h3>
                                {file.description && (
                                    <p className="text-sm text-slate-500 line-clamp-2 leading-relaxed">
                                        {file.description}
                                    </p>
                                )}
                            </div>

                            <div className="pt-4 mt-auto border-t border-slate-100 flex items-center justify-between text-xs text-slate-400 font-medium">
                                <span className="flex items-center gap-1">
                                    📅 {formatDate(file.created_at)}
                                </span>
                                {file.vector_id && (
                                    <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded-md font-mono text-[10px]">
                                        ID: {file.vector_id.substring(0, 6)}...
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
