'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Zap,
  Activity,
  AlertCircle,
  Wallet,
  Network,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ConnectionStatus } from '@/components/realtime/ConnectionStatus';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Build Cloud', href: '/build', icon: Zap },
  { name: 'Jobs', href: '/jobs', icon: Activity },
  { name: 'Incidents', href: '/incidents', icon: AlertCircle },
  { name: 'Network', href: '/network', icon: Network },
  { name: 'Balance', href: '/balance', icon: Wallet },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <Link href="/dashboard" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">
                  ClusterCloud
                </span>
              </Link>

              {/* Navigation */}
              <nav className="hidden md:flex items-center gap-1">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      )}
                    >
                      <Icon className="w-4 h-4" />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* User section */}
            <div className="flex items-center gap-4">
              <ConnectionStatus />
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">
                  Customer Demo
                </div>
                <div className="text-xs text-gray-500">
                  customer-demo-001
                </div>
              </div>
              <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold">
                CD
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto px-6 py-8 max-w-7xl">{children}</main>
    </div>
  );
}
