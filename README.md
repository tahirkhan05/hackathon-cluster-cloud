# ClusterCloud 

> A decentralized community cloud computing marketplace powered by distributed nodes, economic incentives, and AI-driven orchestration.

![Architecture](./diagrams/Architecture.jpeg)

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [System Components](#system-components)
- [Workflow](#workflow)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Domains](#api-domains)
- [Technology Stack](#technology-stack)
- [Configuration](#configuration)
- [Development](#development)
- [Demo](#demo)
- [Economic System](#economic-system)
- [Reliability & Recovery](#reliability--recovery)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

ClusterCloud is a next-generation distributed computing platform that enables anyone to contribute computing resources to a shared marketplace. Built with reliability, fairness, and efficiency at its core, it combines:

- **Decentralized Execution**: Distributed node agents running on commodity hardware
- **Economic Incentives**: Blockchain-inspired ledger system with stakes, rewards, and penalties
- **AI Orchestration**: Intelligent workload scheduling and failure recovery
- **Real-time Monitoring**: WebSocket-based live updates and system observability
- **Fault Tolerance**: Automatic failure detection and cascading impact analysis

### Workflow Diagram

![Workflow](./diagrams/Workflow%20drawings.png)

## ✨ Key Features

### 🎯 Distributed Task Execution
- **Dynamic Workload Scheduling**: Intelligent task assignment based on node capabilities
- **Parallel Processing**: Concurrent task execution across multiple nodes
- **Resource Optimization**: Hardware-aware task distribution

### 💰 Economic System
- **Provider Stakes**: Nodes stake tokens to ensure reliability
- **Performance-Based Rewards**: Earn tokens for successful task completion
- **Automatic Penalties**: Failed tasks trigger financial penalties
- **Broker Fees**: Platform sustainability through transaction fees
- **Customer Credits**: Initial balance for job submission

### 🛡️ Reliability & Fault Tolerance
- **Heartbeat Monitoring**: Continuous node health tracking
- **Failure Detection**: Immediate identification of node failures
- **Automatic Recovery**: AI-powered recovery action planning
- **Cascade Analysis**: Impact assessment for downstream dependencies
- **Task Retry Logic**: Configurable retry mechanisms with exponential backoff

### 🤖 AI-Powered Intelligence
- **Workload Agent**: Analyzes requirements and recommends resources
- **Provider Agent**: Evaluates node capabilities and constraints
- **Recovery Agent**: Generates recovery strategies for failures
- **Decision Window**: Intelligent timeout windows for failure response

### 📊 Real-Time Observability
- **WebSocket Streaming**: Live task status updates
- **System Statistics**: Comprehensive metrics dashboard
- **Incident Tracking**: Automatic incident creation and lifecycle management
- **Audit Logs**: Complete transaction history

## 🧩 System Components

### 1. **Control Plane API** (`apps/api`)
FastAPI-based backend orchestrating the entire system:

- **Jobs**: Workload submission and management
- **Tasks**: Individual execution units
- **Nodes**: Worker registration and lifecycle
- **Workloads**: Job templates and specifications
- **Scheduling**: Intelligent task assignment
- **Ledger**: Economic transaction tracking
- **Recovery**: Failure handling and remediation
- **Impact Analysis**: Cascade effect evaluation
- **Reliability**: Health checks and monitoring
- **WebSocket**: Real-time event streaming

### 2. **Node Agent** (`apps/node-agent`)
Python-based worker daemon that:

- Discovers hardware capabilities (CPU, GPU, memory, disk)
- Registers with control plane
- Maintains heartbeat connection
- Polls for assigned tasks
- Executes workloads in isolated environments
- Reports progress and status
- Handles graceful shutdown

### 3. **Web Dashboard** (`apps/web`)
Next.js frontend providing:

- Job submission interface
- Real-time task monitoring
- Node management dashboard
- Economic ledger visualization
- Incident tracking UI
- System statistics and analytics

## 📊 API Domains

| Domain | Purpose | Key Features |
|--------|---------|--------------|
| **Jobs** | Workload lifecycle management | Submit, track, cancel jobs |
| **Tasks** | Granular execution tracking | Status updates, retries, results |
| **Nodes** | Worker node management | Registration, health, capabilities |
| **Workloads** | Job templates | Pre-configured workload types |
| **Scheduling** | Task assignment | AI-powered optimization |
| **Ledger** | Economic transactions | Stakes, payments, penalties |
| **Recovery** | Failure remediation | Automated recovery plans |
| **Impact** | Cascade analysis | Dependency impact assessment |
| **Incidents** | Issue tracking | Auto-creation, escalation |
| **Reliability** | System health | Metrics, SLAs, health checks |
| **Stats** | Analytics | System-wide statistics |
| **WebSocket** | Real-time events | Live updates, streaming |
| **Demo** | Testing utilities | Simulation endpoints |

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ORM**: SQLAlchemy with Alembic migrations
- **Async Support**: asyncio, WebSockets
- **AI Integration**: AWS Bedrock (Claude 3 Sonnet)
- **Validation**: Pydantic v2

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **State**: React Hooks

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Custom scheduler
- **Networking**: Bridge network for inter-service communication
- **Storage**: Volume persistence for PostgreSQL

### Node Agent
- **Language**: Python 3.11+
- **Hardware Discovery**: platform, psutil, GPUtil
- **Process Management**: Threading, signal handling
- **Logging**: Structured logging with levels

## ⚙️ Configuration

### Environment Variables

#### API Configuration (`apps/api/.env`)
```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./clustercloud.db
# DATABASE_URL=postgresql://user:pass@postgres:5432/clustercloud

# Security
JWT_SECRET=your-secret-key-change-in-production
NODE_API_KEY=optional-api-key-for-nodes
ENABLE_NODE_AUTH=false

# Resource Limits
MAX_TASK_MEMORY_MB=2048
MAX_TASK_CPU_CORES=2.0
MAX_TASK_DISK_MB=5120

# Docker
ENABLE_DOCKER_ISOLATION=true
DOCKER_SECURITY_OPT=no-new-privileges:true
DOCKER_NETWORK=clustercloud_network

# AWS Bedrock (AI)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Timeouts
WORKLOAD_TIMEOUT_SECONDS=300
TASK_TIMEOUT_SECONDS=120
HEARTBEAT_TIMEOUT_SECONDS=15

# Economic System
INITIAL_CUSTOMER_BALANCE=10000
PROVIDER_RELIABILITY_STAKE=100
BROKER_FEE_PERCENTAGE=5
FAILURE_PENALTY_PERCENTAGE=20
RECOVERY_REWARD_PERCENTAGE=10
```

#### Node Agent Configuration (`apps/node-agent/.env`)
```bash
# Control Plane
CONTROL_PLANE_URL=http://localhost:8000
PROVIDER_ID=provider-001

# Agent Settings
HEARTBEAT_INTERVAL_SECONDS=5
MAX_CONCURRENT_TASKS=2
LOG_LEVEL=INFO

# Demo Mode (optional)
SIMULATE_FAILURE=false
FAILURE_AFTER_SECONDS=120
```

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for web development)

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd cluster_cloud
```

2. **Configure environment**
```bash
cp .env.example .env
cp apps/api/.env.development.example apps/api/.env.development
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Verify services**
```bash
# API Health Check
curl http://localhost:8000/health

# Web Dashboard
open http://localhost:3000

# API Documentation
open http://localhost:8000/docs
```

### Local Development

#### API Backend
```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### Web Frontend
```bash
cd apps/web
npm install
npm run dev
```

#### Node Agent
```bash
cd apps/node-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python agent.py
```

## 🎬 Demo

Run the complete end-to-end distributed rendering demo:

```bash
python demo_distributed_rendering.py
```

This demo will:
1. ✅ Start the API backend
2. ✅ Launch multiple node agents
3. ✅ Submit a distributed rendering job (12 frames)
4. ✅ Watch tasks execute across nodes
5. ✅ Display results and statistics

### Demo Features
- **Multi-node simulation**: 3 worker nodes
- **Parallel execution**: Tasks distributed automatically
- **Live monitoring**: Real-time progress updates
- **Result verification**: Output validation
- **Economic tracking**: View ledger transactions

## 💎 Economic System

ClusterCloud implements a blockchain-inspired economic model:

### Transaction Types

| Type | Trigger | Amount | Purpose |
|------|---------|--------|---------|
| **Stake** | Node registration | `PROVIDER_RELIABILITY_STAKE` | Ensure provider commitment |
| **Job Payment** | Job submission | Task price × count | Reserve funds for execution |
| **Task Reward** | Task completion | Task price | Pay provider for work |
| **Broker Fee** | Task completion | Price × `BROKER_FEE_PERCENTAGE` | Platform sustainability |
| **Failure Penalty** | Task failure | Stake × `FAILURE_PENALTY_PERCENTAGE` | Discourage unreliable nodes |
| **Recovery Reward** | Recovery task | Original price × `RECOVERY_REWARD_PERCENTAGE` | Incentivize failure handling |

### Balance Management
- **Customers**: Start with `INITIAL_CUSTOMER_BALANCE` credits
- **Providers**: Must maintain stake balance for active nodes
- **Platform**: Collects broker fees for sustainability

### Example Flow
```
1. Provider stakes 100 tokens → Node registers
2. Customer submits job (10 tasks × 50 = 500 tokens)
3. Task completes → Provider +50, Platform +2.5
4. Task fails → Provider -20 penalty
5. Recovery succeeds → Recovery node +5 bonus
```

## 🔄 Reliability & Recovery

### Failure Detection
```python
# Heartbeat-based health monitoring
HEARTBEAT_TIMEOUT = 15 seconds
MAX_CONSECUTIVE_FAILURES = 3

if node.last_heartbeat > TIMEOUT:
    mark_as_unhealthy()
    trigger_incident()
    initiate_recovery()
```

### Recovery Process

1. **Detection**: Heartbeat monitor identifies failure
2. **Incident Creation**: Automatic incident logged
3. **Impact Analysis**: Cascade analyzer evaluates dependencies
4. **AI Planning**: Recovery agent generates action plan
5. **Execution**: Recovery service coordinates remediation
6. **Verification**: Confirm recovery success

### Cascade Analysis
The impact analyzer evaluates:
- Direct task failures on the failed node
- Downstream tasks waiting on failed task results
- Job completion blockers
- Economic impact (penalties, refunds)

## 📁 Project Structure

```
cluster_cloud/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── domains/           # Domain-driven design modules
│   │   │   ├── ai/           # AI agent implementations
│   │   │   ├── jobs/         # Job management
│   │   │   ├── tasks/        # Task execution
│   │   │   ├── nodes/        # Node lifecycle
│   │   │   ├── scheduling/   # Task assignment
│   │   │   ├── ledger/       # Economic system
│   │   │   ├── recovery/     # Failure handling
│   │   │   ├── impact/       # Cascade analysis
│   │   │   └── ...
│   │   ├── alembic/          # Database migrations
│   │   ├── config.py         # Configuration management
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── main.py           # Application entry point
│   │   └── requirements.txt
│   │
│   ├── node-agent/            # Python worker agent
│   │   ├── agent.py          # Main agent orchestrator
│   │   ├── config.py         # Agent configuration
│   │   ├── hardware.py       # Capability discovery
│   │   ├── registration.py   # Control plane registration
│   │   ├── heartbeat.py      # Health monitoring
│   │   ├── executor.py       # Task execution engine
│   │   └── requirements.txt
│   │
│   └── web/                   # Next.js frontend
│       ├── app/              # Next.js 14 app directory
│       ├── components/       # React components
│       ├── public/           # Static assets
│       └── package.json
│
├── diagrams/                  # Architecture documentation
│   ├── Architecture.jpeg
│   └── Workflow drawings.png
│
├── docker-compose.yml         # Multi-service orchestration
├── .env.example              # Environment template
└── demo_distributed_rendering.py  # End-to-end demo
```

**Built with ❤️ by the ClusterCloud community**

For questions, issues, or feature requests, please open an issue on GitHub.
