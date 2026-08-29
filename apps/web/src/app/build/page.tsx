'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { api, type WorkloadRequirements } from '@/lib/api';
import { formatCLSTR, formatDuration } from '@/lib/utils';
import {
  Zap,
  Clock,
  DollarSign,
  Shield,
  ChevronRight,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

type Step = 'workload' | 'requirements' | 'recommendation' | 'confirm';

export default function BuildCloudPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<Step>('workload');
  const [loading, setLoading] = useState(false);

  // Form state
  const [workloadType, setWorkloadType] = useState('3D Rendering');
  const [totalFrames, setTotalFrames] = useState(100);
  const [deadlineHours, setDeadlineHours] = useState(24);
  const [budget, setBudget] = useState(1000);
  const [reliability, setReliability] = useState(0.9);

  // Recommendation state
  const [recommendation, setRecommendation] = useState<any>(null);

  const handleGetRecommendation = async () => {
    setLoading(true);
    try {
      const requirements: WorkloadRequirements = {
        workload_type: workloadType,
        total_frames: totalFrames,
        deadline_hours: deadlineHours,
        total_budget_clstr: budget,
        min_reliability: reliability,
        requires_gpu: true,
      };

      const rec = await api.getSchedulingRecommendation(requirements);
      setRecommendation(rec);
      setCurrentStep('recommendation');
    } catch (error) {
      console.error('Failed to get recommendation:', error);
      alert('Failed to get recommendation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBuildCloud = async () => {
    setLoading(true);
    try {
      const requirements: WorkloadRequirements = {
        workload_type: workloadType,
        total_frames: totalFrames,
        deadline_hours: deadlineHours,
        total_budget_clstr: budget,
        min_reliability: reliability,
        requires_gpu: true,
      };

      const job = await api.createJob(requirements);
      router.push(`/jobs/${job.job_id}`);
    } catch (error) {
      console.error('Failed to create job:', error);
      alert('Failed to create job. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Build Your Cloud
          </h1>
          <p className="text-gray-600">
            Answer a few questions and we'll build the perfect cloud for you
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-between mb-8">
          {[
            { key: 'workload', label: 'Workload' },
            { key: 'requirements', label: 'Requirements' },
            { key: 'recommendation', label: 'Review' },
          ].map((step, idx) => {
            const isActive = currentStep === step.key;
            const isPast =
              ['workload', 'requirements', 'recommendation'].indexOf(
                currentStep
              ) >
              ['workload', 'requirements', 'recommendation'].indexOf(step.key);

            return (
              <div key={step.key} className="flex items-center flex-1">
                <div className="flex items-center gap-3 flex-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                      isPast
                        ? 'bg-primary-600 text-white'
                        : isActive
                        ? 'bg-primary-100 text-primary-600 ring-4 ring-primary-50'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    {isPast ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  <span
                    className={`font-medium ${
                      isActive ? 'text-gray-900' : 'text-gray-500'
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {idx < 2 && (
                  <ChevronRight className="w-5 h-5 text-gray-300 mx-2" />
                )}
              </div>
            );
          })}
        </div>

        {/* Step: Workload */}
        {currentStep === 'workload' && (
          <Card>
            <CardBody className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  What are you building?
                </h2>
                <p className="text-gray-600">
                  Tell us about your workload so we can optimize for it
                </p>
              </div>

              {/* Workload Type */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  Workload Type
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: '3D Rendering', icon: Sparkles },
                    { value: 'Video Processing', icon: Zap },
                    { value: 'ML Training', icon: Zap },
                    { value: 'Batch Processing', icon: Zap },
                  ].map((option) => {
                    const Icon = option.icon;
                    const isSelected = workloadType === option.value;

                    return (
                      <button
                        key={option.value}
                        onClick={() => setWorkloadType(option.value)}
                        className={`p-4 rounded-lg border-2 text-left transition-all ${
                          isSelected
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <Icon
                          className={`w-5 h-5 mb-2 ${
                            isSelected ? 'text-primary-600' : 'text-gray-400'
                          }`}
                        />
                        <div
                          className={`font-medium ${
                            isSelected ? 'text-primary-900' : 'text-gray-900'
                          }`}
                        >
                          {option.value}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Frames */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  How many frames?
                </label>
                <input
                  type="number"
                  value={totalFrames}
                  onChange={(e) => setTotalFrames(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  min="1"
                  max="10000"
                />
                <p className="text-sm text-gray-500">
                  More frames = more distribution
                </p>
              </div>

              <Button
                onClick={() => setCurrentStep('requirements')}
                size="lg"
                className="w-full gap-2"
              >
                Continue
                <ChevronRight className="w-5 h-5" />
              </Button>
            </CardBody>
          </Card>
        )}

        {/* Step: Requirements */}
        {currentStep === 'requirements' && (
          <Card>
            <CardBody className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Set your constraints
                </h2>
                <p className="text-gray-600">
                  Balance speed, cost, and reliability
                </p>
              </div>

              {/* Deadline */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Clock className="w-4 h-4" />
                  Deadline (hours)
                </label>
                <input
                  type="range"
                  value={deadlineHours}
                  onChange={(e) => setDeadlineHours(Number(e.target.value))}
                  min="1"
                  max="168"
                  className="w-full"
                />
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">1 hour</span>
                  <span className="font-semibold text-primary-600">
                    {formatDuration(deadlineHours)}
                  </span>
                  <span className="text-gray-600">7 days</span>
                </div>
              </div>

              {/* Budget */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <DollarSign className="w-4 h-4" />
                  Maximum Budget (CLSTR)
                </label>
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  min="100"
                  max="100000"
                  step="100"
                />
                <p className="text-sm text-gray-500">
                  {formatCLSTR(budget)} available
                </p>
              </div>

              {/* Reliability */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Shield className="w-4 h-4" />
                  Reliability Requirement
                </label>
                <input
                  type="range"
                  value={reliability}
                  onChange={(e) => setReliability(Number(e.target.value))}
                  min="0.5"
                  max="1.0"
                  step="0.05"
                  className="w-full"
                />
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Basic (50%)</span>
                  <span className="font-semibold text-primary-600">
                    {(reliability * 100).toFixed(0)}%
                  </span>
                  <span className="text-gray-600">Maximum (100%)</span>
                </div>
                <p className="text-sm text-gray-500">
                  Higher reliability = higher cost but fewer failures
                </p>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => setCurrentStep('workload')}
                  variant="outline"
                  size="lg"
                  className="flex-1"
                >
                  Back
                </Button>
                <Button
                  onClick={handleGetRecommendation}
                  size="lg"
                  className="flex-1 gap-2"
                  disabled={loading}
                >
                  {loading ? 'Analyzing...' : 'Get Recommendation'}
                  <Sparkles className="w-5 h-5" />
                </Button>
              </div>
            </CardBody>
          </Card>
        )}

        {/* Step: Recommendation */}
        {currentStep === 'recommendation' && recommendation && (
          <div className="space-y-6">
            <Card className="border-2 border-primary-200 bg-primary-50">
              <CardBody className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      AI Recommendation
                    </h3>
                    <p className="text-gray-700 leading-relaxed">
                      {recommendation.reasoning}
                    </p>
                  </div>
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardBody className="space-y-6">
                <div>
                  <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                    Your Cloud Configuration
                  </h2>

                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <div className="text-sm text-gray-600 mb-1">
                        Workload
                      </div>
                      <div className="font-semibold text-gray-900">
                        {workloadType}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-1">Frames</div>
                      <div className="font-semibold text-gray-900">
                        {totalFrames}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-1">
                        Selected Nodes
                      </div>
                      <div className="font-semibold text-gray-900">
                        {recommendation.recommended_nodes.length} nodes
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-1">
                        Estimated Time
                      </div>
                      <div className="font-semibold text-gray-900">
                        {formatDuration(
                          recommendation.estimated_completion_hours
                        )}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-1">
                        Total Cost
                      </div>
                      <div className="font-semibold text-primary-600">
                        {formatCLSTR(recommendation.total_cost_clstr)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600 mb-1">
                        Confidence
                      </div>
                      <div className="font-semibold text-green-600">
                        {(recommendation.confidence_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border-t pt-6">
                  <div className="flex gap-3">
                    <Button
                      onClick={() => setCurrentStep('requirements')}
                      variant="outline"
                      size="lg"
                      className="flex-1"
                    >
                      Adjust Settings
                    </Button>
                    <Button
                      onClick={handleBuildCloud}
                      size="lg"
                      className="flex-1 gap-2"
                      disabled={loading}
                    >
                      {loading ? (
                        'Building...'
                      ) : (
                        <>
                          <Zap className="w-5 h-5" />
                          Build My Cloud
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
