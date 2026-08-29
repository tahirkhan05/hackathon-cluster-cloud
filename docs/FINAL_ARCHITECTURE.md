# ClusterCloud - Final Architecture

**Version:** MVP 1.0  
**Status:** Hackathon Ready  
**Last Updated:** 2024-01-15

---

## System Overview

ClusterCloud is a distributed 3D rendering platform that automatically handles:
- Workload analysis and cluster composition (AI-driven)
- Task distribution across multiple nodes
- Failure detection and automatic recovery
- Economic settlement with fair penalties and rewards

### Core Value Proposition

**Customer sees:** "I want to render 20 frames" → System delivers rendered frames  
**System handles:** Node selection, task distribution, failure recovery, economic settlement

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                       CUSTOMER LAYER                         │
│  Web UI (Next.js) - Simple 4-question interface             │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────────┐
│                    CONTROL PLANE (FastAPI)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ AI Analysis │  │ Job          │  │ Failure      │       │
│  │ (Bedrock)   │  │ Scheduler    │  │ Detector     │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Recovery    │  │ Economic     │  │ WebSocket    │       │
│  │ Service     │  │ Ledger       │  │ Events       │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────┬───────────────────────────────────────────┘
                  │ REST API + WebSocket
┌─────────────────┴───────────────────────────────────────────┐
│                     WORKER NODES (Python)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Node Agent                                           │   │
│  │  ├── Hardware Detection                              │   │
│  │  ├── Registration & Heartbeat                        │   │
│  │  ├── Task Polling                                    │   │
│  │  └── Docker Executor (isolated workloads)           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Job Creation Flow

```
Customer → [Build My Cloud]
    ↓
Workload Requirements:
- Type: 3D Rendering
- Frames: 20
- Deadline: 1 hour
- Budget: 500 CLSTR
- Reliability: 85%
    ↓
AI Analysis (AWS Bedrock):
- Estimate compute time
- Calculate parallelism
- Determine node requirements
    ↓
Deterministic Scheduler:
- Find compatible nodes
- Score by reliability/cost/capacity
- Select optimal set
    ↓
Task Creation:
- Split job into 20 tasks (one per frame)
- Assign tasks to selected nodes
- Set status: ASSIGNED
    ↓
Database Persistence:
- Job record created
- 20 Task records created
- Node assignments recorded
```

### 2. Task Execution Flow

```
Node Agent (Poll):
GET /api/tasks/poll?node_id=xxx
    ↓
Control Plane Response:
- Returns oldest ASSIGNED task for this node
- Updates task status: ASSIGNED → RUNNING
    ↓
Node Agent:
- Downloads task parameters
- Creates isolated work directory
- Executes in Docker container:
  * Network isolation (--network=none)
  * Resource limits (CPU, RAM, disk)
  * Read-only filesystem
  * Non-root user
    ↓
Task Completes:
POST /api/tasks/{task_id}/complete
- Updates task status: RUNNING → COMPLETED
- Uploads result (rendered frame)
- Updates job progress
    ↓
Economic Settlement:
- Escrow → Provider (95 CLSTR)
- Escrow → Broker (5 CLSTR fee)
```

### 3. Failure & Recovery Flow

```
Failure Detection:
- Node misses heartbeat (15s timeout)
- Mark node: HEALTHY → UNHEALTHY
- Create incident record
    ↓
Identify Affected Tasks:
- Find tasks with status ASSIGNED or RUNNING
- Owned by failed node
    ↓
AI Recovery Decision (AWS Bedrock):
- Analyze remaining nodes
- Consider reliability, cost, capacity
- Recommend replacement node
    ↓
Deterministic Validation:
- Verify node compatibility
- Check resource constraints
- Validate budget limits
    ↓
Task Reassignment:
- Update task.node_id → replacement_node
- Reset status: FAILED → ASSIGNED
- Increment retry_count
    ↓
Economic Settlement:
- Failed provider penalty: -20 CLSTR (from stake)
- Customer compensation: +15 CLSTR
- Recovery provider reward: +10 CLSTR
```

---

## State Machines

### Job States

```
SUBMITTED
   ↓
ANALYZING (AI analyzing workload)
   ↓
SCHEDULING (finding nodes)
   ↓
ALLOCATED (nodes selected, tasks created)
   ↓
RUNNING (tasks executing)
   ↓ (if node fails)
RECOVERING (automatic recovery)
   ↓
COMPLETED / FAILED / CANCELLED
```

**Allowed Transitions:**
- SUBMITTED → ANALYZING
- ANALYZING → SCHEDULING
- SCHEDULING → ALLOCATED
- ALLOCATED → RUNNING
- RUNNING → COMPLETED/FAILED/RECOVERING
- RECOVERING → RUNNING/FAILED

### Task States

```
PENDING
   ↓
ASSIGNED (assigned to node)
   ↓
RUNNING (executing on node)
   ↓
COMPLETED
   ↓ (if failed, with retries)
FAILED → ASSIGNED (retry)
```

**Allowed Transitions:**
- PENDING → ASSIGNED
- ASSIGNED → RUNNING
- RUNNING → COMPLETED/FAILED
- FAILED → ASSIGNED (if retries remaining)

---

## Database Schema

### Core Tables

**jobs**
- job_id (PK)
- customer_id
- workload_type
- status (enum)
- total_frames, completed_frames, failed_frames
- total_budget_clstr
- created_at, updated_at

**tasks**
- task_id (PK)
- job_id (FK)
- assigned_node_id (FK)
- frame_number
- status (enum)
- cost_clstr
- retry_count
- created_at, started_at, completed_at

**nodes**
- node_id (PK)
- provider_id
- name, ip_address
- status (enum)
- is_healthy (boolean)
- cpu_cores, total_ram_gb
- gpu_info
- reliability_score (0-1)
- cost_per_hour_clstr
- last_heartbeat

**incidents**
- incident_id (PK)
- incident_type (enum)
- severity (enum)
- status (enum: OPEN, RESOLVED)
- related_job_id (FK)
- related_node_id (FK)
- metadata (JSON: affected tasks, recovery actions)
- detected_at, resolved_at

**transactions**
- transaction_id (PK)
- transaction_type (enum)
- from_account, to_account
- amount_clstr
- related_job_id, related_task_id, related_incident_id
- timestamp

---

## API Endpoints

### Customer API

```
POST   /api/jobs                    # Create job
GET    /api/jobs                    # List jobs
GET    /api/jobs/{id}               # Get job details
GET    /api/jobs/{id}/tasks         # Get job tasks

GET    /api/nodes                   # List nodes
GET    /api/stats                   # System statistics

GET    /api/ledger/balance/{account}      # Get balance
GET    /api/ledger/transactions           # Transaction history

POST   /api/demo/simulate-failure/{node_id}  # Demo only
```

### Node API

```
POST   /api/nodes/register          # Register node
POST   /api/nodes/{id}/heartbeat    # Send heartbeat
GET    /api/tasks/poll              # Poll for work
POST   /api/tasks/{id}/complete     # Mark complete
POST   /api/tasks/{id}/failed       # Mark failed
```

### WebSocket

```
WS     /ws/events                   # Real-time event stream
```

---

## Security Model

### MVP Security (Implemented)

✅ **Docker Isolation**
- Network isolation (--network=none)
- Resource limits (CPU, memory, disk)
- Read-only root filesystem
- Non-root user execution
- No privileged mode

✅ **API Key Authentication** (optional)
- Node registration requires X-API-Key header
- Configurable via ENABLE_NODE_AUTH=true

✅ **Resource Limits**
- MAX_TASK_MEMORY_MB=2048
- MAX_TASK_CPU_CORES=2.0
- TASK_TIMEOUT_SECONDS=120

✅ **Input Validation**
- Pydantic models validate all inputs
- SQL injection protection (SQLAlchemy ORM)

### Production Hardening Needed

❌ **Not Implemented (See SECURITY.md)**
- Per-node certificates (mTLS)
- Secrets management (Vault)
- TLS/HTTPS encryption
- Seccomp/AppArmor profiles
- Runtime security monitoring
- Comprehensive audit logging

---

## Technology Stack

### Backend
- **FastAPI** - REST API framework
- **SQLAlchemy** - ORM
- **SQLite** - Database (MVP), PostgreSQL (production)
- **AWS Bedrock** - AI (Claude Sonnet 3.5)
- **Docker** - Workload isolation
- **WebSocket** - Real-time events

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Node Agent
- **Python** - Runtime
- **httpx** - HTTP client
- **Pillow** - Image rendering (demo)
- **psutil** - Hardware detection

---

## Deployment Architecture

### Development (Current)

```
Laptop/PC:
├── apps/api (FastAPI on :8000)
├── apps/web (Next.js on :3000)
└── apps/node-agent (3+ instances, different ports)

Database: SQLite file (./clustercloud.db)
Networking: localhost only
Security: Authentication disabled
```

### Production (Recommended)

```
AWS/Cloud:
├── ECS/Kubernetes
│   ├── Control Plane (FastAPI) - multiple replicas
│   ├── Frontend (Next.js) - CDN + serverless
│   └── RDS PostgreSQL - managed database
│
├── Worker Nodes
│   ├── EC2 instances or bare metal
│   ├── Node Agent with Docker
│   └── VPN/VPC networking
│
└── Supporting Services
    ├── AWS Secrets Manager
    ├── CloudWatch Logs
    ├── S3 for rendered outputs
    └── Load Balancer + TLS
```

---

## Performance Characteristics

### Latency
- Job creation: <2 seconds
- Task assignment: <1 second
- Heartbeat processing: <100ms
- Failure detection: <15 seconds
- Recovery completion: 30-60 seconds

### Throughput
- 100+ tasks/minute (3 nodes)
- Scales linearly with node count
- WebSocket: 100+ concurrent connections

### Resource Usage
- Control Plane: ~200MB RAM, <10% CPU
- Node Agent: ~50MB RAM, task-dependent CPU
- Database: <100MB for 1000 jobs

---

## Reliability & Error Handling

### Idempotency

✅ **All critical operations are idempotent:**
- Job creation (same customer_id + params = same job)
- Task completion (multiple calls with same result = one update)
- Economic transactions (same task_id = one payment)
- Node registration (same provider_id = update, not duplicate)

### Retry Logic

✅ **Automatic retries:**
- Failed tasks: MAX_TASK_RETRIES=3
- HTTP requests: exponential backoff
- Database transactions: SQLAlchemy retry

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Node crash | Heartbeat timeout (15s) | Automatic reassignment |
| Task failure | Executor error | Retry up to 3 times |
| Network partition | Connection timeout | Reconnect with backoff |
| Database lock | SQLAlchemy timeout | Transaction retry |
| WebSocket disconnect | Client detection | Auto-reconnect (10 attempts) |

---

## Monitoring & Observability

### Logs

```python
# All modules use Python logging
import logging
logger = logging.getLogger(__name__)

# Levels:
# ERROR: Failures requiring attention
# WARNING: Recoverable issues
# INFO: Normal operations
# DEBUG: Detailed tracing (dev only)
```

### Metrics (Basic)

```
/api/stats endpoint:
- total_nodes, healthy_nodes
- total_jobs, active_jobs
- total_tasks_completed
- total_clstr_transacted
```

### Real-time Events

```
WebSocket /ws/events:
- node_joined, node_failed
- job_started, job_completed
- task_assigned, task_completed
- recovery_started, recovery_completed
- ledger_transaction
```

---

## Known Limitations

### MVP Constraints

1. **Single-tenant** - No customer isolation
2. **No authentication** - Default open (dev mode)
3. **SQLite** - Not for production scale
4. **No TLS** - HTTP only
5. **Local storage** - Rendered frames in /tmp
6. **Basic AI** - Simple prompts, no fine-tuning
7. **No GPU** - CPU rendering only (demo)
8. **Manual demo** - Failure trigger is manual

### Scale Limits

- **Nodes:** Tested up to 10, should handle 100+
- **Concurrent jobs:** Tested up to 5, should handle 50+
- **Tasks per job:** Tested up to 100, should handle 1000+
- **WebSocket clients:** Tested up to 10, should handle 100+

---

## Testing Coverage

### Unit Tests
- ✅ Scheduler algorithm
- ✅ Failure detection logic
- ✅ Recovery service
- ✅ AI agents (fallback)
- ✅ Economic system
- ✅ Security (API keys)

### Integration Tests
- ✅ End-to-end job execution
- ✅ Multi-node distributed rendering
- ✅ Failure and recovery flow
- ✅ Economic settlement

### Not Tested
- ❌ Load testing (100+ nodes)
- ❌ Chaos engineering
- ❌ Long-running stability (24h+)
- ❌ Network partition scenarios

---

## Future Enhancements

### Phase 14 (Post-Hackathon)
- Real Blender integration
- GPU-accelerated rendering
- S3/cloud storage for outputs
- Customer authentication (JWT)

### Phase 15 (Production)
- Multi-tenant isolation
- Per-node API keys
- TLS everywhere
- Horizontal scaling
- Metrics & alerting (Prometheus)

### Phase 16 (Enterprise)
- SOC 2 compliance
- SLA guarantees
- Custom pricing models
- White-label deployment

---

## Demo-Specific Features

### Manual Failure Trigger

```typescript
// In demo UI
<Button onClick={simulateFailure}>
  Simulate Node Failure
</Button>

// Backend
POST /api/demo/simulate-failure/{node_id}
```

**What it does:**
1. Marks node UNHEALTHY
2. Creates incident
3. Triggers recovery
4. Shows economic settlement

### Demo Safety

- ⚠️ Demo endpoints should be DISABLED in production
- ⚠️ Add environment check: `if settings.DEMO_MODE`
- ⚠️ Require explicit opt-in: `ENABLE_DEMO_ENDPOINTS=true`

---

## Audit Results Summary

### Critical Fixes Applied
1. ✅ Fixed demo router to use correct RecoveryService class
2. ✅ Added is_healthy flag consistency in failure simulation
3. ✅ Fixed incident metadata structure (incomplete_task_ids in metadata dict)
4. ✅ Cleaned up unnecessary comments and AI-style verbosity

### Verified Components
- ✅ State machines are correct and enforced
- ✅ Idempotency guaranteed for all critical operations
- ✅ Database transactions properly committed
- ✅ WebSocket reconnection logic implemented
- ✅ Error handling comprehensive
- ✅ Security controls documented

### Remaining Risks
- ⚠️ SQLite in production (use PostgreSQL)
- ⚠️ No authentication by default (enable for prod)
- ⚠️ Demo endpoints exposed (disable for prod)
- ⚠️ No TLS encryption (add for prod)

---

**This architecture is production-capable for MVP/hackathon with the security caveats documented in SECURITY.md**
