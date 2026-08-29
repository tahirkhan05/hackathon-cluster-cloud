'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { 
  Activity, 
  Server, 
  Zap, 
  TrendingUp,
  Clock,
  Database,
  Cpu,
  Check
} from 'lucide-react';

interface Stats {
  total_nodes: number;
  active_nodes: number;
  total_jobs: number;
  active_jobs: number;
  total_tasks: number;
  completed_tasks: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({
    total_nodes: 0,
    active_nodes: 0,
    total_jobs: 0,
    active_jobs: 0,
    total_tasks: 0,
    completed_tasks: 0,
  });
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsRes, balanceRes] = await Promise.all([
          fetch('http://localhost:8000/api/stats'),
          fetch('http://localhost:8000/api/ledger/balance/customer:customer-demo-001')
        ]);
        
        const statsData = await statsRes.json();
        const balanceData = await balanceRes.json();
        
        setStats(statsData);
        setBalance(balanceData.balance || 0);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-[#FF8A65]/20 border-t-[#FF8A65] rounded-full animate-spin"></div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-12 pb-12">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl bg-white p-12 md:p-16 card-shadow">
          {/* Decorative blob */}
          <div className="absolute -right-40 -top-40 w-96 h-96 bg-[#FF8A65] opacity-20 rounded-full animate-blob"></div>
          <div className="absolute -right-20 top-20 w-64 h-64 bg-[#FFB199] opacity-30 rounded-full animate-float" style={{ animationDelay: '1s' }}></div>
          
          {/* Dot pattern overlay */}
          <div className="absolute inset-0 dot-pattern opacity-30"></div>

          <div className="relative">
            <div className="inline-block mb-4">
              <span className="text-[#FF6B35] text-sm font-semibold tracking-wide uppercase">
                Control Plane
              </span>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-[#153B44] mb-6 leading-tight">
              Engineering <span className="gradient-text">the future</span>
              <br />
              of <span className="text-[#FF6B35]">distributed</span> computing.
            </h1>
            <p className="text-[#153B44]/70 text-xl max-w-2xl leading-relaxed">
              Intelligent orchestration platform built for scale, designed for simplicity.
            </p>

            {/* CTA */}
            <div className="mt-10">
              <button className="inline-flex items-center gap-2 px-8 py-4 bg-[#153B44] text-white rounded-full font-medium hover:-translate-y-1 transition-all duration-300 hover:shadow-xl">
                <span>Explore System</span>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="animate-bounce">
                  <path d="M8 3L8 13M8 13L12 9M8 13L4 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { label: 'Active Nodes', value: stats.active_nodes, total: stats.total_nodes, icon: Server },
            { label: 'Running Jobs', value: stats.active_jobs, total: stats.total_jobs, icon: Activity },
            { label: 'Tasks Complete', value: stats.completed_tasks, total: stats.total_tasks, icon: Check },
            { label: 'CLSTR Balance', value: balance.toLocaleString(), total: null, icon: Zap },
          ].map((stat, i) => (
            <div
              key={stat.label}
              className="group bg-white rounded-2xl p-6 card-shadow hover-lift"
              style={{ animation: `fadeInUp 0.6s ease-out ${i * 0.1}s both` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-[#FF8A65]/10 rounded-xl group-hover:bg-[#FF8A65]/20 transition-colors">
                  <stat.icon className="w-6 h-6 text-[#FF6B35]" />
                </div>
              </div>
              <h3 className="text-3xl font-bold text-[#153B44] mb-1">
                {stat.value}
                {stat.total !== null && <span className="text-lg text-[#153B44]/40">/{stat.total}</span>}
              </h3>
              <p className="text-[#153B44]/60 text-sm font-medium">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* System Metrics */}
        <div>
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-[#153B44] mb-2">System Metrics</h2>
            <p className="text-[#153B44]/60">Real-time performance monitoring</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Network Status */}
            <div className="bg-white rounded-2xl p-8 card-shadow hover-lift">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-[#153B44] flex items-center gap-3">
                  <Database className="w-6 h-6 text-[#FF6B35]" />
                  Network Status
                </h3>
                <span className="flex items-center gap-2 text-emerald-600 text-sm font-semibold">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </span>
                  Online
                </span>
              </div>

              <div className="space-y-4">
                {[
                  { label: 'CPU Utilization', value: '45%', icon: Cpu, color: '#FF6B35' },
                  { label: 'Memory Usage', value: '62%', icon: Database, color: '#FF8A65' },
                  { label: 'Avg Task Time', value: '3.2s', icon: Clock, color: '#FFB199' },
                ].map((metric, i) => (
                  <div
                    key={metric.label}
                    className="flex items-center justify-between p-4 rounded-xl bg-[#F5F1E7] hover:bg-[#EEEAE0] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <metric.icon className="w-5 h-5" style={{ color: metric.color }} />
                      <div>
                        <p className="text-[#153B44] font-semibold">{metric.label}</p>
                        <p className="text-[#153B44]/50 text-sm">Cluster average</p>
                      </div>
                    </div>
                    <span className="text-2xl font-bold text-[#153B44]">{metric.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-2xl p-8 card-shadow hover-lift">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-[#153B44] flex items-center gap-3">
                  <Activity className="w-6 h-6 text-[#FF6B35]" />
                  Recent Activity
                </h3>
              </div>

              <div className="space-y-3">
                {[
                  { event: 'Node registered', detail: 'TDESK joined cluster', time: '2m ago' },
                  { event: 'Job completed', detail: 'Rendering task finished', time: '5m ago' },
                  { event: 'Tasks assigned', detail: `${stats.total_tasks} tasks distributed`, time: '8m ago' },
                  { event: 'Heartbeat received', detail: 'All nodes healthy', time: '10m ago' },
                ].map((activity, i) => (
                  <div 
                    key={i}
                    className="flex items-center gap-4 p-4 rounded-xl bg-[#F5F1E7] hover:bg-[#EEEAE0] transition-all"
                    style={{ animation: `slideInRight 0.5s ease-out ${i * 0.1}s both` }}
                  >
                    <div className="w-2 h-2 rounded-full bg-[#FF6B35]"></div>
                    <div className="flex-1">
                      <p className="text-[#153B44] font-semibold text-sm">{activity.event}</p>
                      <p className="text-[#153B44]/50 text-xs">{activity.detail}</p>
                    </div>
                    <span className="text-[#153B44]/40 text-xs font-medium">{activity.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Performance Insights */}
        <div className="bg-white rounded-2xl p-8 card-shadow">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-2xl font-bold text-[#153B44] mb-1">Performance Insights</h3>
              <p className="text-[#153B44]/60">System health and efficiency metrics</p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 rounded-full">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              <span className="text-emerald-600 font-semibold">99.9% Uptime</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { label: 'Response Time', value: '< 100ms', trend: '+12%', good: true },
              { label: 'Task Success Rate', value: '98.5%', trend: '+2.3%', good: true },
              { label: 'Resource Efficiency', value: '87%', trend: '+5%', good: true },
            ].map((insight, i) => (
              <div
                key={insight.label}
                className="p-6 rounded-xl bg-[#F5F1E7] border-2 border-transparent hover:border-[#FF8A65]/30 transition-all"
                style={{ animation: `fadeInUp 0.6s ease-out ${i * 0.1}s both` }}
              >
                <p className="text-[#153B44]/60 text-sm font-medium mb-2">{insight.label}</p>
                <div className="flex items-end justify-between">
                  <h4 className="text-3xl font-bold text-[#153B44]">{insight.value}</h4>
                  <span className={`text-sm font-semibold ${insight.good ? 'text-emerald-600' : 'text-red-600'}`}>
                    {insight.trend}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
