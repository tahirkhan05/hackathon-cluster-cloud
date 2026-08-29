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
  HardDrive
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

  const StatCard = ({ 
    title, 
    value, 
    subtitle, 
    icon: Icon, 
    gradient,
    delay 
  }: { 
    title: string; 
    value: string | number; 
    subtitle: string; 
    icon: any; 
    gradient: string;
    delay: number;
  }) => (
    <div 
      className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 p-6 hover:border-blue-500/50 transition-all duration-500 hover:shadow-xl hover:shadow-blue-500/10 hover:-translate-y-1"
      style={{ 
        animation: `fadeInUp 0.6s ease-out ${delay}s both`,
      }}
    >
      {/* Animated gradient background */}
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 bg-gradient-to-br ${gradient}`}></div>
      
      {/* Icon with glow effect */}
      <div className={`relative mb-4 inline-flex p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-lg`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      
      {/* Content */}
      <div className="relative">
        <p className="text-slate-400 text-sm font-medium mb-1">{title}</p>
        <h3 className="text-3xl font-bold text-white mb-1 transition-transform duration-300 group-hover:scale-105">
          {value}
        </h3>
        <p className="text-slate-500 text-sm">{subtitle}</p>
      </div>

      {/* Hover shine effect */}
      <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
    </div>
  );

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
            <div className="absolute inset-0 w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8 pb-8">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 p-8 md:p-12">
          {/* Animated background elements */}
          <div className="absolute inset-0 opacity-30">
            <div className="absolute top-10 left-10 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl animate-blob"></div>
            <div className="absolute top-0 right-10 w-72 h-72 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000"></div>
            <div className="absolute bottom-10 left-20 w-72 h-72 bg-pink-400 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-4000"></div>
          </div>

          <div className="relative">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 animate-fadeIn">
              ClusterCloud Control Plane
            </h1>
            <p className="text-blue-100 text-lg md:text-xl max-w-2xl animate-fadeIn" style={{ animationDelay: '0.2s' }}>
              Intelligent distributed computing platform with AI-powered orchestration and real-time monitoring
            </p>
            
            {/* Quick stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 hover:bg-white/20 transition-all duration-300">
                <p className="text-blue-100 text-sm">Active Nodes</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.active_nodes}</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 hover:bg-white/20 transition-all duration-300">
                <p className="text-blue-100 text-sm">Running Jobs</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.active_jobs}</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 hover:bg-white/20 transition-all duration-300">
                <p className="text-blue-100 text-sm">Tasks Complete</p>
                <p className="text-3xl font-bold text-white mt-1">{stats.completed_tasks}</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 hover:bg-white/20 transition-all duration-300">
                <p className="text-blue-100 text-sm">CLSTR Balance</p>
                <p className="text-3xl font-bold text-white mt-1">{balance.toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* System Metrics */}
        <div>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <div className="w-1 h-8 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
            System Metrics
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Nodes"
              value={stats.total_nodes}
              subtitle="Compute resources"
              icon={Server}
              gradient="from-blue-500 to-blue-600"
              delay={0}
            />
            <StatCard
              title="Active Jobs"
              value={stats.active_jobs}
              subtitle="Currently processing"
              icon={Activity}
              gradient="from-purple-500 to-purple-600"
              delay={0.1}
            />
            <StatCard
              title="Task Completion"
              value={`${stats.completed_tasks}/${stats.total_tasks}`}
              subtitle="Overall progress"
              icon={Zap}
              gradient="from-pink-500 to-pink-600"
              delay={0.2}
            />
            <StatCard
              title="System Health"
              value="99.9%"
              subtitle="Uptime this month"
              icon={TrendingUp}
              gradient="from-emerald-500 to-emerald-600"
              delay={0.3}
            />
          </div>
        </div>

        {/* Performance Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Network Status */}
          <div className="rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 p-6 hover:border-blue-500/50 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600">
                  <Database className="w-5 h-5 text-white" />
                </div>
                Network Status
              </h3>
              <span className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                Online
              </span>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-blue-500/30 transition-all duration-300">
                <div className="flex items-center gap-3">
                  <Cpu className="w-5 h-5 text-blue-400" />
                  <div>
                    <p className="text-white font-medium">CPU Utilization</p>
                    <p className="text-slate-400 text-sm">Across all nodes</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-white">45%</span>
              </div>

              <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-purple-500/30 transition-all duration-300">
                <div className="flex items-center gap-3">
                  <HardDrive className="w-5 h-5 text-purple-400" />
                  <div>
                    <p className="text-white font-medium">Memory Usage</p>
                    <p className="text-slate-400 text-sm">Average across cluster</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-white">62%</span>
              </div>

              <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-pink-500/30 transition-all duration-300">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-pink-400" />
                  <div>
                    <p className="text-white font-medium">Avg Task Time</p>
                    <p className="text-slate-400 text-sm">Last 24 hours</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-white">3.2s</span>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 p-6 hover:border-purple-500/50 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                Recent Activity
              </h3>
            </div>

            <div className="space-y-3">
              {[
                { event: 'Node registered', detail: 'TDESK joined the cluster', time: '2m ago', color: 'blue' },
                { event: 'Job completed', detail: 'frame_rendering #ad4971', time: '5m ago', color: 'emerald' },
                { event: 'Task assigned', detail: '5 tasks distributed', time: '8m ago', color: 'purple' },
                { event: 'Heartbeat received', detail: 'All nodes healthy', time: '10m ago', color: 'pink' },
              ].map((activity, i) => (
                <div 
                  key={i}
                  className="flex items-center gap-4 p-3 rounded-xl bg-slate-800/30 border border-slate-700/30 hover:border-slate-600 hover:bg-slate-800/50 transition-all duration-300"
                  style={{ animation: `slideInRight 0.5s ease-out ${i * 0.1}s both` }}
                >
                  <div className={`w-2 h-2 rounded-full bg-${activity.color}-400 animate-pulse`}></div>
                  <div className="flex-1">
                    <p className="text-white font-medium text-sm">{activity.event}</p>
                    <p className="text-slate-400 text-xs">{activity.detail}</p>
                  </div>
                  <span className="text-slate-500 text-xs">{activity.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes blob {
          0% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          100% {
            transform: translate(0px, 0px) scale(1);
          }
        }

        .animate-blob {
          animation: blob 7s infinite;
        }

        .animation-delay-2000 {
          animation-delay: 2s;
        }

        .animation-delay-4000 {
          animation-delay: 4s;
        }

        .animate-fadeIn {
          animation: fadeIn 1s ease-out;
        }
      `}</style>
    </DashboardLayout>
  );
}
