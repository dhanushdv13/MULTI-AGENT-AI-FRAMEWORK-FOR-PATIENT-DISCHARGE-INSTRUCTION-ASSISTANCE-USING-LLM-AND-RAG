'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

export default function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  const navigation = [
    { name: 'Upload Document', href: '/dashboard/upload', icon: '📤' },
    { name: 'All Files', href: '/dashboard/files', icon: '📁' },
  ];

  const isActive = (href: string) => pathname === href;

  return (
    <div className="w-full md:w-[280px] h-auto md:h-screen relative md:sticky top-0 left-0 bg-slate-50 border-b md:border-b-0 md:border-r border-slate-200 flex flex-col p-6 z-50">
      {/* Logo */}
      <div className="mb-8 pb-6 border-b border-slate-200">
        <div className="flex items-center gap-2 mb-1">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#4F86ED" />
            <path d="M2 17L12 22L22 17" stroke="#4F86ED" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M2 12L12 17L22 12" stroke="#4F86ED" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">
            Dischargo
          </h2>
        </div>
        <p className="text-xs text-slate-500 pl-8">
          Medical Intelligence
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-2">
        {navigation.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${isActive(item.href)
              ? 'bg-gradient-to-br from-[#4F86ED] to-[#3A6BC7] text-white shadow-md shadow-blue-500/25'
              : 'text-slate-600 hover:bg-slate-200 hover:text-slate-900 hover:translate-x-1'
              }`}
          >
            <span className="flex items-center justify-center">
              {item.icon === '📤' && (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
              )}
              {item.icon === '📁' && (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              )}
            </span>
            <span>{item.name}</span>
          </Link>
        ))}
      </nav>

      {/* Logout Button */}
      <div className="pt-6 border-t border-slate-200">
        <button
          onClick={logout}
          className="flex items-center gap-3 w-full px-4 py-3 text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
          Logout
        </button>
      </div>
    </div>
  );
}
