'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';

interface Incident {
  incident_id: string;
  node_id: string;
  incident_type: string;
  severity: string;
  status: string;
  detected_at: string;
  resolved_at?: string;
  description: string;
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchIncidents = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/incidents');
      const data = await res.json();
      setIncidents(data.incidents || []);
    } catch (error) {
      console.error('Failed to fetch incidents:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30';
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
      case 'low': return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'text-red-400';
      case 'acknowledged': return 'text-yellow-400';
      case 'resolved': return 'text-emerald-400';
      default: return 'text-slate-400';
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Incidents</h1>
          <p className="text-slate-400 mt-1">System failures and anomalies</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Total</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {incidents.length}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Open</div>
            <div className="text-2xl font-bold text-red-400 mt-1">
              {incidents.filter(i => i.status === 'open').length}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Acknowledged</div>
            <div className="text-2xl font-bold text-yellow-400 mt-1">
              {incidents.filter(i => i.status === 'acknowledged').length}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Resolved</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {incidents.filter(i => i.status === 'resolved').length}
            </div>
          </div>
        </div>

        {/* Incidents List */}
        <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
          <div className="p-4 border-b border-slate-700/50">
            <h2 className="text-lg font-semibold text-slate-100">Recent Incidents</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center text-slate-400">Loading incidents...</div>
          ) : incidents.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-emerald-400 text-5xl mb-2">✓</div>
              <div className="text-slate-400">No incidents reported</div>
              <div className="text-slate-500 text-sm mt-1">System is healthy</div>
            </div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {incidents.map((incident) => (
                <div key={incident.incident_id} className="p-4 hover:bg-slate-700/30 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getSeverityColor(incident.severity)}`}>
                          {incident.severity.toUpperCase()}
                        </span>
                        <span className={`text-sm font-medium ${getStatusColor(incident.status)}`}>
                          {incident.status.toUpperCase()}
                        </span>
                        <span className="text-slate-500 text-sm">
                          {incident.incident_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="text-slate-100">
                        {incident.description}
                      </div>
                      <div className="text-xs text-slate-500 mt-2 font-mono">
                        Node: {incident.node_id}
                      </div>
                    </div>
                    <div className="text-right text-sm text-slate-400">
                      <div>{new Date(incident.detected_at).toLocaleString()}</div>
                      {incident.resolved_at && (
                        <div className="text-emerald-400 mt-1">
                          Resolved {new Date(incident.resolved_at).toLocaleString()}
                        </div>
                      )}
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
