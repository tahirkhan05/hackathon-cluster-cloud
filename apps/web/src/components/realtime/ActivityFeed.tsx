'use client';

import { useEventFeed } from '@/hooks/useWebSocket';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatTimestamp } from '@/lib/utils';
import {
  Activity,
  Server,
  Zap,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  DollarSign,
  RefreshCw,
  TrendingUp,
} from 'lucide-react';
import type { RealtimeEvent } from '@/lib/websocket';

const EVENT_ICONS: Record<string, any> = {
  node_joined: Server,
  node_selected: Server,
  node_failed: XCircle,
  job_started: Zap,
  job_completed: CheckCircle2,
  task_assigned: Activity,
  task_completed: CheckCircle2,
  task_failed: AlertTriangle,
  recovery_started: RefreshCw,
  replacement_selected: Server,
  recovery_completed: CheckCircle2,
  ledger_transaction: DollarSign,
  system_status: TrendingUp,
};

const EVENT_COLORS: Record<string, string> = {
  node_joined: 'bg-blue-100 text-blue-700',
  node_selected: 'bg-blue-100 text-blue-700',
  node_failed: 'bg-red-100 text-red-700',
  job_started: 'bg-purple-100 text-purple-700',
  job_completed: 'bg-green-100 text-green-700',
  task_assigned: 'bg-cyan-100 text-cyan-700',
  task_completed: 'bg-green-100 text-green-700',
  task_failed: 'bg-red-100 text-red-700',
  recovery_started: 'bg-orange-100 text-orange-700',
  replacement_selected: 'bg-blue-100 text-blue-700',
  recovery_completed: 'bg-green-100 text-green-700',
  ledger_transaction: 'bg-purple-100 text-purple-700',
  system_status: 'bg-gray-100 text-gray-700',
};

function getEventMessage(event: RealtimeEvent): string {
  const { event_type, data } = event;

  switch (event_type) {
    case 'node_joined':
      return `Node ${data.name} joined the network`;
    case 'node_selected':
      return `Node ${data.node_id?.slice(0, 8)} selected for job`;
    case 'node_failed':
      return `Node ${data.node_id?.slice(0, 8)} failed`;
    case 'job_started':
      return `Job ${data.job_id?.slice(0, 8)} started (${data.total_frames} frames)`;
    case 'job_completed':
      return `Job ${data.job_id?.slice(0, 8)} completed`;
    case 'task_assigned':
      return `Task assigned to node ${data.node_id?.slice(0, 8)}`;
    case 'task_completed':
      return `Task completed in ${data.duration_seconds?.toFixed(1)}s`;
    case 'task_failed':
      return `Task failed: ${data.error}`;
    case 'recovery_started':
      return `Recovery started for ${data.affected_task_count} tasks`;
    case 'replacement_selected':
      return `Replacement node ${data.replacement_node_id?.slice(0, 8)} selected`;
    case 'recovery_completed':
      return `Recovered ${data.recovered_task_count} tasks`;
    case 'ledger_transaction':
      return `${data.amount_clstr} CLSTR: ${data.from_account} → ${data.to_account}`;
    case 'connection_established':
      return 'Connected to real-time events';
    default:
      return `Event: ${event_type}`;
  }
}

export function ActivityFeed({ className }: { className?: string }) {
  const { events, clearEvents } = useEventFeed(30);

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Live Activity</CardTitle>
        {events.length > 0 && (
          <button
            onClick={clearEvents}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Clear
          </button>
        )}
      </CardHeader>
      <CardBody className="p-0">
        {events.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No recent activity</p>
            <p className="text-sm text-gray-400 mt-1">
              Events will appear here in real-time
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
            {events.map((event, index) => {
              const Icon =
                EVENT_ICONS[event.event_type] || Activity;
              const colorClass =
                EVENT_COLORS[event.event_type] ||
                'bg-gray-100 text-gray-700';

              return (
                <div
                  key={`${event.timestamp}-${index}`}
                  className="px-6 py-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${colorClass}`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm text-gray-900 truncate">
                          {getEventMessage(event)}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          className={`${colorClass} text-xs`}
                        >
                          {event.event_type.replace(/_/g, ' ')}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(event.timestamp)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
