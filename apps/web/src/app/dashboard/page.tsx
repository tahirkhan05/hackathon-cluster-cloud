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
            <div className="h-8 bg-gray-200 rounded w-64 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-xl"></div>
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
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome back
            </h1>
            <p className="text-gray-600 mt-1">
              Your distributed cloud is ready to build
            </p>
          </div>
          <Link href="/build">
            <Button size="lg" className="gap-2">
              <Zap className="w-5 h-5" />
              Build My Cloud
            </Button>
          </Link>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Balance */}
          <Card className="bg-gradient-to-br from-primary-500 to-primary-700 border-0 text-white">
            <CardBody className="space-y-2">
              <div className="flex items-center gap-2 text-primary-100">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm font-medium">Balance</span>
              </div>
              <div className="text-3xl font-bold">
                {formatCLSTR(balance)}
              </div>
              <div className="text-sm text-primary-100">
                Available to spend
              </div>
            </CardBody>
          </Card>

          {/* Active Jobs */}
          <Card>
            <CardBody className="space-y-2">
              <div className="flex items-center gap-2 text-gray-500">
                <Activity className="w-4 h-4" />
                <span className="text-sm font-medium">Active Jobs</span>
              </div>
              <div className="text-3xl font-bold text-gray-900">
                {stats?.active_jobs || 0}
              </div>
              <div className="text-sm text-gray-500">
                {stats?.total_jobs || 0} total jobs
              </div>
            </CardBody>
          </Card>

          {/* Network Health */}
          <Card>
            <CardBody className="space-y-2">
              <div className="flex items-center gap-2 text-gray-500">
                <Server className="w-4 h-4" />
                <span className="text-sm font-medium">Network</span>
              </div>
              <div className="text-3xl font-bold text-gray-900">
                {stats?.healthy_nodes || 0}/{stats?.total_nodes || 0}
              </div>
              <div className="text-sm text-green-600 font-medium">
                Healthy nodes
              </div>
            </CardBody>
          </Card>

          {/* Tasks Completed */}
          <Card>
            <CardBody className="space-y-2">
              <div className="flex items-center gap-2 text-gray-500">
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-sm font-medium">Completed</span>
              </div>
              <div className="text-3xl font-bold text-gray-900">
                {stats?.total_tasks_completed || 0}
              </div>
              <div className="text-sm text-gray-500">Total tasks</div>
            </CardBody>
          </Card>
        </div>

        {/* Two Column Layout: Jobs + Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Jobs - Takes 2 columns */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Recent Jobs</CardTitle>
                <Link
                  href="/jobs"
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                >
                  View all
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </CardHeader>
              <CardBody className="p-0">
                {recentJobs.length === 0 ? (
                  <div className="px-6 py-12 text-center">
                    <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No jobs yet
                    </h3>
                    <p className="text-gray-600 mb-6">
                      Build your first cloud to get started
                    </p>
                    <Link href="/build">
                      <Button>
                        <Zap className="w-4 h-4 mr-2" />
                        Build My Cloud
                      </Button>
                    </Link>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {recentJobs.map((job) => {
                      const progress = calculateProgress(
                        job.completed_frames,
                        job.total_frames
                      );

                      return (
                        <Link
                          key={job.job_id}
                          href={`/jobs/${job.job_id}`}
                          className="block px-6 py-4 hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-1">
                                <h4 className="font-semibold text-gray-900">
                                  {job.workload_type}
                                </h4>
                                <Badge
                                  className={getStatusColor(job.status)}
                                >
                                  {job.status}
                                </Badge>
                              </div>
                              <div className="flex items-center gap-4 text-sm text-gray-600">
                                <span className="flex items-center gap-1">
                                  <Activity className="w-3.5 h-3.5" />
                                  {job.completed_frames}/{job.total_frames} frames
                                </span>
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3.5 h-3.5" />
                                  {formatTimestamp(job.created_at)}
                                </span>
                              </div>
                            </div>
                            <div className="text-right ml-6">
                              <div className="text-lg font-semibold text-gray-900">
                                {formatCLSTR(job.total_budget_clstr)}
                              </div>
                              <div className="text-sm text-gray-500">Budget</div>
                            </div>
                          </div>
                          <ProgressBar value={progress} size="sm" />
                          {job.failed_frames > 0 && (
                            <div className="flex items-center gap-1 text-sm text-orange-600 mt-2">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              {job.failed_frames} failed frames
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

          {/* Live Activity Feed - Takes 1 column */}
          <ActivityFeed />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="hover:shadow-md transition-shadow cursor-pointer group">
            <Link href="/build">
              <CardBody className="text-center py-8">
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-primary-200 transition-colors">
                  <Zap className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  Build New Cloud
                </h3>
                <p className="text-sm text-gray-600">
                  Create a distributed workload
                </p>
              </CardBody>
            </Link>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer group">
            <Link href="/network">
              <CardBody className="text-center py-8">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-green-200 transition-colors">
                  <Server className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  View Network
                </h3>
                <p className="text-sm text-gray-600">
                  See available compute nodes
                </p>
              </CardBody>
            </Link>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer group">
            <Link href="/balance">
              <CardBody className="text-center py-8">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-purple-200 transition-colors">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  View Balance
                </h3>
                <p className="text-sm text-gray-600">
                  Track your CLSTR spending
                </p>
              </CardBody>
            </Link>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
