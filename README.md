# ClusterCloud

**Community-owned cloud computing marketplace for distributed workloads**

ClusterCloud enables individuals to share compute resources and allows customers to execute parallelizable workloads across a distributed network of provider nodes—without understanding traditional cloud infrastructure.

## 🎯 MVP Focus: 3D Frame Rendering

This hackathon MVP demonstrates distributed 3D rendering with:

- **Automatic workload analysis** using AI
- **Intelligent resource selection** and task distribution
- **Real-time failure detection** and automatic recovery
- **Economic incentives** through the CLSTR token system
- **Live monitoring** dashboard with full visibility

## 🏗️ Architecture

### Modular Monolith Control Plane
- **Workloads**: Job definitions and workload type registry
- **Jobs & Tasks**: State management and execution tracking
- **Nodes**: Provider registration and capability tracking
- **Scheduling**: Task assignment and resource matching
- **Execution**: Orchestration and progress monitoring
- **Incidents**: Failure detection and recovery coordination
- **Reliability**: Provider reputation and history
- **Ledger**: CLSTR tokenomics and transactions
- **AI Orchestration**: Bedrock integration for intelligent decisions

### Distributed Workers
- **Node Agent**: Python daemon running on provider machines
- Registers with control plane
- Executes rendering tasks in isolated Docker containers
- Sends heartbeat signals
- Reports task progress and results

### Frontend
- **Next.js dashboard** with real-time WebSocket updates
- Simple customer workflow: specify workload → observe execution
- Network health, active jobs, incidents, and recovery activity

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL (or SQLite for development)
- AWS credentials with Bedrock access

### Setup

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd clustercloud
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start infrastructure**
   ```bash
   docker-compose up -d
   ```

3. **Set up backend**
   ```bash
   cd apps/api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   python main.py
   ```

4. **Set up node agent(s)**
   ```bash
   cd apps/node-agent
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python agent.py
   ```

5. **Set up frontend**
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

6. **Access the dashboard**
   Open http://localhost:3000

## 🎬 Demo Scenario

The demo showcases automatic failure recovery:

1. Customer submits 100-frame rendering job
2. AI analyzes workload as parallelizable
3. System selects 4 provider nodes
4. Frames distributed (25 frames per node)
5. Live progress dashboard shows execution
6. **Node C fails mid-rendering**
7. System detects missing heartbeat
8. Recovery agent identifies incomplete tasks
9. Compatible replacement node selected
10. Tasks reassigned automatically
11. Rendering continues seamlessly
12. Reliability scores and CLSTR ledger updated
13. Final rendered frames available

## 📦 Repository Structure

```
clustercloud/
├── apps/
│   ├── api/              # FastAPI control plane
│   ├── node-agent/       # Python node worker
│   └── web/              # Next.js dashboard
├── packages/
│   └── shared/           # Shared types and utilities
├── infrastructure/
│   ├── docker/           # Container configs
│   └── aws/              # AWS deployment configs
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── tests/                # Integration tests
└── docker-compose.yml    # Local development stack
```

## 🔒 Security (MVP)

- Docker container isolation for workloads
- Non-privileged execution with resource limits
- Restricted network access
- Ephemeral job workspaces
- API key authentication between components
- No host filesystem exposure
- Audit logging for all operations

**Note**: This is a hackathon MVP. Production deployment requires additional security hardening.

## 💰 CLSTR Tokenomics

Internal simulated currency for the MVP:

- **Customers** spend CLSTR for compute resources
- **Providers** earn CLSTR by executing tasks successfully
- **Broker fee** (5%) deducted from transactions
- **Reliability stake** held for quality assurance
- **Penalties** applied for node failures
- **Rewards** given for successful recovery assistance

All transactions are deterministic and auditable.

## 🧪 Testing

```bash
# Run backend tests
cd apps/api
pytest

# Run frontend tests
cd apps/web
npm test

# Run integration tests
cd tests
pytest
```

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

This is a hackathon MVP. Contributions welcome after initial demo!

---

Built for the hackathon by the ClusterCloud team
