/**
 * ClusterCloud API Client
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Node {
  node_id: string;
  name: string;
  ip_address: string;
  status: string;
  cpu_cores: number;
  cpu_model: string;
  total_ram_gb: number;
  available_ram_gb: number;
  gpu_info: string | null;
  reliability_score: number;
  cost_per_hour_clstr: number;
  last_heartbeat: string;
}

export interface Job {
  job_id: string;
  customer_id: string;
  workload_type: string;
  status: string;
  total_frames: number;
  completed_frames: number;
  failed_frames: number;
  total_budget_clstr: number;
  deadline: string | null;
  min_reliability: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  task_id: string;
  job_id: string;
  frame_number: number;
  status: string;
  assigned_node_id: string | null;
  cost_clstr: number;
  retry_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface Incident {
  incident_id: string;
  incident_type: string;
  severity: string;
  status: string;
  related_job_id: string | null;
  related_node_id: string | null;
  affected_task_ids: string[];
  detected_at: string;
  resolved_at: string | null;
  recovery_actions: any[];
}

export interface Transaction {
  transaction_id: string;
  timestamp: string;
  transaction_type: string;
  from_account: string;
  to_account: string;
  amount_clstr: number;
  description: string | null;
  related_job_id: string | null;
}

export interface WorkloadRequirements {
  workload_type: string;
  total_frames: number;
  deadline_hours?: number;
  total_budget_clstr: number;
  min_reliability: number;
  min_cpu_cores?: number;
  min_ram_gb?: number;
  requires_gpu?: boolean;
}

export interface SchedulingRecommendation {
  recommended_nodes: string[];
  estimated_completion_hours: number;
  total_cost_clstr: number;
  confidence_score: number;
  reasoning: string;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  // Nodes
  async getNodes(): Promise<Node[]> {
    return this.request<Node[]>('/api/nodes');
  }

  async getNode(nodeId: string): Promise<Node> {
    return this.request<Node>(`/api/nodes/${nodeId}`);
  }

  // Jobs
  async getJobs(): Promise<Job[]> {
    return this.request<Job[]>('/api/jobs');
  }

  async getJob(jobId: string): Promise<Job> {
    return this.request<Job>(`/api/jobs/${jobId}`);
  }

  async createJob(requirements: WorkloadRequirements): Promise<Job> {
    return this.request<Job>('/api/jobs', {
      method: 'POST',
      body: JSON.stringify(requirements),
    });
  }

  // Tasks
  async getJobTasks(jobId: string): Promise<Task[]> {
    return this.request<Task[]>(`/api/jobs/${jobId}/tasks`);
  }

  // Incidents
  async getIncidents(): Promise<Incident[]> {
    return this.request<Incident[]>('/api/incidents');
  }

  async getJobIncidents(jobId: string): Promise<Incident[]> {
    return this.request<Incident[]>(`/api/incidents?job_id=${jobId}`);
  }

  // Economics
  async getBalance(account: string): Promise<{ balance: number }> {
    return this.request<{ balance: number }>(`/api/ledger/balance/${account}`);
  }

  async getTransactions(account?: string): Promise<Transaction[]> {
    const query = account ? `?account=${account}` : '';
    return this.request<Transaction[]>(`/api/ledger/transactions${query}`);
  }

  // AI Recommendations
  async getSchedulingRecommendation(
    requirements: WorkloadRequirements
  ): Promise<SchedulingRecommendation> {
    return this.request<SchedulingRecommendation>('/api/scheduling/recommend', {
      method: 'POST',
      body: JSON.stringify(requirements),
    });
  }

  // System Stats
  async getSystemStats(): Promise<{
    total_nodes: number;
    healthy_nodes: number;
    total_jobs: number;
    active_jobs: number;
    total_tasks_completed: number;
    total_clstr_transacted: number;
  }> {
    return this.request('/api/stats');
  }
}

export const api = new APIClient();
