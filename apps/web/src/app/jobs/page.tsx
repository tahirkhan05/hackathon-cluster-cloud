'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';

interface Job {
  job_id: string;
  workload_type: string;
  status: string;
  total_frames: number;
  completed_frames: number;
  failed_frames: number;
  total_budget_clstr: number;
  created_at: string;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    async function loadJobs() {
      try {
        const res = await fetch('http://localhost:8000/api/jobs/');
        const data = await res.json();
        setJobs(data.jobs || []);
      } catch (error) {
        console.error('Failed to load jobs:', error);
      } finally {
        setLoading(false);
      }
    }

    loadJobs();
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredJobs = Array.isArray(jobs) ? jobs.filter((job) => {
    if (filter === 'all') return true;
    if (filter === 'active')
      return ['RUNNING', 'ALLOCATED', 'SCHEDULING', 'PENDING'].includes(job.status);
    if (filter === 'completed') return job.status === 'COMPLETED';
    if (filter === 'failed') return job.status === 'FAILED';
    return true;
  }) : [];

  const stats = {
    total: jobs.length,
    active: jobs.filter((j) =>
      ['RUNNING', 'ALLOCATED', 'SCHEDULING', 'PENDING'].includes(j.status)
    ).length,
    completed: jobs.filter((j) => j.status === 'COMPLETED').length,
    failed: jobs.filter((j) => j.status === 'FAILED').length,
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'text-emerald-400 bg-emerald-500/10';
      case 'RUNNING': return 'text-blue-400 bg-blue-500/10';
      case 'FAILED': return 'text-red-400 bg-red-500/10';
      case 'PENDING': return 'text-yellow-400 bg-yellow-500/10';
      default: return 'text-slate-400 bg-slate-500/10';
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-8 text-center text-slate-400">Loading jobs...</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Jobs</h1>
          <p className="text-slate-400 mt-1">Distributed workload execution</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <button
            onClick={() => setFilter('all')}
            className={`text-left bg-slate-800/50 rounded-lg p-4 border transition-colors ${
              filter === 'all' ? 'border-indigo-500' : 'border-slate-700/50 hover:border-slate-600'
            }`}
          >
            <div className="text-slate-400 text-sm">Total Jobs</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {stats.total}
            </div>
          </button>

          <button
            onClick={() => setFilter('active')}
            className={`text-left bg-slate-800/50 rounded-lg p-4 border transition-colors ${
              filter === 'active' ? 'border-indigo-500' : 'border-slate-700/50 hover:border-slate-600'
            }`}
          >
            <div className="text-slate-400 text-sm">Active</div>
            <div className="text-2xl font-bold text-blue-400 mt-1">
              {stats.active}
            </div>
          </button>

          <button
            onClick={() => setFilter('completed')}
            className={`text-left bg-slate-800/50 rounded-lg p-4 border transition-colors ${
              filter === 'completed' ? 'border-indigo-500' : 'border-slate-700/50 hover:border-slate-600'
            }`}
          >
            <div className="text-slate-400 text-sm">Completed</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {stats.completed}
            </div>
          </button>

          <button
            onClick={() => setFilter('failed')}
            className={`text-left bg-slate-800/50 rounded-lg p-4 border transition-colors ${
              filter === 'failed' ? 'border-indigo-500' : 'border-slate-700/50 hover:border-slate-600'
            }`}
          >
            <div className="text-slate-400 text-sm">Failed</div>
            <div className="text-2xl font-bold text-red-400 mt-1">
              {stats.failed}
            </div>
          </button>
        </div>

        {/* Jobs List */}
        <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
          <div className="p-4 border-b border-slate-700/50">
            <h2 className="text-lg font-semibold text-slate-100">
              {filter === 'all' ? 'All Jobs' : `${filter.charAt(0).toUpperCase() + filter.slice(1)} Jobs`}
            </h2>
          </div>

          {filteredJobs.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              {filter === 'all' ? 'No jobs created yet' : `No ${filter} jobs`}
            </div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {filteredJobs.map((job) => {
                const progress = job.total_frames > 0 
                  ? Math.round((job.completed_frames / job.total_frames) * 100)
                  : 0;

                return (
                  <div
                    key={job.job_id}
                    className="p-4 hover:bg-slate-700/30 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(job.status)}`}>
                          {job.status}
                        </span>
                        <span className="text-slate-100 font-medium">
                          {job.workload_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="text-sm text-slate-400">
                        {new Date(job.created_at).toLocaleString()}
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <div className="flex gap-6">
                        <div>
                          <span className="text-slate-400">Progress: </span>
                          <span className="text-slate-100">{job.completed_frames}/{job.total_frames} frames ({progress}%)</span>
                        </div>
                        {job.failed_frames > 0 && (
                          <div>
                            <span className="text-slate-400">Failed: </span>
                            <span className="text-red-400">{job.failed_frames}</span>
                          </div>
                        )}
                        <div>
                          <span className="text-slate-400">Budget: </span>
                          <span className="text-slate-100">{job.total_budget_clstr.toLocaleString()} CLSTR</span>
                        </div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mt-3 w-full bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>

                    <div className="text-xs text-slate-500 mt-2 font-mono">
                      {job.job_id}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
