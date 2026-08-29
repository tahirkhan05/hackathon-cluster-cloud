'use client';

import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { formatCLSTR, formatTimestamp } from '@/lib/utils';
import {
  AlertTriangle,
  XCircle,
  CheckCircle2,
  ArrowRight,
  Clock,
  DollarSign,
  RefreshCw,
  Zap,
  Server,
  Activity,
} from 'lucide-react';

interface IncidentData {
  incident_id: string;
  incident_type: string;
  severity: string;
  status: string;
  failed_node_id: string;
  failed_node_name: string;
  affected_task_ids: string[];
  replacement_node_id?: string;
  replacement_node_name?: string;
  recovery_reasoning?: string;
  detected_at: string;
  resolved_at?: string;
  recovery_actions: any[];
  economics?: {
    penalty_amount: number;
    compensation_amount: number;
    recovery_reward: number;
  };
}

interface Props {
  incident: IncidentData | null;
  loading?: boolean;
}

export function IncidentRecoveryVisualization({ incident, loading }: Props) {
  if (loading) {
    return (
      <Card className="border-orange-200 bg-orange-50">
        <CardBody className="text-center py-12">
          <RefreshCw className="w-12 h-12 text-orange-600 animate-spin mx-auto mb-4" />
          <p className="text-orange-900 font-medium">
            Detecting failure...
          </p>
        </CardBody>
      </Card>
    );
  }

  if (!incident) {
    return (
      <Card className="border-gray-200">
        <CardBody className="text-center py-12">
          <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Active Incidents
          </h3>
          <p className="text-gray-600">
            All nodes healthy and running smoothly
          </p>
        </CardBody>
      </Card>
    );
  }

  const isRecovering = incident.status === 'RECOVERING';
  const isResolved = incident.status === 'RESOLVED';
  const recoveryTime = incident.resolved_at && incident.detected_at
    ? Math.round(
        (new Date(incident.resolved_at).getTime() -
          new Date(incident.detected_at).getTime()) /
          1000
      )
    : 0;

  return (
    <Card className="border-2 border-orange-300 shadow-lg">
      <CardHeader className="bg-gradient-to-r from-orange-50 to-red-50 border-b border-orange-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-orange-900">
                Node Failure Detected
              </CardTitle>
              <p className="text-sm text-orange-700">
                Automatic recovery in progress
              </p>
            </div>
          </div>
          <Badge
            className={
              isResolved
                ? 'bg-green-100 text-green-700'
                : 'bg-orange-100 text-orange-700'
            }
          >
            {incident.status}
          </Badge>
        </div>
      </CardHeader>

      <CardBody className="space-y-6">
        {/* Failure Timeline */}
        <div className="flex items-center gap-4">
          {/* Failed Node */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <XCircle className="w-5 h-5 text-red-600" />
              <span className="text-sm font-medium text-gray-700">
                Failed Node
              </span>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-red-600" />
                <div className="flex-1">
                  <div className="font-semibold text-red-900">
                    {incident.failed_node_name || incident.failed_node_id.slice(0, 8)}
                  </div>
                  <div className="text-xs text-red-600">
                    {incident.affected_task_ids.length} tasks affected
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Arrow */}
          <ArrowRight className="w-6 h-6 text-gray-400 flex-shrink-0" />

          {/* Replacement Node */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <RefreshCw
                className={`w-5 h-5 ${
                  isResolved ? 'text-green-600' : 'text-orange-600 animate-spin'
                }`}
              />
              <span className="text-sm font-medium text-gray-700">
                Replacement Node
              </span>
            </div>
            {incident.replacement_node_id ? (
              <div
                className={`${
                  isResolved
                    ? 'bg-green-50 border-green-200'
                    : 'bg-blue-50 border-blue-200'
                } border rounded-lg p-3`}
              >
                <div className="flex items-center gap-2">
                  <Server
                    className={`w-4 h-4 ${
                      isResolved ? 'text-green-600' : 'text-blue-600'
                    }`}
                  />
                  <div className="flex-1">
                    <div
                      className={`font-semibold ${
                        isResolved ? 'text-green-900' : 'text-blue-900'
                      }`}
                    >
                      {incident.replacement_node_name ||
                        incident.replacement_node_id.slice(0, 8)}
                    </div>
                    <div
                      className={`text-xs ${
                        isResolved ? 'text-green-600' : 'text-blue-600'
                      }`}
                    >
                      {isResolved ? 'Recovery complete' : 'Reassigning tasks...'}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
                <div className="text-sm text-gray-500">Selecting...</div>
              </div>
            )}
          </div>
        </div>

        {/* AI Recovery Reasoning */}
        {incident.recovery_reasoning && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-purple-900 mb-1">
                  AI Recovery Decision
                </h4>
                <p className="text-sm text-purple-800 leading-relaxed">
                  {incident.recovery_reasoning}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Recovery Progress */}
        {isRecovering && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Recovery Progress
              </span>
              <span className="text-sm text-gray-600">
                {incident.affected_task_ids.length} tasks reassigning
              </span>
            </div>
            <ProgressBar value={50} size="md" className="mb-2" />
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Activity className="w-4 h-4 animate-pulse" />
              Reassigning tasks to replacement node...
            </div>
          </div>
        )}

        {/* Recovery Stats */}
        {isResolved && (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-4 h-4 text-gray-600" />
                <span className="text-xs font-medium text-gray-600">
                  Recovery Time
                </span>
              </div>
              <div className="text-lg font-bold text-gray-900">
                {recoveryTime}s
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-4 h-4 text-gray-600" />
                <span className="text-xs font-medium text-gray-600">
                  Tasks Recovered
                </span>
              </div>
              <div className="text-lg font-bold text-gray-900">
                {incident.affected_task_ids.length}
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span className="text-xs font-medium text-gray-600">
                  Status
                </span>
              </div>
              <div className="text-lg font-bold text-green-600">
                Complete
              </div>
            </div>
          </div>
        )}

        {/* Economic Impact */}
        {incident.economics && (
          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              Economic Settlement
            </h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="text-xs text-red-600 mb-1">Provider Penalty</div>
                <div className="text-lg font-bold text-red-700">
                  -{formatCLSTR(incident.economics.penalty_amount)}
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="text-xs text-blue-600 mb-1">
                  Customer Compensation
                </div>
                <div className="text-lg font-bold text-blue-700">
                  +{formatCLSTR(incident.economics.compensation_amount)}
                </div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="text-xs text-green-600 mb-1">
                  Recovery Reward
                </div>
                <div className="text-lg font-bold text-green-700">
                  +{formatCLSTR(incident.economics.recovery_reward)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="text-xs text-gray-500 flex items-center justify-between">
          <span>Detected: {formatTimestamp(incident.detected_at)}</span>
          {incident.resolved_at && (
            <span>Resolved: {formatTimestamp(incident.resolved_at)}</span>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
