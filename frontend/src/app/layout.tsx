import './globals.css';
import type { Metadata } from 'next';

import { ToastProvider } from '@/context/ToastContext';

export const metadata: Metadata = {
    title: 'Dischargo - Medical Document Management',
    description: 'AI-powered discharge summary analysis and management',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>
                <ToastProvider>
                    {children}
                </ToastProvider>
            </body>
        </html>
    );
}
