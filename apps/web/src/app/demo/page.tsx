'use client';

import { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { ActivityFeed } from '@/components/realtime/ActivityFeed';
import { IncidentRecoveryVisualization } from '@/components/demo/IncidentRecoveryVisualization';
import { FailureSimulator } from '@/components/demo/FailureSimulator';
import { ImpactAnalysisPanel } from '@/components/demo/ImpactAnalysisPanel';
import { api, type Job, type Node, type Incident } from '@/lib/api';
import { useRealtimeEvent } from '@/hooks/useWebSocket';
import {
  formatCLSTR,
  formatTimestamp,
  getStatusColor,
  calculateProgress,
} from '@/lib/utils';
import {
  Zap,
  Server,
  Activity,
  TrendingUp,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';
import Link from 'next/link';

export default function DemoPage() {
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [activeIncident, setActiveIncident] = useState<any | null>(null);
  const [demoPhase, setDemoPhase] = useState<
    'idle' | 'creating' | 'running' | 'incident' | 'completed'
  >('idle');

  // Load data
  useEffect(() => {
    async function loadData() {
      try {
        const [jobsData, nodesData, incidentsData] = await Promise.all([
          api.getJobs(),
          api.getNodes(),
          api.getIncidents(),
        ]);

        // Find most recent active job
        const runningJob = jobsData.find((j) =>
          ['RUNNING', 'ALLOCATED', 'RECOVERING'].includes(j.status)
        );
        if (runningJob) {
          setActiveJob(runningJob);
          setDemoPhase('running');
        }

        setNodes(nodesData);

        // Find active incident
        const activeInc = incidentsData.find(
          (i) => i.status !== 'RESOLVED'
        );
        if (activeInc) {
          setActiveIncident(activeInc);
          setDemoPhase('incident');
        }
      } catch (error) {
        console.error('Failed to load demo data:', error);
      }
    }

    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, []);

  // Listen to real-time events
  useRealtimeEvent(
    [
      'job_started',
      'task_completed',
      'node_failed',
      'recovery_started',
      'recovery_completed',
    ],
    (event) => {
      console.log('Demo event:', event);

      if (event.event_type === 'job_started') {
        setDemoPhase('running');
      } else if (event.event_type === 'node_failed') {
        setDemoPhase('incident');
      } else if (event.event_type === 'recovery_completed') {
        setDemoPhase('running');
      }
    }
  );

  const handleStartDemo = async () => {
    setDemoPhase('creating');

    try {
      const job = await api.createJob({
        workload_type: '3D Rendering',
        total_frames: 20,
        deadline_hours: 1,
        total_budget_clstr: 500,
        min_reliability: 0.85,
        requires_gpu: true,
      });

      setActiveJob(job);
      setDemoPhase('running');
    } catch (error) {
      console.error('Failed to start demo:', error);
      alert('Failed to start demo job');
      setDemoPhase('idle');
    }
  };

  const healthyNodes = nodes.filter((n) => n.status === 'HEALTHY');
  const targetNode = healthyNodes[0]; // For failure simulation

  const progress = activeJob
    ? calculateProgress(activeJob.completed_frames, activeJob.total_frames)
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-600 to-purple-600 rounded-2xl p-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">
                ClusterCloud Live Demo
              </h1>
              <p className="text-primary-100 text-lg">
                Distributed rendering with automatic failure recovery
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-primary-100 mb-1">Demo Phase</div>
              <Badge className="bg-white text-primary-700 text-lg px-4 py-2">
                {demoPhase.toUpperCase()}
              </Badge>
            </div>
          </div>
        </div>

        {/* Demo Control */}
        {demoPhase === 'idle' && (
          <Card className="border-2 border-primary-300 bg-gradient-to-br from-primary-50 to-purple-50">
            <CardBody className="text-center py-12">
              <Sparkles className="w-16 h-16 text-primary-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                Ready to Demonstrate
              </h2>
              <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
                This demo will showcase the complete ClusterCloud workflow: AI
                workload analysis, automatic cluster composition, distributed
                execution, failure detection, AI-driven recovery, and economic
                settlement.
              </p>
              <Button onClick={handleStartDemo} size="lg" className="gap-2">
                <Zap className="w-5 h-5" />
                Start Demo Job
              </Button>
            </CardBody>
          </Card>
        )}

        {demoPhase === 'creating' && (
          <Card>
            <CardBody className="text-center py-12">
              <Zap className="w-12 h-12 text-primary-600 animate-pulse mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Creating Job...
              </h3>
              <p className="text-gray-600">
                AI analyzing workload and composing cluster
              </p>
            </CardBody>
          </Card>
        )}

        {/* Active Job */}
        {activeJob && (demoPhase === 'running' || demoPhase === 'incident') && (
          <div className="space-y-6">
            {/* Job Progress */}
            <Card className="border-2 border-primary-200">
              <CardHeader className="bg-gradient-to-r from-primary-50 to-purple-50">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-primary-900">
                      Active Rendering Job
                    </CardTitle>
                    <p className="text-sm text-primary-700 mt-1">
                      {activeJob.workload_type} - {activeJob.total_frames}{' '}
                      frames
                    </p>
                  </div>
                  <Badge className={getStatusColor(activeJob.status)}>
                    {activeJob.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardBody className="space-y-4">
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Progress</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {progress}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Completed</div>
                    <div className="text-2xl font-bold text-green-600">
                      {activeJob.completed_frames}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Remaining</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {activeJob.total_frames - activeJob.completed_frames}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Budget</div>
                    <div className="text-2xl font-bold text-primary-600">
                      {formatCLSTR(activeJob.total_budget_clstr)}
                    </div>
                  </div>
                </div>

                <ProgressBar value={progress} size="lg" showLabel />

                {activeJob.failed_frames > 0 && (
                  <div className="flex items-center gap-2 text-orange-700 bg-orange-50 rounded-lg p-3">
                    <AlertTriangle className="w-5 h-5" />
                    <span className="font-medium">
                      {activeJob.failed_frames} frames failed (recovering)
                    </span>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Failure Simulator (only if not already failed) */}
            {!activeIncident && targetNode && (
              <FailureSimulator
                nodeId={targetNode.node_id}
                disabled={demoPhase === 'incident'}
              />
            )}

            {/* Impact Analysis & Recovery (new enhanced panel) */}
            {activeIncident && (
              <ImpactAnalysisPanel
                nodeId={activeIncident.node_id || activeIncident.related_node_id}
                incidentId={activeIncident.incident_id}
                onExecuteRecovery={() => {
                  // Refresh data after recovery
                  setTimeout(() => {
                    window.location.reload();
                  }, 2000);
                }}
              />
            )}

            {/* Original Incident Visualization (fallback) */}
            {activeIncident && !activeIncident.node_id && (
              <IncidentRecoveryVisualization incident={activeIncident} />
            )}

            {/* Network Status */}
            <Card>
              <CardHeader>
                <CardTitle>Network Nodes</CardTitle>
              </CardHeader>
              <CardBody>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {nodes.slice(0, 3).map((node) => (
                    <div
                      key={node.node_id}
                      className={`border-2 rounded-lg p-4 ${
                        node.status === 'HEALTHY'
                          ? 'border-green-200 bg-green-50'
                          : node.status === 'UNHEALTHY'
                          ? 'border-red-200 bg-red-50'
                          : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <Server
                          className={`w-8 h-8 ${
                            node.status === 'HEALTHY'
                              ? 'text-green-600'
                              : node.status === 'UNHEALTHY'
                              ? 'text-red-600'
                              : 'text-gray-600'
                          }`}
                        />
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900">
                            {node.name}
                          </div>
                          <Badge
                            className={getStatusColor(node.status)}
                          >
                            {node.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600">
                        <div>CPU: {node.cpu_cores} cores</div>
                        <div>RAM: {node.total_ram_gb}GB</div>
                        <div>
                          Reliability: {(node.reliability_score * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          </div>
        )}

        {demoPhase === 'completed' && (
          <Card className="border-2 border-green-300 bg-gradient-to-br from-green-50 to-emerald-50">
            <CardBody className="text-center py-12">
              <CheckCircle2 className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                Demo Complete!
              </h2>
              <p className="text-gray-600 mb-6">
                Job completed successfully with automatic recovery
              </p>
              <Button onClick={() => setDemoPhase('idle')} size="lg">
                Reset Demo
              </Button>
            </CardBody>
          </Card>
        )}

        {/* Live Activity */}
        <ActivityFeed />
      </div>
    </DashboardLayout>
  );
}
