'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const { isAuthenticated } = useAuth();
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
        if (!isAuthenticated()) {
            router.push('/login');
        }
    }, [router, isAuthenticated]);

    // Prevent hydration mismatch by rendering nothing until mounted on client
    if (!isMounted) {
        return null;
    }

    // If mounted but not authenticated, return null (redirecting)
    if (!isAuthenticated()) {
        return null;
    }

    return <>{children}</>;
}
