'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Layers,
  Activity,
  AlertTriangle,
  DollarSign,
  Network,
  Play,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ConnectionStatus } from '@/components/realtime/ConnectionStatus';

const navigation = [
  { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Workloads', href: '/build', icon: Layers },
  { name: 'Jobs', href: '/jobs', icon: Activity },
  { name: 'Network', href: '/network', icon: Network },
  { name: 'Incidents', href: '/incidents', icon: AlertTriangle },
  { name: 'Billing', href: '/billing', icon: DollarSign },
  { name: 'Demo', href: '/demo', icon: Play },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-12">
              <Link href="/dashboard" className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-9 h-9 bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
                    <div className="w-5 h-5 border-2 border-white rounded-sm"></div>
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-white"></div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-slate-900 tracking-tight">
                    ClusterCloud
                  </div>
                  <div className="text-xs text-slate-500 -mt-0.5">
                    Control Plane
                  </div>
                </div>
              </Link>

              <nav className="hidden lg:flex items-center gap-2">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        'flex items-center gap-2.5 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200',
                        isActive
                          ? 'bg-indigo-50 text-indigo-700 shadow-sm'
                          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      )}
                    >
                      <Icon className="w-4 h-4" />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="flex items-center gap-5">
              <ConnectionStatus />
              
              <div className="h-8 w-px bg-slate-200"></div>
              
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-medium text-slate-900">
                    Production
                  </div>
                  <div className="text-xs text-slate-500">
                    customer-demo-001
                  </div>
                </div>
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center text-white text-sm font-semibold shadow-md">
                  PR
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto px-8 py-8 max-w-[1400px]">{children}</main>
    </div>
  );
}
