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
    <div className="min-h-screen bg-[#F5F1E7]">
      <header className="bg-white border-b border-[#153B44]/10 sticky top-0 z-50 shadow-sm">
        <div className="mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-12">
              <Link href="/dashboard" className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-10 h-10 bg-[#153B44] rounded-xl flex items-center justify-center shadow-md">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#FF8A65"/>
                      <path d="M2 17L12 22L22 17" stroke="#FF8A65" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M2 12L12 17L22 12" stroke="#FFB199" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  </div>
                </div>
                <div>
                  <div className="text-xl font-bold text-[#153B44] tracking-tight">
                    ClusterCloud
                  </div>
                  <div className="text-xs text-[#FF6B35] font-semibold -mt-0.5">
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
                        'flex items-center gap-2.5 px-4 py-2.5 rounded-full text-sm font-semibold transition-all duration-300',
                        isActive
                          ? 'bg-[#FF8A65] text-white shadow-md'
                          : 'text-[#153B44] hover:bg-[#FF8A65]/10 hover:text-[#FF6B35]'
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
              
              <div className="h-8 w-px bg-[#153B44]/10"></div>
              
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-bold text-[#153B44]">
                    Production
                  </div>
                  <div className="text-xs text-[#FF6B35] font-medium">
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
