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

### What Is Real (Genuinely Implemented)

✅ **Distributed Execution:**
- Remote node registration and capability discovery
- Pull-based task polling (firewall-friendly)
- Distributed task execution across multiple machines
- Real heartbeat monitoring (5s interval)
- Real-time WebSocket events

✅ **Failure & Recovery:**
- Heartbeat-based failure detection (< 15s)
- Automatic task reassignment to healthy nodes
- AI recovery recommendations with deterministic validation
- Incident tracking and resolution
- Economic penalties and rewards

✅ **AI Orchestration:**
- AWS Bedrock integration (Claude Sonnet 3.5)
- Workload analysis and resource planning
- Recovery decision recommendations
- Fallback logic when AI unavailable
- All recommendations validated deterministically

✅ **Economic System:**
- CLSTR internal token ledger
- Auditable transaction history
- Provider rewards and penalties
- Customer compensation for failures
- Deterministic accounting (no double-payments)

✅ **Reliability Tracking:**
- Provider reliability scoring
- Task success rate tracking
- Uptime monitoring
- Historical performance metrics

### What Is Simulated (MVP Limitations)

⚠️ **Rendering Workload:**
- Uses simulated Python renderer (not real Blender)
- Generates placeholder images for demo speed
- Real Blender integration: post-MVP (~1 week)

⚠️ **GPU Rendering:**
- CPU-based simulation only
- GPU detection present, rendering simulated
- Real GPU rendering: post-MVP

⚠️ **Storage:**
- Local filesystem storage
- S3/cloud storage: production deployment

⚠️ **Payment Processing:**
- Internal CLSTR tokens only
- Real payment integration (Stripe): production

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
- Python 3.11+
- Node.js 18+
- Docker (optional, for workload isolation)
- AWS credentials with Bedrock access (optional, for AI features)

### Setup

1. **Clone and configure**
   ```bash
   git clone https://github.com/tahirkhan05/hackathon-cluster-cloud.git
   cd cluster_cloud
   ```

2. **Set up backend**
   ```bash
   cd apps/api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

3. **Set up node agent(s)**
   ```bash
   cd apps/node-agent
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python agent.py
   ```

4. **Set up frontend**
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

5. **Access the dashboard**
   Open http://localhost:3000

**For detailed setup including two-laptop distributed demo, see [docs/RUN_INSTRUCTIONS.md](docs/RUN_INSTRUCTIONS.md)**

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
├── docs/                 # Documentation
└── docker-compose.yml    # Local development stack (optional)
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
