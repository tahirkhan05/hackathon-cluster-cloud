'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';

interface Node {
  node_id: string;
  provider_id: string;
  status: string;
  capabilities: {
    cpu_cores: number;
    ram_gb: number;
    gpu_count: number;
    storage_gb: number;
  };
  last_heartbeat: string;
}

export default function NetworkPage() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNodes();
    const interval = setInterval(fetchNodes, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchNodes = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/nodes');
      const data = await res.json();
      setNodes(data.nodes || []);
    } catch (error) {
      console.error('Failed to fetch nodes:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'text-emerald-400';
      case 'busy': return 'text-amber-400';
      case 'offline': return 'text-slate-500';
      default: return 'text-slate-400';
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Network Nodes</h1>
          <p className="text-slate-400 mt-1">Connected compute resources</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Total Nodes</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {nodes.length}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Available</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {nodes.filter(n => n.status === 'available').length}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Busy</div>
            <div className="text-2xl font-bold text-amber-400 mt-1">
              {nodes.filter(n => n.status === 'busy').length}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Offline</div>
            <div className="text-2xl font-bold text-slate-500 mt-1">
              {nodes.filter(n => n.status === 'offline').length}
            </div>
          </div>
        </div>

        {/* Nodes List */}
        <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
          <div className="p-4 border-b border-slate-700/50">
            <h2 className="text-lg font-semibold text-slate-100">Active Nodes</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center text-slate-400">Loading nodes...</div>
          ) : nodes.length === 0 ? (
            <div className="p-8 text-center text-slate-400">No nodes registered</div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {nodes.map((node) => (
                <div key={node.node_id} className="p-4 hover:bg-slate-700/30 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className={`text-sm font-medium ${getStatusColor(node.status)}`}>
                          {node.status.toUpperCase()}
                        </span>
                        <span className="text-slate-100 font-medium">{node.provider_id}</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-1 font-mono">
                        {node.node_id}
                      </div>
                    </div>
                    
                    <div className="flex gap-6 text-sm">
                      <div>
                        <div className="text-slate-400">CPU</div>
                        <div className="text-slate-100 font-medium">
                          {node.capabilities?.cpu_cores || 0} cores
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400">RAM</div>
                        <div className="text-slate-100 font-medium">
                          {node.capabilities?.ram_gb?.toFixed(1) || 0} GB
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400">GPU</div>
                        <div className="text-slate-100 font-medium">
                          {node.capabilities?.gpu_count || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400">Storage</div>
                        <div className="text-slate-100 font-medium">
                          {node.capabilities?.storage_gb?.toFixed(0) || 0} GB
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
