# ClusterCloud Architecture

## System Overview

ClusterCloud is a **modular monolith control plane** with distributed worker nodes.

### Key Design Principles

1. **Separation of AI and deterministic logic**
   - AI provides recommendations and explanations
   - Deterministic code makes final decisions
   - All AI suggestions validated by business rules

2. **Clear state machines**
   - Jobs: pending → analyzing → scheduled → executing → completed/failed
   - Tasks: queued → assigned → running → completed/failed
   - Nodes: registering → available → busy → offline

3. **Idempotent operations**
   - Task assignments can be retried safely
   - Ledger transactions are unique per event
   - Recovery operations don't duplicate work

4. **Event-driven coordination**
   - Heartbeat monitoring detects failures
   - WebSocket broadcasts real-time updates
   - Audit log captures all state changes

## Core Domains

### Workloads
Defines supported workload types and their characteristics.

**MVP**: Frame rendering (parallelizable, stateless, GPU-preferred)

**Schema**:
- workload_type: string
- parallelizable: boolean
- resource_requirements: dict
- estimated_task_duration: seconds

### Jobs
Customer-submitted work requests.

**Lifecycle**: submitted → analyzed → scheduled → executing → completed/failed

**Schema**:
- job_id: uuid
- customer_id: uuid
- workload_type: string
- parameters: json (frame_count, resolution, etc.)
- status: enum
- created_at, started_at, completed_at: timestamp
- total_cost_clstr: decimal

### Tasks
Individual units of work distributed to nodes.

**Schema**:
- task_id: uuid
- job_id: uuid (foreign key)
- node_id: uuid (nullable)
- task_number: int
- parameters: json (frame_range, input_urls, etc.)
- status: enum (queued, assigned, running, completed, failed)
- retry_count: int
- assigned_at, started_at, completed_at: timestamp
- result_url: string

### Nodes
Provider machines registered with the control plane.

**Schema**:
- node_id: uuid
- provider_id: uuid
- capabilities: json (cpu_cores, ram_gb, gpu_model, etc.)
- status: enum (available, busy, offline)
- last_heartbeat: timestamp
- reliability_score: float (0.0 - 1.0)
- total_tasks_completed: int
- total_tasks_failed: int
- clstr_earned: decimal
- clstr_staked: decimal

### Scheduling
Task-to-node assignment logic.

**Algorithm**:
1. Filter nodes by capability requirements
2. Filter by current availability
3. Sort by reliability score (descending)
4. Sort by cost (ascending) as tiebreaker
5. Assign tasks round-robin among top candidates
6. Record assignments in database

### Execution
Orchestrates task lifecycle and monitoring.

**Responsibilities**:
- Track task state transitions
- Monitor node heartbeats
- Detect timeouts
- Trigger recovery on failure
- Update job progress
- Broadcast real-time events

### Incidents
Records and manages failure events.

**Schema**:
- incident_id: uuid
- job_id: uuid
- task_id: uuid
- node_id: uuid
- incident_type: enum (heartbeat_timeout, task_timeout, node_crash, etc.)
- detected_at: timestamp
- resolved_at: timestamp
- recovery_node_id: uuid (nullable)
- status: enum (detected, recovering, resolved, unresolved)

### Reliability
Tracks provider reputation and history.

**Metrics**:
- Success rate (completed / total)
- Average task duration
- Failure incidents
- Recovery contributions
- Stake at risk

**Score Calculation**:
```
reliability_score = (completed_tasks * 1.0 + recovery_assists * 0.5) / 
                    (total_tasks + failed_tasks * 2.0)
```

Clamped to [0.0, 1.0]

### Ledger
CLSTR token accounting.

**Transaction Types**:
- `job_created`: Customer pre-payment
- `task_completed`: Provider earnings
- `broker_fee`: Platform cut
- `stake_held`: Provider deposit
- `stake_returned`: Successful task completion
- `penalty_applied`: Node failure
- `compensation_issued`: Customer refund
- `recovery_reward`: Replacement node bonus

**Schema**:
- transaction_id: uuid
- timestamp: timestamp
- transaction_type: enum
- from_account: uuid
- to_account: uuid
- amount_clstr: decimal
- related_job_id: uuid (nullable)
- related_task_id: uuid (nullable)
- related_incident_id: uuid (nullable)
- description: string

### AI Orchestration
Integrates AWS Bedrock for intelligent decisions.

**Use Cases**:
1. **Workload Analysis**
   - Input: Job parameters, workload type
   - Output: Parallelizability assessment, recommended resources, estimated duration
   - Validation: Must match registered workload type capabilities

2. **Resource Planning**
   - Input: Task requirements, available nodes
   - Output: Recommended node selection with reasoning
   - Validation: Selected nodes must meet hard constraints

3. **Recovery Recommendations**
   - Input: Incident details, incomplete tasks, available nodes
   - Output: Recommended recovery strategy and replacement nodes
   - Validation: Must have capacity and meet requirements

4. **Human-Readable Explanations**
   - Input: Any system decision
   - Output: Plain English explanation for dashboard
   - Validation: None (informational only)

## Data Flow

### Job Submission Flow
```
Customer → API → Workload Analyzer (AI) → Scheduler → Database
                      ↓
                 Validation & Business Rules
```

### Task Execution Flow
```
Scheduler → Task Assignment → Node Agent → Docker Container → Result Upload
              ↓                    ↓
         Update DB          Heartbeat Monitor
```

### Failure Recovery Flow
```
Heartbeat Monitor → Incident Created → Recovery Agent (AI) → Scheduler → Reassignment
                         ↓                    ↓
                   Update Reliability    Ledger Transactions
```

## Communication Patterns

### Control Plane ↔ Node Agent
- **Registration**: POST /api/nodes/register
- **Heartbeat**: POST /api/nodes/{node_id}/heartbeat (every 5s)
- **Task Assignment**: GET /api/tasks/next?node_id={node_id}
- **Task Update**: POST /api/tasks/{task_id}/status
- **Result Submission**: POST /api/tasks/{task_id}/result

### Control Plane → Frontend
- **REST API**: Job CRUD, node status, ledger queries
- **WebSocket**: Real-time job progress, incidents, recovery events

## Security Boundaries

### Node Agent Authentication
- API key in request header: `X-Node-Agent-Key`
- Node ID tied to agent key
- Rate limiting on registration endpoints

### Workload Isolation
- Each task runs in ephemeral Docker container
- Resource limits: CPU, memory, disk, network
- No host filesystem access
- Restricted network (only output upload endpoint)
- Non-root execution

### Customer Isolation
- Customer accounts separate from provider accounts
- Jobs scoped to customer_id
- API authentication required for all operations

## Scalability Considerations (Future)

This MVP runs locally. For production:

1. **Database**: Connection pooling, read replicas
2. **Task Queue**: Redis/RabbitMQ for async processing
3. **File Storage**: S3 for results and inputs
4. **Monitoring**: Prometheus, Grafana
5. **Load Balancing**: Multiple API instances
6. **Geographic Distribution**: Regional control planes

## Non-Goals for MVP

- Multi-tenancy with strong isolation
- Byzantine fault tolerance
- Distributed consensus
- Production-grade security
- Real monetary transactions
- Advanced scheduling algorithms (bin packing, etc.)
- Dynamic pricing
- Reputation staking smart contracts
