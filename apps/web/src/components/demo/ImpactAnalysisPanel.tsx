'use client';

import { useEffect, useState } from 'react';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  AlertTriangle,
  Clock,
  Activity,
  TrendingUp,
  ArrowRight,
  Zap,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

interface ImpactAnalysisData {
  node_id: string;
  cascade_impact: {
    affected_node: {
      node_id: string;
      name: string;
      status: string;
    };
    affected_tasks: Array<{
      task_id: string;
      job_id: string;
      estimated_completion_minutes: number;
    }>;
    affected_jobs: Array<{
      job_id: string;
      customer_id: string;
      affected_tasks_count: number;
    }>;
    estimated_delay_minutes: number;
    deadline_risks: Array<{
      job_id: string;
      risk_level: string;
      slack_minutes: number;
    }>;
    cascade_chain: Array<{
      step: string;
      description: string;
      timestamp: string;
    }>;
  };
  scenarios: {
    scenarios: {
      do_nothing: {
        scenario: string;
        estimated_completion_minutes: number;
        affected_tasks_count: number;
        deadline_breaches: number;
        estimated_cost_clstr: number;
        timeline: Array<{
          time_minutes: number;
          event: string;
          description: string;
        }>;
      };
      recover_now: {
        scenario: string;
        estimated_completion_minutes: number;
        affected_tasks_count: number;
        deadline_breaches: number;
        estimated_cost_clstr: number;
        timeline: Array<{
          time_minutes: number;
          event: string;
          description: string;
        }>;
      };
    };
    comparison: {
      time_saved_minutes: number;
      deadline_delta: number;
      cost_delta_clstr: number;
      recommended_action: string;
    };
    recommendation: {
      action: string;
      reason: string;
      confidence: string;
    };
  };
  decision_window: {
    decision_window_seconds: number;
    urgency_level: string;
    urgency_reason: string;
    recommendation: string;
    after_window_impact: {
      expected_impact: string;
      description: string;
    };
  };
  ai_explanation?: string;
}

interface Props {
  nodeId: string;
  incidentId?: string;
  onExecuteRecovery?: () => void;
}

export function ImpactAnalysisPanel({ nodeId, incidentId, onExecuteRecovery }: Props) {
  const [data, setData] = useState<ImpactAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);

  useEffect(() => {
    loadAnalysis();
  }, [nodeId, incidentId]);

  useEffect(() => {
    if (data?.decision_window) {
      setCountdown(data.decision_window.decision_window_seconds);
    }
  }, [data]);

  useEffect(() => {
    if (countdown === null || countdown <= 0) return;

    const timer = setInterval(() => {
      setCountdown(prev => (prev! > 0 ? prev! - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const url = incidentId
        ? `/api/impact/incident/${incidentId}/analysis`
        : `/api/impact/node-failure/${nodeId}/analysis`;
      
      const response = await fetch(url);
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('Failed to load impact analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeRecovery = async () => {
    if (!incidentId) return;

    try {
      setExecuting(true);
      const response = await fetch(`/api/impact/incident/${incidentId}/execute-recovery`, {
        method: 'POST',
      });

      if (response.ok) {
        if (onExecuteRecovery) {
          onExecuteRecovery();
        }
      }
    } catch (error) {
      console.error('Failed to execute recovery:', error);
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <Card className="border-2 border-orange-300">
        <CardBody className="text-center py-12">
          <Activity className="w-12 h-12 text-orange-600 animate-spin mx-auto mb-4" />
          <p className="text-orange-900 font-medium">
            Analyzing impact...
          </p>
        </CardBody>
      </Card>
    );
  }

  if (!data || !data.cascade_impact.affected_tasks.length) {
    return (
      <Card>
        <CardBody className="text-center py-8">
          <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto mb-3" />
          <p className="text-gray-600">No active impact</p>
        </CardBody>
      </Card>
    );
  }

  const { cascade_impact, scenarios, decision_window, ai_explanation } = data;
  const doNothing = scenarios.scenarios.do_nothing;
  const recoverNow = scenarios.scenarios.recover_now;

  const urgencyColor = 
    decision_window.urgency_level === 'CRITICAL' ? 'red' :
    decision_window.urgency_level === 'HIGH' ? 'orange' :
    decision_window.urgency_level === 'MEDIUM' ? 'yellow' : 'blue';

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      {}
      <Card className={`border-2 border-${urgencyColor}-300 shadow-lg`}>
        <CardHeader className={`bg-gradient-to-r from-${urgencyColor}-50 to-${urgencyColor}-100 border-b`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 bg-${urgencyColor}-600 rounded-full flex items-center justify-center`}>
                <AlertTriangle className="w-6 h-6 text-white" />
              </div>
              <div>
                <CardTitle className={`text-${urgencyColor}-900`}>
                  CRITICAL INCIDENT
                </CardTitle>
                <p className={`text-sm text-${urgencyColor}-700 font-medium`}>
                  {cascade_impact.affected_node.name} OFFLINE
                </p>
              </div>
            </div>
            <Badge className={`bg-${urgencyColor}-600 text-white text-lg px-4 py-2`}>
              {decision_window.urgency_level}
            </Badge>
          </div>
        </CardHeader>

        <CardBody className="space-y-6">
          {}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              CURRENT IMPACT
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-3 border">
                <div className="text-2xl font-bold text-gray-900">
                  {cascade_impact.affected_tasks.length}
                </div>
                <div className="text-sm text-gray-600">tasks</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 border">
                <div className="text-2xl font-bold text-gray-900">
                  {cascade_impact.affected_jobs.length}
                </div>
                <div className="text-sm text-gray-600">jobs</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 border">
                <div className="text-2xl font-bold text-gray-900">
                  {Math.round(cascade_impact.estimated_delay_minutes)}m
                </div>
                <div className="text-sm text-gray-600">estimated delay</div>
              </div>
            </div>
          </div>

          {}
          <div className={`bg-${urgencyColor}-50 border-2 border-${urgencyColor}-300 rounded-lg p-4`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Clock className={`w-6 h-6 text-${urgencyColor}-600`} />
                <div>
                  <h4 className={`font-semibold text-${urgencyColor}-900`}>
                    DECISION WINDOW
                  </h4>
                  <p className={`text-sm text-${urgencyColor}-700`}>
                    {decision_window.urgency_reason}
                  </p>
                </div>
              </div>
              <div className={`text-4xl font-bold text-${urgencyColor}-600`}>
                {countdown !== null ? formatTime(countdown) : '--:--'}
              </div>
            </div>
            {countdown !== null && countdown <= 10 && (
              <div className={`mt-3 text-sm text-${urgencyColor}-800 font-medium animate-pulse`}>
                ⚠️ {decision_window.after_window_impact.description}
              </div>
            )}
          </div>

          {}
          <div className="border-t pt-4">
            <h3 className="font-semibold text-gray-900 mb-4">
              IMPACT PROJECTION
            </h3>

            <div className="grid grid-cols-2 gap-6">
              {}
              <div>
                <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <XCircle className="w-4 h-4 text-red-500" />
                  WHAT IF WE DO NOTHING?
                </h4>
                <div className="space-y-2">
                  {doNothing.timeline.slice(0, 4).map((event, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <span className="text-gray-500 font-mono w-12">
                        T+{event.time_minutes}m
                      </span>
                      <span className="text-gray-700">{event.description}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-4 bg-red-50 border border-red-200 rounded p-3">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <div className="text-gray-600">Delay</div>
                      <div className="font-bold text-red-700">
                        {Math.round(doNothing.estimated_completion_minutes)}m
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Breaches</div>
                      <div className="font-bold text-red-700">
                        {doNothing.deadline_breaches}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {}
              <div>
                <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  WHAT IF WE RECOVER NOW?
                </h4>
                <div className="space-y-2">
                  {recoverNow.timeline.slice(0, 4).map((event, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <span className="text-gray-500 font-mono w-12">
                        T+{event.time_minutes}m
                      </span>
                      <span className="text-gray-700">{event.description}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-4 bg-green-50 border border-green-200 rounded p-3">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <div className="text-gray-600">Delay</div>
                      <div className="font-bold text-green-700">
                        {Math.round(recoverNow.estimated_completion_minutes)}m
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Breaches</div>
                      <div className="font-bold text-green-700">
                        {recoverNow.deadline_breaches}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {}
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                RECOVERY IMPACT
              </h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-xs text-blue-600 mb-1">Time Saved</div>
                  <div className="text-2xl font-bold text-blue-700">
                    {Math.round(scenarios.comparison.time_saved_minutes)}m
                  </div>
                </div>
                <div>
                  <div className="text-xs text-blue-600 mb-1">Breaches Prevented</div>
                  <div className="text-2xl font-bold text-blue-700">
                    {scenarios.comparison.deadline_delta}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-blue-600 mb-1">Cost Savings</div>
                  <div className="text-2xl font-bold text-blue-700">
                    {Math.round(scenarios.comparison.cost_delta_clstr)} CLSTR
                  </div>
                </div>
              </div>
            </div>
          </div>

          {}
          {ai_explanation && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-purple-900 mb-2">
                    AI RECOMMENDATION
                  </h4>
                  <p className="text-sm text-purple-800 leading-relaxed mb-3">
                    {ai_explanation}
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-purple-600 text-white">
                      {scenarios.recommendation.confidence} CONFIDENCE
                    </Badge>
                    <span className="text-sm text-purple-700">
                      {scenarios.recommendation.reason}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {}
          <div className="pt-4 border-t">
            <Button
              onClick={executeRecovery}
              disabled={executing}
              className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white text-lg py-4"
            >
              {executing ? (
                <>
                  <Activity className="w-5 h-5 animate-spin mr-2" />
                  Executing Recovery...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-5 h-5 mr-2" />
                  EXECUTE RECOVERY
                </>
              )}
            </Button>
            <p className="text-xs text-center text-gray-500 mt-2">
              Calls existing RecoveryService to reassign tasks
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
