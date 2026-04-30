'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { useToast } from '@/context/ToastContext';

export default function ViewOriginalPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const { showToast } = useToast();
    const [blobUrl, setBlobUrl] = useState<string | null>(null);
    const [fileType, setFileType] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const blobUrlRef = useRef<string | null>(null);

    useEffect(() => {
        const fetchFile = async () => {
            try {
                const response = await api.get(`/uploads/${params.id}/content`, {
                    responseType: 'blob'
                });

                const type = response.headers['content-type'];
                const blob = new Blob([response.data], { type });
                const url = URL.createObjectURL(blob);

                blobUrlRef.current = url;
                setBlobUrl(url);
                setFileType(type);
            } catch (err: any) {
                console.error(err);
                const message = 'Failed to load file';
                setError(message);
                showToast(message, 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchFile();

        // Cleanup blob URL on unmount
        return () => {
            if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
        };
    }, [params.id, showToast]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen bg-slate-50">
                <div className="spinner w-10 h-10 border-4 border-slate-200 border-t-[#4F86ED] rounded-full animate-spin"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-slate-50 p-4">
                <div className="text-4xl mb-4">⚠️</div>
                <h1 className="text-xl font-bold text-slate-800 mb-2">Error Loading File</h1>
                <p className="text-slate-500 mb-6">{error}</p>
                <button
                    onClick={() => router.back()}
                    className="px-6 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
                >
                    Go Back
                </button>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-slate-900">
            {/* Header */}
            <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between shadow-sm z-10">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => router.back()}
                        className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-500"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                    </button>
                    <h1 className="text-base font-bold text-slate-800 flex items-center gap-2">
                        📄 Original File Viewer
                    </h1>
                </div>
                <a
                    href={blobUrl!}
                    download={`file-${params.id}`}
                    className="px-4 py-2 bg-[#4F86ED] hover:bg-[#3A6BC7] text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download
                </a>
            </header>

            {/* Viewer Content */}
            <div className="flex-1 overflow-hidden flex items-center justify-center p-4">
                {fileType.includes('image') ? (
                    <img
                        src={blobUrl!}
                        alt="Original File"
                        className="max-w-full max-h-full object-contain rounded shadow-lg"
                    />
                ) : (
                    <iframe
                        src={blobUrl!}
                        className="w-full h-full bg-white rounded shadow-lg"
                        title="File Viewer"
                    />
                )}
            </div>
        </div>
    );
}
