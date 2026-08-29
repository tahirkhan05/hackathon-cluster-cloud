'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { api, type Job } from '@/lib/api';
import {
  formatCLSTR,
  formatTimestamp,
  getStatusColor,
  calculateProgress,
} from '@/lib/utils';
import {
  Activity,
  Clock,
  Zap,
  AlertTriangle,
  ChevronRight,
} from 'lucide-react';

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    async function loadJobs() {
      try {
        const data = await api.getJobs();
        setJobs(data);
      } catch (error) {
        console.error('Failed to load jobs:', error);
      } finally {
        setLoading(false);
      }
    }

    loadJobs();
    const interval = setInterval(loadJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  const filteredJobs = jobs.filter((job) => {
    if (filter === 'all') return true;
    if (filter === 'active')
      return ['RUNNING', 'ALLOCATED', 'SCHEDULING'].includes(job.status);
    if (filter === 'completed') return job.status === 'COMPLETED';
    if (filter === 'failed') return job.status === 'FAILED';
    return true;
  });

  const stats = {
    total: jobs.length,
    active: jobs.filter((j) =>
      ['RUNNING', 'ALLOCATED', 'SCHEDULING'].includes(j.status)
    ).length,
    completed: jobs.filter((j) => j.status === 'COMPLETED').length,
    failed: jobs.filter((j) => j.status === 'FAILED').length,
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-48"></div>
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded-xl"></div>
            ))}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Jobs</h1>
            <p className="text-gray-600 mt-1">
              Monitor your distributed workloads
            </p>
          </div>
          <Link href="/build">
            <Button className="gap-2">
              <Zap className="w-4 h-4" />
              Build New Cloud
            </Button>
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <button
            onClick={() => setFilter('all')}
            className={`text-left ${
              filter === 'all' ? 'ring-2 ring-primary-500' : ''
            }`}
          >
            <Card>
              <CardBody>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.total}
                </div>
                <div className="text-sm text-gray-600">Total Jobs</div>
              </CardBody>
            </Card>
          </button>

          <button
            onClick={() => setFilter('active')}
            className={`text-left ${
              filter === 'active' ? 'ring-2 ring-primary-500' : ''
            }`}
          >
            <Card>
              <CardBody>
                <div className="text-2xl font-bold text-green-600">
                  {stats.active}
                </div>
                <div className="text-sm text-gray-600">Active</div>
              </CardBody>
            </Card>
          </button>

          <button
            onClick={() => setFilter('completed')}
            className={`text-left ${
              filter === 'completed' ? 'ring-2 ring-primary-500' : ''
            }`}
          >
            <Card>
              <CardBody>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.completed}
                </div>
                <div className="text-sm text-gray-600">Completed</div>
              </CardBody>
            </Card>
          </button>

          <button
            onClick={() => setFilter('failed')}
            className={`text-left ${
              filter === 'failed' ? 'ring-2 ring-primary-500' : ''
            }`}
          >
            <Card>
              <CardBody>
                <div className="text-2xl font-bold text-red-600">
                  {stats.failed}
                </div>
                <div className="text-sm text-gray-600">Failed</div>
              </CardBody>
            </Card>
          </button>
        </div>

        {/* Jobs List */}
        <Card>
          <CardBody className="p-0">
            {filteredJobs.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No jobs found
                </h3>
                <p className="text-gray-600 mb-6">
                  {filter === 'all'
                    ? 'Create your first job to get started'
                    : `No ${filter} jobs`}
                </p>
                {filter === 'all' && (
                  <Link href="/build">
                    <Button>
                      <Zap className="w-4 h-4 mr-2" />
                      Build My Cloud
                    </Button>
                  </Link>
                )}
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {filteredJobs.map((job) => {
                  const progress = calculateProgress(
                    job.completed_frames,
                    job.total_frames
                  );

                  return (
                    <Link
                      key={job.job_id}
                      href={`/jobs/${job.job_id}`}
                      className="block px-6 py-5 hover:bg-gray-50 transition-colors group"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold text-gray-900">
                              {job.workload_type}
                            </h3>
                            <Badge className={getStatusColor(job.status)}>
                              {job.status}
                            </Badge>
                          </div>

                          <div className="flex items-center gap-6 text-sm text-gray-600 mb-3">
                            <span className="flex items-center gap-1.5">
                              <Activity className="w-4 h-4" />
                              {job.completed_frames}/{job.total_frames} frames
                            </span>
                            <span className="flex items-center gap-1.5">
                              <Clock className="w-4 h-4" />
                              {formatTimestamp(job.created_at)}
                            </span>
                            <span className="font-medium text-gray-900">
                              {formatCLSTR(job.total_budget_clstr)}
                            </span>
                          </div>

                          <ProgressBar value={progress} size="sm" />

                          {job.failed_frames > 0 && (
                            <div className="flex items-center gap-1 text-sm text-orange-600 mt-2">
                              <AlertTriangle className="w-4 h-4" />
                              {job.failed_frames} failed frames
                            </div>
                          )}
                        </div>

                        <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-gray-600 transition-colors ml-4" />
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </DashboardLayout>
  );
}
