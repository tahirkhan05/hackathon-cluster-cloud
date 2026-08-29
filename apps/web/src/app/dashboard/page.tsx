'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { ActivityFeed } from '@/components/realtime/ActivityFeed';
import { api, type Job, type Node } from '@/lib/api';
import {
  formatCLSTR,
  formatTimestamp,
  getStatusColor,
  calculateProgress,
} from '@/lib/utils';
import {
  Zap,
  TrendingUp,
  Activity,
  Server,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import Link from 'next/link';

interface DashboardStats {
  total_nodes: number;
  healthy_nodes: number;
  total_jobs: number;
  active_jobs: number;
  total_tasks_completed: number;
  total_clstr_transacted: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [balance, setBalance] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [statsData, jobsData, balanceData] = await Promise.all([
          api.getSystemStats(),
          api.getJobs(),
          api.getBalance('customer:customer-demo-001'),
        ]);

        setStats(statsData);
        setRecentJobs(jobsData.slice(0, 5));
        setBalance(balanceData.balance);
      } catch (error) {
        console.error('Failed to load dashboard:', error);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
    const interval = setInterval(loadDashboard, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="animate-pulse">
            <div className="h-8 bg-slate-200 rounded w-64 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-slate-200 rounded-xl"></div>
              ))}
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              System Overview
            </h1>
            <p className="text-slate-600 mt-1 text-sm">
              Monitor your distributed infrastructure and workload execution
            </p>
          </div>
          <Link href="/build">
            <Button size="lg" className="gap-2 shadow-md">
              <Zap className="w-4 h-4" />
              Create Workload
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-600 border-0 text-white shadow-lg">
            <CardBody className="space-y-2">
              <div className="flex items-center gap-2 text-indigo-100">
                <TrendingUp className="w-4 h-4" />
                <span className="text-xs font-medium uppercase tracking-wide">Account Balance</span>
              </div>
              <div className="text-3xl font-bold">
                {formatCLSTR(balance)}
              </div>
              <div className="text-sm text-indigo-100">
                Available credit
              </div>
            </CardBody>
          </Card>

          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardBody className="space-y-2">
              <div className="flex items-center gap-2 text-slate-500">
                <Activity className="w-4 h-4" />
                <span className="text-xs font-medium uppercase tracking-wide">Active Workloads</span>
              </div>
              <div className="text-3xl font-bold text-slate-900">
                {stats?.active_jobs || 0}
              </div>
              <div className="text-sm text-slate-500">
                {stats?.total_jobs || 0} total executed
              </div>
            </CardBody>
          </Card>

          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardBody className="space-y-2">
              <div className="flex items-center gap-2 text-slate-500">
                <Server className="w-4 h-4" />
                <span className="text-xs font-medium uppercase tracking-wide">Compute Nodes</span>
              </div>
              <div className="text-3xl font-bold text-slate-900">
                {stats?.healthy_nodes || 0}<span className="text-xl text-slate-400">/{stats?.total_nodes || 0}</span>
              </div>
              <div className="text-sm text-emerald-600 font-medium">
                Operational
              </div>
            </CardBody>
          </Card>

          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardBody className="space-y-2">
              <div className="flex items-center gap-2 text-slate-500">
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-xs font-medium uppercase tracking-wide">Tasks Processed</span>
              </div>
              <div className="text-3xl font-bold text-slate-900">
                {stats?.total_tasks_completed || 0}
              </div>
              <div className="text-sm text-slate-500">Lifetime total</div>
            </CardBody>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="flex items-center justify-between border-b border-slate-100 pb-4">
                <CardTitle className="text-slate-900">Recent Workloads</CardTitle>
                <Link
                  href="/jobs"
                  className="text-sm text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
                >
                  View all
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </CardHeader>
              <CardBody className="p-0">
                {recentJobs.length === 0 ? (
                  <div className="px-6 py-16 text-center">
                    <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <Activity className="w-8 h-8 text-slate-400" />
                    </div>
                    <h3 className="text-lg font-medium text-slate-900 mb-2">
                      No workloads executed
                    </h3>
                    <p className="text-slate-600 mb-6 text-sm">
                      Deploy your first distributed workload to see metrics here
                    </p>
                    <Link href="/build">
                      <Button>
                        <Zap className="w-4 h-4 mr-2" />
                        Create Workload
                      </Button>
                    </Link>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {recentJobs.map((job) => {
                      const progress = calculateProgress(
                        job.completed_frames,
                        job.total_frames
                      );

                      return (
                        <Link
                          key={job.job_id}
                          href={`/jobs/${job.job_id}`}
                          className="block px-6 py-5 hover:bg-slate-50 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h4 className="font-semibold text-slate-900">
                                  {job.workload_type}
                                </h4>
                                <Badge
                                  className={getStatusColor(job.status)}
                                >
                                  {job.status}
                                </Badge>
                              </div>
                              <div className="flex items-center gap-6 text-sm text-slate-600">
                                <span className="flex items-center gap-1.5">
                                  <Activity className="w-3.5 h-3.5" />
                                  {job.completed_frames}/{job.total_frames} tasks
                                </span>
                                <span className="flex items-center gap-1.5">
                                  <Clock className="w-3.5 h-3.5" />
                                  {formatTimestamp(job.created_at)}
                                </span>
                              </div>
                            </div>
                            <div className="text-right ml-6">
                              <div className="text-lg font-semibold text-slate-900">
                                {formatCLSTR(job.total_budget_clstr)}
                              </div>
                              <div className="text-sm text-slate-500">Allocated</div>
                            </div>
                          </div>
                          <ProgressBar value={progress} size="sm" />
                          {job.failed_frames > 0 && (
                            <div className="flex items-center gap-1.5 text-sm text-amber-600 mt-3">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              {job.failed_frames} failed tasks
                            </div>
                          )}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </CardBody>
            </Card>
          </div>

          <ActivityFeed />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-slate-200 hover:shadow-md transition-all cursor-pointer group hover:border-indigo-200">
            <Link href="/build">
              <CardBody className="text-center py-8">
                <div className="w-14 h-14 bg-gradient-to-br from-indigo-100 to-violet-100 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:from-indigo-200 group-hover:to-violet-200 transition-colors">
                  <Zap className="w-7 h-7 text-indigo-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">
                  Deploy Workload
                </h3>
                <p className="text-sm text-slate-600">
                  Configure and execute distributed tasks
                </p>
              </CardBody>
            </Link>
          </Card>

          <Card className="border-slate-200 hover:shadow-md transition-all cursor-pointer group hover:border-emerald-200">
            <Link href="/network">
              <CardBody className="text-center py-8">
                <div className="w-14 h-14 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:from-emerald-200 group-hover:to-teal-200 transition-colors">
                  <Server className="w-7 h-7 text-emerald-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">
                  Network Status
                </h3>
                <p className="text-sm text-slate-600">
                  Monitor compute node availability
                </p>
              </CardBody>
            </Link>
          </Card>

          <Card className="border-slate-200 hover:shadow-md transition-all cursor-pointer group hover:border-purple-200">
            <Link href="/balance">
              <CardBody className="text-center py-8">
                <div className="w-14 h-14 bg-gradient-to-br from-purple-100 to-fuchsia-100 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:from-purple-200 group-hover:to-fuchsia-200 transition-colors">
                  <TrendingUp className="w-7 h-7 text-purple-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">
                  Billing Overview
                </h3>
                <p className="text-sm text-slate-600">
                  Review token usage and spending
                </p>
              </CardBody>
            </Link>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
