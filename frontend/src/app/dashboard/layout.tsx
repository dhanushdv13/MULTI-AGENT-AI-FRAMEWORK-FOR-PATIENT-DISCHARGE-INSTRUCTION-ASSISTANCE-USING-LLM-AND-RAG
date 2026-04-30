'use client';

import ProtectedRoute from '@/components/ProtectedRoute';
import Sidebar from '@/components/Sidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="flex flex-col md:flex-row h-screen bg-slate-50 overflow-hidden">
        <Sidebar />
        <main className="flex-1 p-6 md:p-8 overflow-y-auto h-full">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}
