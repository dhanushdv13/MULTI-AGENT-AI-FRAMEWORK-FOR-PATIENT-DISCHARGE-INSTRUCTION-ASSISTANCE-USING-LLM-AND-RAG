'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { useToast } from '@/context/ToastContext';

export default function UploadPage() {
    const router = useRouter();
    const { showToast } = useToast();
    const [file, setFile] = useState<File | null>(null);
    const [description, setDescription] = useState('');
    const [additionalNotes, setAdditionalNotes] = useState('');
    const [loading, setLoading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState('');
    const [dragActive, setDragActive] = useState(false);

    const [uploadProgress, setUploadProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('Processing...');
    const [logs, setLogs] = useState<string[]>([]);
    const logsEndRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) {
            showToast('Please select a file', 'error');
            return;
        }

        // File size validation (10MB max)
        const MAX_FILE_SIZE = 10 * 1024 * 1024;
        if (file.size > MAX_FILE_SIZE) {
            showToast('File size exceeds 10MB limit', 'error');
            return;
        }

        setLoading(true);
        setProcessing(false);
        setUploadProgress(0);
        setStatusMessage("Starting upload...");
        setLogs(["Starting upload..."]);
        setError('');

        try {
            const formData = new FormData();
            formData.append('file', file);
            if (description) formData.append('description', description);
            if (additionalNotes) formData.append('additional_notes', additionalNotes);

            // Step 1: Upload File
            const response = await api.post('/uploads/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    const total = progressEvent.total || progressEvent.loaded;
                    const percent = Math.round((progressEvent.loaded * 100) / total);
                    setUploadProgress(percent);
                    if (percent === 100) {
                        setProcessing(true);
                        setStatusMessage("Upload complete. Starting processing...");
                        setLogs(prev => [...prev, "Upload complete. Starting processing..."]);
                    }
                },
            });

            const { upload_id } = response.data;

            // Step 2: Poll for Processing Status
            let isProcessing = true;
            while (isProcessing) {
                try {
                    const statusRes = await api.get(`/uploads/${upload_id}`);
                    const { vector_status, processing_step, page_count } = statusRes.data;

                    if (processing_step) {
                        setStatusMessage(processing_step);
                        // Avoid duplicates if step hasn't changed
                        setLogs(prev => {
                            if (prev[prev.length - 1] !== processing_step) {
                                return [...prev, processing_step];
                            }
                            return prev;
                        });
                    }

                    if (vector_status === 'COMPLETED') {
                        showToast(`File uploaded successfully! Processed ${page_count} pages.`, 'success');
                        router.push('/dashboard/files');
                        isProcessing = false;
                    } else if (vector_status === 'FAILED') {
                        throw new Error(processing_step || "Processing failed");
                    } else {
                        // Wait 1 second before next poll
                        await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                } catch (pollErr) {
                    console.error("Polling error:", pollErr);
                    // If polling fails (network jitter), don't crash, just retry
                    // But if it's the specific error we threw above, rethrow
                    if (pollErr instanceof Error && pollErr.message.includes("Processing failed")) {
                        throw pollErr;
                    }
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }

        } catch (err: any) {
            let message = 'Upload failed';
            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                message = Array.isArray(detail)
                    ? detail.map((d: any) => d.msg).join(', ')
                    : typeof detail === 'object'
                        ? JSON.stringify(detail)
                        : String(detail);
            } else if (err.message) {
                message = err.message;
            }
            showToast(message, 'error');
            setError(message);
        } finally {
            setLoading(false);
            setUploadProgress(0);
            setStatusMessage('');
        }
    };

    return (
        <div className="max-w-4xl mx-auto animate-fadeIn">
            <div className="mb-8">
                <h1 className="text-3xl font-bold gradient-text mb-2">
                    Upload Discharge Summary
                </h1>
                <p className="text-text-secondary">
                    Upload your medical discharge documents for AI-powered analysis
                </p>
            </div>

            <div className="glass-card p-8">
                <form onSubmit={handleSubmit}>
                    {error && (
                        <div className="mb-6 p-3 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    {/* File Upload Dropzone */}
                    <div
                        className={`upload-dropzone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById('fileInput')?.click()}
                    >
                        <input
                            id="fileInput"
                            type="file"
                            className="hidden"
                            onChange={handleFileChange}
                            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                        />

                        <div className="upload-content">
                            {file ? (
                                <>
                                    <div className="text-6xl mb-4">📄</div>
                                    <p className="text-lg font-semibold text-text-primary mb-2">
                                        {file.name}
                                    </p>
                                    <p className="text-sm text-text-muted">
                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                    <button
                                        type="button"
                                        className="mt-4 text-sm text-primary-light hover:text-primary"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setFile(null);
                                        }}
                                    >
                                        Remove file
                                    </button>
                                </>
                            ) : (
                                <>
                                    <div className="text-6xl mb-4">📤</div>
                                    <p className="text-lg font-semibold text-text-primary mb-2">
                                        Drag and drop your file here
                                    </p>
                                    <p className="text-sm text-text-muted mb-4">
                                        or click to browse
                                    </p>
                                    <p className="text-xs text-text-muted">
                                        Supports: PDF, JPG, PNG, DOC, DOCX
                                    </p>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Progress Bar (Only when uploading) */}
                    {loading && !processing && (
                        <div className="mt-6">
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-text-secondary">Uploading file...</span>
                                <span className="text-text-primary font-medium">{uploadProgress}%</span>
                            </div>
                            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                                <div
                                    className="h-full bg-[#4F86ED] transition-all duration-300 ease-out shadow-[0_0_10px_rgba(79,134,237,0.5)]"
                                    style={{ width: `${uploadProgress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    {/* Processing UI (Loader + Logs) */}
                    {processing && (
                        <div className="mt-8 flex flex-col items-center animate-fadeIn">
                            {/* Large Spinner */}
                            <div className="relative mb-6">
                                <div className="w-16 h-16 border-4 border-slate-100 rounded-full"></div>
                                <div className="w-16 h-16 border-4 border-[#4F86ED] rounded-full border-t-transparent animate-spin absolute top-0 left-0"></div>
                                <div className="absolute top-0 left-0 w-16 h-16 flex items-center justify-center">
                                    <span className="text-2xl animate-pulse">🧠</span>
                                </div>
                            </div>

                            <h3 className="text-lg font-bold text-slate-800 mb-1">Processing Document</h3>
                            <p className="text-slate-500 text-sm mb-6">AI is analyzing text and structure...</p>

                            {/* Processing Log (Scrollbar) */}
                            <div className="w-full p-4 bg-slate-900 rounded-xl border border-slate-800 h-48 overflow-y-auto custom-scrollbar font-mono text-xs text-slate-300 shadow-inner">
                                {logs.map((log, i) => (
                                    <div key={i} className="mb-2 last:mb-0 border-b border-slate-800/50 last:border-0 pb-1 last:pb-0 flex gap-3">
                                        <span className="text-[#4F86ED] select-none font-bold">➜</span>
                                        <span className="leading-relaxed">{log}</span>
                                    </div>
                                ))}
                                <div className="flex gap-2 animate-pulse mt-2">
                                    <span className="text-[#4F86ED] select-none font-bold">➜</span>
                                    <span className="w-2 h-4 bg-[#4F86ED]"></span>
                                </div>
                                <div ref={logsEndRef} />
                            </div>
                        </div>
                    )}

                    {/* Description */}
                    <div className="mt-6">
                        <label className="input-label">
                            Description
                        </label>
                        <input
                            type="text"
                            className="input"
                            placeholder="e.g., Discharge summary from City Hospital"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>

                    {/* Additional Notes */}
                    <div className="mt-4">
                        <label className="input-label">
                            Additional Notes (Optional)
                        </label>
                        <textarea
                            className="input"
                            rows={4}
                            placeholder="Any additional information about this document..."
                            value={additionalNotes}
                            onChange={(e) => setAdditionalNotes(e.target.value)}
                        />
                    </div>

                    {/* Submit Button */}
                    <div className="mt-6 flex gap-4">
                        <button
                            type="submit"
                            className="btn btn-primary flex-1"
                            disabled={loading || !file}
                        >
                            {loading ? (
                                <>
                                    <div className="spinner" />
                                    {uploadProgress < 100 ? 'Uploading...' : 'Processing...'}
                                </>
                            ) : (
                                '✓ Upload Document'
                            )}
                        </button>
                        <button
                            type="button"
                            className="btn btn-outline"
                            onClick={() => router.push('/dashboard/files')}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                    </div>
                </form>
            </div>

            <style jsx>{`
        .upload-dropzone {
          border: 2px dashed var(--border);
          border-radius: var(--radius-lg);
          padding: 3rem;
          text-align: center;
          cursor: pointer;
          transition: all var(--transition-base);
          background: var(--bg-secondary);
        }

        .upload-dropzone:hover {
          border-color: var(--primary);
          background: var(--bg-tertiary);
          transform: translateY(-2px);
        }

        .upload-dropzone.active {
          border-color: var(--primary);
          background: var(--bg-tertiary);
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
        }

        .upload-dropzone.has-file {
          border-color: var(--secondary);
          background: rgba(20, 184, 166, 0.05);
        }

        .upload-content {
          pointer-events: none;
        }

        .hidden {
          display: none;
        }

        textarea.input {
          resize: vertical;
        }
      `}</style>
        </div>
    );
}
