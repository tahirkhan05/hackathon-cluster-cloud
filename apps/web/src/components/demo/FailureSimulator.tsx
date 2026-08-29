'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardBody } from '@/components/ui/Card';
import { api } from '@/lib/api';
import { AlertTriangle, Zap, CheckCircle2 } from 'lucide-react';

interface Props {
  nodeId?: string;
  onFailureTriggered?: () => void;
  disabled?: boolean;
}

export function FailureSimulator({ nodeId, onFailureTriggered, disabled }: Props) {
  const [triggering, setTriggering] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleTriggerFailure = async () => {
    if (!nodeId) {
      alert('No node selected. Please wait for nodes to be available.');
      return;
    }

    const confirm = window.confirm(
      `⚠️ DEMO MODE\n\nThis will simulate a failure of node ${nodeId.slice(
        0,
        8
      )}...\n\nThis will:\n- Mark the node as UNHEALTHY\n- Trigger failure detection\n- Start automatic recovery\n- Show economic settlement\n\nContinue?`
    );

    if (!confirm) return;

    setTriggering(true);
    setSuccess(false);

    try {
      await fetch(`/api/demo/simulate-failure/${nodeId}`, {
        method: 'POST',
      });

      setSuccess(true);
      
      if (onFailureTriggered) {
        onFailureTriggered();
      }

      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (error) {
      console.error('Failed to trigger failure:', error);
      alert('Failed to trigger failure. Check console for details.');
    } finally {
      setTriggering(false);
    }
  };

  return (
    <Card className="border-2 border-orange-300 bg-gradient-to-br from-orange-50 to-red-50">
      <CardBody>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center flex-shrink-0">
            {success ? (
              <CheckCircle2 className="w-6 h-6 text-white" />
            ) : (
              <AlertTriangle className="w-6 h-6 text-white" />
            )}
          </div>

          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 mb-1">
              Failure Simulation
            </h3>
            <p className="text-sm text-gray-600">
              Demonstrate automatic recovery and economic settlement
            </p>
          </div>

          <Button
            onClick={handleTriggerFailure}
            disabled={disabled || triggering || !nodeId}
            variant="secondary"
            size="lg"
            className="gap-2 bg-orange-600 hover:bg-orange-700 text-white"
          >
            {triggering ? (
              <>
                <Zap className="w-5 h-5 animate-pulse" />
                Triggering...
              </>
            ) : success ? (
              <>
                <CheckCircle2 className="w-5 h-5" />
                Triggered!
              </>
            ) : (
              <>
                <AlertTriangle className="w-5 h-5" />
                Simulate Node Failure
              </>
            )}
          </Button>
        </div>

        {!nodeId && (
          <div className="mt-3 text-sm text-orange-700 bg-orange-100 rounded-lg p-3">
            ⏳ Waiting for nodes to register...
          </div>
        )}
      </CardBody>
    </Card>
  );
}
