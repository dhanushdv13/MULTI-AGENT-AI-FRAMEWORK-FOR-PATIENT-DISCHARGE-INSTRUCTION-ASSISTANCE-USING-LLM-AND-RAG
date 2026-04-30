'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Upload, ChatMessage } from '@/types';
import { useToast } from '@/context/ToastContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function FileDetailPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const { showToast } = useToast();
    const [file, setFile] = useState<Upload | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputMessage, setInputMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const [error, setError] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // ── sessionStorage helpers — chat persists within session, per document ──
    const storageKey = (vectorId: string) => `chat_history_${vectorId}`;

    const loadMessages = (vectorId: string): ChatMessage[] => {
        try {
            const raw = sessionStorage.getItem(storageKey(vectorId));
            if (!raw) return [];
            const parsed = JSON.parse(raw) as Array<Omit<ChatMessage, 'timestamp'> & { timestamp: string }>;
            return parsed.map((m) => ({ ...m, timestamp: new Date(m.timestamp) }));
        } catch {
            return [];
        }
    };

    const saveMessages = (vectorId: string, msgs: ChatMessage[]) => {
        try {
            sessionStorage.setItem(storageKey(vectorId), JSON.stringify(msgs));
        } catch {
            // sessionStorage full or unavailable — silently ignore
        }
    };

    const clearChat = () => {
        if (!file?.vector_id) return;
        sessionStorage.removeItem(storageKey(file.vector_id));
        setMessages([]);
        showToast('Chat history cleared', 'success');
    };

    useEffect(() => {
        fetchFile();
    }, [params.id]);

    // Load stored messages once the file (and its vector_id) is known
    useEffect(() => {
        if (file?.vector_id) {
            setMessages(loadMessages(file.vector_id));
        }
    }, [file?.vector_id]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchFile = async () => {
        try {
            const response = await api.get(`/uploads/${params.id}`);
            setFile(response.data);
        } catch (err: any) {
            let message = 'Failed to fetch file';
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

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const sendMessage = async () => {
        if (!inputMessage.trim() || !file?.vector_id) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: inputMessage,
            timestamp: new Date(),
        };

        // Save user message immediately to sessionStorage
        setMessages((prev) => {
            const updated = [...prev, userMessage];
            saveMessages(file.vector_id!, updated);
            return updated;
        });
        setInputMessage('');
        setSending(true);

        try {
            const response = await api.post(`/chat/${file.vector_id}`, {
                message: inputMessage,
            });

            const agentMessage: ChatMessage = {
                role: 'agent',
                content: response.data.response,
                agent: response.data.agent,
                timestamp: new Date(),
            };

            setMessages((prev) => {
                const updated = [...prev, agentMessage];
                saveMessages(file.vector_id!, updated);
                return updated;
            });
        } catch (err: any) {
            let message = 'Failed to send message';
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
            setSending(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // Helper to safely format timestamp
    const formatTimestamp = (ts: Date | string) => {
        const date = ts instanceof Date ? ts : new Date(ts);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner" style={{ width: '40px', height: '40px' }} />
            </div>
        );
    }

    if (error && !file) {
        return (
            <div className="glass-card p-8 text-center">
                <div className="text-6xl mb-4">⚠️</div>
                <h2 className="text-xl font-semibold mb-2">Error</h2>
                <p className="text-text-secondary mb-6">{error}</p>
                <button onClick={() => router.push('/dashboard/files')} className="btn btn-primary">
                    Back to Files
                </button>
            </div>
        );
    }

    if (!file) return null;

    return (
        <div className="max-w-7xl mx-auto animate-fade-in-down h-full flex flex-col">
            {/* Header */}
            <div className="mb-6 flex-none">
                <button
                    onClick={() => router.push('/dashboard/files')}
                    className="text-slate-500 hover:text-[#4F86ED] mb-4 flex items-center gap-2 transition-colors font-medium text-sm"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
                    </svg>
                    Back to Files
                </button>
                <h1 className="text-3xl font-bold text-slate-900">{file.filename}</h1>
            </div>

            {/* 30/70 Split Layout */}
            <div className="flex flex-col lg:flex-row gap-8 flex-1 min-h-0">
                {/* Left Panel - 30% */}
                <div className="w-full lg:w-[30%] flex flex-col gap-6 h-full">
                    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm overflow-hidden flex flex-col h-full">
                        <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-slate-800 border-b border-slate-100 pb-4 flex-none">
                            <span className="text-2xl">📄</span> details
                        </h2>

                        <div className="flex-1 space-y-6 overflow-y-auto pr-2 custom-scrollbar">
                            <div className="pb-4 border-b border-slate-100">
                                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Filename</label>
                                <p className="text-slate-900 font-medium break-all">{file.filename}</p>
                            </div>

                            {file.description && (
                                <div className="pb-4 border-b border-slate-100">
                                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Description</label>
                                    <p className="text-slate-700 leading-relaxed text-sm">{file.description}</p>
                                </div>
                            )}

                            <div className="grid grid-cols-1 gap-4 pb-4 border-b border-slate-100">
                                <div>
                                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Upload Date</label>
                                    <p className="text-slate-900 text-sm">
                                        {new Date(file.created_at).toLocaleString()}
                                    </p>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Status</label>
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide ${file.vector_status?.toUpperCase() === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                                        }`}>
                                        {file.vector_status}
                                    </span>
                                </div>
                            </div>

                            {file.vector_id && (
                                <div className="pb-4 border-b border-slate-100">
                                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Vector ID</label>
                                    <p className="text-slate-500 font-mono text-xs break-all bg-slate-50 p-2 rounded border border-slate-100">{file.vector_id}</p>
                                </div>
                            )}



                            {/* Additional Notes */}
                            {file.additional_notes && (
                                <div>
                                    <h3 className="text-sm font-semibold mb-2 flex items-center gap-2 text-slate-800">
                                        <span className="text-lg">📝</span> Notes
                                    </h3>
                                    <p className="text-slate-600 italic bg-yellow-50 p-3 rounded-lg border border-yellow-100 text-sm">{file.additional_notes}</p>
                                </div>
                            )}

                            {/* Original File Info */}
                            {/* Original File Info & Actions */}
                            <div className="mt-auto pt-6 flex flex-col gap-3">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Actions</h3>
                                <div className="flex flex-col gap-2">
                                    <div className="flex flex-col gap-3">
                                        <button
                                            onClick={() => router.push(`/dashboard/files/${params.id}/content`)}
                                            className="flex items-center justify-center gap-2 px-4 py-2 bg-white border border-slate-200 hover:border-[#4F86ED] text-slate-700 hover:text-[#4F86ED] rounded-lg transition-all shadow-sm hover:shadow-md text-sm font-medium group"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-slate-400 group-hover:text-[#4F86ED] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                            </svg>
                                            View Original
                                        </button>

                                        <button
                                            onClick={() => router.push(`/dashboard/files/${params.id}/extracted`)}
                                            className="flex items-center justify-center gap-2 px-4 py-2 bg-white border border-slate-200 hover:border-blue-600 text-slate-700 hover:text-blue-600 rounded-lg transition-all shadow-sm hover:shadow-md text-sm font-medium group"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-slate-400 group-hover:text-blue-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                            </svg>
                                            View Extracted Content
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Panel - 70% Chat */}
                <div className="w-full lg:w-[70%] h-[600px] lg:h-full flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                    <div className="p-4 border-b border-slate-100 bg-slate-50/50 backdrop-blur-sm flex-none flex items-center justify-between">
                        <div>
                            <h2 className="text-lg font-bold flex items-center gap-2 text-slate-800">
                                <span>💬</span> AI Chat Assistant
                            </h2>
                            <p className="text-xs text-slate-500 mt-1 pl-7">
                                Ask questions about this document
                            </p>
                        </div>
                        {messages.length > 0 && (
                            <button
                                onClick={clearChat}
                                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-red-500 px-3 py-1.5 rounded-lg hover:bg-red-50 border border-transparent hover:border-red-100 transition-all"
                                title="Clear chat history for this document"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                                Clear Chat
                            </button>
                        )}
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-slate-50/30">
                        {messages.length === 0 ? (
                            <div className="text-center py-12 flex flex-col items-center justify-center opacity-70">
                                <div className="text-5xl mb-4 grayscale opacity-50">🤖</div>
                                <p className="text-slate-500 text-sm font-medium">
                                    Start a conversation about this document
                                </p>
                                <div className="mt-6 text-xs text-slate-400 bg-white p-4 rounded-lg border border-slate-100 shadow-sm max-w-xs">
                                    <p className="font-bold mb-2 uppercase tracking-wide text-gray-300">Suggested Queries</p>
                                    <ul className="space-y-2 text-left">
                                        <li className="flex items-center gap-2 hover:text-[#4F86ED] cursor-pointer transition-colors">✨ Bills and insurance coverage</li>
                                        <li className="flex items-center gap-2 hover:text-[#4F86ED] cursor-pointer transition-colors">✨ Diet and nutrition info</li>
                                        <li className="flex items-center gap-2 hover:text-[#4F86ED] cursor-pointer transition-colors">✨ Medication prices</li>
                                    </ul>
                                </div>
                            </div>
                        ) : (
                            <>
                                {messages.map((msg, idx) => (
                                    <div
                                        key={idx}
                                        className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
                                    >
                                        <div className="flex items-center gap-2 mb-1 px-1">
                                            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                                                {msg.role === 'user' ? 'You' : (msg.agent || 'AI Assistant')}
                                            </span>
                                            <span className="text-[10px] text-slate-300">
                                                {formatTimestamp(msg.timestamp)}
                                            </span>
                                        </div>
                                        <div className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm overflow-hidden ${msg.role === 'user'
                                            ? 'bg-[#4F86ED] text-white rounded-tr-none'
                                            : 'bg-white border border-slate-200 text-slate-700 rounded-tl-none'
                                            }`}>
                                            <div className="prose prose-sm max-w-none break-words">
                                                <ReactMarkdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                                        a: ({ node, ...props }) => <a className="text-blue-600 hover:underline font-medium" target="_blank" rel="noopener noreferrer" {...props} />,
                                                        ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
                                                        ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                                                        li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                                                        h1: ({ node, ...props }) => <h1 className="text-lg font-bold mb-2 mt-4" {...props} />,
                                                        h2: ({ node, ...props }) => <h2 className="text-base font-bold mb-2 mt-3" {...props} />,
                                                        h3: ({ node, ...props }) => <h3 className="text-sm font-bold mb-1 mt-2" {...props} />,
                                                        blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2 text-gray-600" {...props} />,
                                                        table: ({ node, ...props }) => <div className="overflow-x-auto my-2"><table className="min-w-full divide-y divide-gray-200 border" {...props} /></div>,
                                                        th: ({ node, ...props }) => <th className="px-3 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b" {...props} />,
                                                        td: ({ node, ...props }) => <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 border-b" {...props} />,
                                                        code: ({ node, ...props }) => <code className="bg-gray-100 rounded px-1 py-0.5 text-xs font-mono text-pink-600" {...props} />,
                                                        pre: ({ node, ...props }) => <pre className="bg-gray-800 text-white p-3 rounded-lg overflow-x-auto my-2 text-xs" {...props} />,
                                                    }}
                                                >
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                <div ref={messagesEndRef} />
                            </>
                        )}

                        {sending && (
                            <div className="flex flex-col max-w-[85%] mr-auto items-start animate-pulse">
                                <div className="flex items-center gap-2 mb-1 px-1">
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">AI Assistant</span>
                                </div>
                                <div className="p-4 rounded-2xl rounded-tl-none bg-white border border-slate-200 text-slate-700 shadow-sm">
                                    <div className="flex items-center gap-2 text-sm">
                                        <div className="w-2 h-2 bg-[#4F86ED] rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                                        <div className="w-2 h-2 bg-[#4F86ED] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                        <div className="w-2 h-2 bg-[#4F86ED] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                                        <span className="ml-2 text-slate-400">Thinking...</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Input */}
                    <div className="p-4 border-t border-slate-200 bg-white shadow-sm z-10 flex-none">
                        <div className="flex gap-2 relative">
                            <input
                                type="text"
                                className="w-full pl-5 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#4F86ED]/20 focus:border-[#4F86ED] transition-all shadow-inner"
                                placeholder="Ask a question about this document..."
                                value={inputMessage}
                                onChange={(e) => setInputMessage(e.target.value)}
                                onKeyDown={handleKeyPress}
                                disabled={sending}
                            />
                            <button
                                onClick={sendMessage}
                                className="absolute right-2 top-2 p-2 bg-[#4F86ED] hover:bg-[#3A6BC7] text-white rounded-lg shadow-md transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed"
                                disabled={!inputMessage.trim() || sending}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
