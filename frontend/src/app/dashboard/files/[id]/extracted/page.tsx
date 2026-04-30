'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Upload } from '@/types';
import { useToast } from '@/context/ToastContext';

export default function ExtractedContentPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const { showToast } = useToast();
    const [file, setFile] = useState<Upload | null>(null);
    const [content, setContent] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchContent();
    }, [params.id]);

    const fetchContent = async () => {
        try {
            // Fetch file metadata
            const fileRes = await api.get(`/uploads/${params.id}`);
            setFile(fileRes.data);

            // Fetch extracted HTML (converted from DOCX)
            const htmlRes = await api.get(`/uploads/${params.id}/extracted/html`);
            setContent(htmlRes.data);
        } catch (err: any) {
            console.error(err);
            setError('Failed to load extracted content. Please try again.');
            showToast('Failed to load content', 'error');
        } finally {
            setLoading(false);
        }
    };

    const downloadDocx = async () => {
        if (!file) return;
        try {
            const response = await api.get(`/uploads/${params.id}/extracted`, {
                responseType: 'blob',
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${file.filename.split('.')[0]}_extracted.docx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            showToast('Download started', 'success');
        } catch (err) {
            showToast('Download failed', 'error');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner" style={{ width: '40px', height: '40px' }} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass-card p-8 text-center">
                <div className="text-6xl mb-4">⚠️</div>
                <h2 className="text-xl font-semibold mb-2">Error</h2>
                <p className="text-text-secondary mb-6">{error}</p>
                <div className="flex gap-4 justify-center">
                    <button onClick={() => router.back()} className="btn btn-secondary">
                        Go Back
                    </button>
                    {/* Fallback download if view fails */}
                    {file && (
                        <button onClick={downloadDocx} className="btn btn-primary">
                            Download DOCX
                        </button>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto h-full flex flex-col animate-fade-in-down">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between flex-none">
                <div>
                    <button
                        onClick={() => router.back()}
                        className="text-slate-500 hover:text-[#4F86ED] mb-2 flex items-center gap-2 transition-colors font-medium text-sm"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
                        </svg>
                        Back
                    </button>
                    <h1 className="text-2xl font-bold text-slate-800">Extracted Content</h1>
                    <p className="text-slate-500 text-sm">
                        DOCX Preview for {file?.filename}
                    </p>
                </div>
                <button
                    onClick={downloadDocx}
                    className="flex items-center gap-2 px-4 py-2 bg-[#4F86ED] hover:bg-[#3A6BC7] text-white rounded-lg shadow-md transition-all hover:scale-105 text-sm font-medium"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    Download Original (.docx)
                </button>
            </div>

            {/* Content Viewer */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm flex-1 overflow-hidden flex flex-col">
                <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                        Document Preview
                    </span>
                </div>
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar bg-white">
                    <div
                        className="prose prose-sm max-w-none text-slate-700 leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: content }}
                    />
                </div>
            </div>
        </div>
    );
}
