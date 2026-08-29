'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Activity, Clock, Zap, CheckCircle, XCircle, Loader } from 'lucide-react';

interface Job {
  job_id: string;
  workload_type: string;
  status: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  budget_clstr: number;
  created_at: string;
  progress_percentage: number;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [creating, setCreating] = useState(false);

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

  const createDemoJob = async () => {
    setCreating(true);
    try {
      const response = await fetch('http://localhost:8000/api/jobs/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: 'customer:customer-demo-001',
          workload_type: 'frame_rendering',
          parameters: {
            project_name: 'Demo Job',
            total_frames: 10,
            frame_range_start: 1,
            frame_range_end: 10,
          },
          budget_clstr: 1000,
        }),
      });

      if (response.ok) {
        const newJob = await response.json();
        setJobs([newJob, ...jobs]);
        alert('Job created successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to create job: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to create job:', error);
      alert('Failed to create job. Check console for details.');
    } finally {
      setCreating(false);
    }
  };

  const filteredJobs = Array.isArray(jobs) ? jobs.filter((job) => {
    if (filter === 'all') return true;
    if (filter === 'active')
      return ['running', 'pending', 'submitted'].includes(job.status.toLowerCase());
    if (filter === 'completed') return job.status.toLowerCase() === 'completed';
    if (filter === 'failed') return job.status.toLowerCase() === 'failed';
    return true;
  }) : [];

  const stats = {
    total: jobs.length,
    active: jobs.filter((j) =>
      ['running', 'pending', 'submitted'].includes(j.status.toLowerCase())
    ).length,
    completed: jobs.filter((j) => j.status.toLowerCase() === 'completed').length,
    failed: jobs.filter((j) => j.status.toLowerCase() === 'failed').length,
  };

  const getStatusConfig = (status: string) => {
    const s = status.toLowerCase();
    if (s === 'completed') return { 
      color: 'from-emerald-500 to-emerald-600', 
      bg: 'bg-emerald-500/10', 
      border: 'border-emerald-500/30',
      text: 'text-emerald-400',
      icon: CheckCircle
    };
    if (s === 'running') return { 
      color: 'from-blue-500 to-blue-600', 
      bg: 'bg-blue-500/10', 
      border: 'border-blue-500/30',
      text: 'text-blue-400',
      icon: Zap
    };
    if (s === 'failed') return { 
      color: 'from-red-500 to-red-600', 
      bg: 'bg-red-500/10', 
      border: 'border-red-500/30',
      text: 'text-red-400',
      icon: XCircle
    };
    return { 
      color: 'from-yellow-500 to-yellow-600', 
      bg: 'bg-yellow-500/10', 
      border: 'border-yellow-500/30',
      text: 'text-yellow-400',
      icon: Loader
    };
  };

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
        {/* Header */}
        <div className="flex items-center justify-between animate-fadeIn">
          <div>
            <h1 className="text-4xl font-bold text-[#153B44] mb-2 flex items-center gap-3">
              <div className="w-1.5 h-10 bg-[#FF6B35] rounded-full"></div>
              Jobs Dashboard
            </h1>
            <p className="text-[#153B44]/60 text-lg">Monitor and manage your distributed workloads</p>
          </div>
          
          {/* Create Job Button */}
          <button
            onClick={createDemoJob}
            disabled={creating}
            className="flex items-center gap-2 px-6 py-3 bg-[#FF6B35] text-white rounded-full font-semibold hover:-translate-y-1 hover:shadow-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {creating ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                Create Demo Job
              </>
            )}
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { label: 'Total Jobs', value: stats.total, gradient: 'from-blue-500 to-blue-600', delay: 0 },
            { label: 'Active', value: stats.active, gradient: 'from-purple-500 to-purple-600', delay: 0.1 },
            { label: 'Completed', value: stats.completed, gradient: 'from-emerald-500 to-emerald-600', delay: 0.2 },
            { label: 'Failed', value: stats.failed, gradient: 'from-red-500 to-red-600', delay: 0.3 },
          ].map((stat, i) => (
            <button
              key={stat.label}
              onClick={() => setFilter(stat.label.toLowerCase() === 'total jobs' ? 'all' : stat.label.toLowerCase())}
              className={`group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border p-6 hover:-translate-y-1 transition-all duration-500 hover:shadow-xl ${
                filter === (stat.label.toLowerCase() === 'total jobs' ? 'all' : stat.label.toLowerCase())
                  ? 'border-blue-500 shadow-lg shadow-blue-500/20'
                  : 'border-slate-700/50 hover:border-blue-500/50'
              }`}
              style={{ animation: `fadeInUp 0.6s ease-out ${stat.delay}s both` }}
            >
              <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 bg-gradient-to-br ${stat.gradient}`}></div>
              <div className="relative">
                <p className="text-slate-400 text-sm font-medium mb-2">{stat.label}</p>
                <p className="text-4xl font-bold text-white group-hover:scale-110 transition-transform duration-300">{stat.value}</p>
              </div>
              <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
            </button>
          ))}
        </div>

        {/* Jobs List */}
        <div className="rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 overflow-hidden animate-fadeInUp" style={{ animationDelay: '0.4s' }}>
          <div className="p-6 border-b border-slate-700/50 bg-gradient-to-r from-slate-800/50 to-slate-800/30">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <Activity className="w-6 h-6 text-blue-400" />
              {filter === 'all' ? 'All Jobs' : `${filter.charAt(0).toUpperCase() + filter.slice(1)} Jobs`}
            </h2>
          </div>

          {filteredJobs.length === 0 ? (
            <div className="p-16 text-center">
              <div className="inline-flex p-4 rounded-full bg-slate-800 mb-4">
                <Activity className="w-8 h-8 text-slate-600" />
              </div>
              <p className="text-slate-400 text-lg">
                {filter === 'all' ? 'No jobs created yet' : `No ${filter} jobs`}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {filteredJobs.map((job, index) => {
                const statusConfig = getStatusConfig(job.status);
                const StatusIcon = statusConfig.icon;
                
                return (
                  <div
                    key={job.job_id}
                    className="p-6 hover:bg-slate-800/30 transition-all duration-300 group"
                    style={{ animation: `slideInRight 0.5s ease-out ${index * 0.05}s both` }}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl bg-gradient-to-br ${statusConfig.color} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                          <StatusIcon className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors">
                            {job.workload_type.replace(/_/g, ' ').toUpperCase()}
                          </h3>
                          <div className="flex items-center gap-3 mt-1">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.border} ${statusConfig.text} border`}>
                              {job.status.toUpperCase()}
                            </span>
                            <span className="flex items-center gap-1.5 text-slate-400 text-sm">
                              <Clock className="w-4 h-4" />
                              {new Date(job.created_at).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <p className="text-2xl font-bold text-white">{Math.round(job.progress_percentage)}%</p>
                        <p className="text-slate-400 text-sm">Complete</p>
                      </div>
                    </div>

                    {/* Progress Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
                        <p className="text-slate-400 text-xs mb-1">Total Tasks</p>
                        <p className="text-lg font-bold text-white">{job.total_tasks}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
                        <p className="text-slate-400 text-xs mb-1">Completed</p>
                        <p className="text-lg font-bold text-emerald-400">{job.completed_tasks}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
                        <p className="text-slate-400 text-xs mb-1">Budget</p>
                        <p className="text-lg font-bold text-blue-400">{job.budget_clstr} CLSTR</p>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="relative w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`absolute inset-y-0 left-0 bg-gradient-to-r ${statusConfig.color} rounded-full transition-all duration-1000 shadow-lg`}
                        style={{ width: `${job.progress_percentage}%` }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                      </div>
                    </div>

                    {/* Job ID */}
                    <p className="text-xs text-slate-500 mt-3 font-mono">{job.job_id}</p>
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
