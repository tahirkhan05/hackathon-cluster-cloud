# ClusterCloud - Complete Run Instructions

**For:** Hackathon Demo & Development  
**Platform:** Windows, macOS, Linux  
**Time Required:** 10 minutes setup

---

## Prerequisites

### Required Software

```bash
# Check versions
python --version    # Python 3.11+ required
node --version      # Node.js 18+ required
npm --version       # npm 9+ required
docker --version    # Docker 20+ required (optional but recommended)
```

### Install Missing Software

**Python 3.11+**
- Windows: https://www.python.org/downloads/
- macOS: `brew install python@3.11`
- Linux: `sudo apt install python3.11`

**Node.js 18+**
- All platforms: https://nodejs.org/

**Docker** (optional, for workload isolation)
- https://docs.docker.com/get-docker/

---

## Architecture Options

ClusterCloud supports two deployment modes:

### Single-Machine Demo (Development)
Run all components on one machine for quick testing and development.

### Two-Laptop Demo (Real Distributed)
**This is the authentic distributed demo:**
- **Laptop A:** Control plane (API + database + web UI)
- **Laptop B:** Real remote node agent

This section covers both modes.

---

## Quick Start (5 Minutes) - Single Machine

### 1. Clone Repository

```bash
git clone https://github.com/tahirkhan05/hackathon-cluster-cloud.git
cd hackathon-cluster-cloud
```

### 2. Start Backend

```bash
cd apps/api

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

**Verify:** Open http://localhost:8000/docs (Swagger UI)

### 3. Start Frontend (New Terminal)

```bash
cd apps/web

# Install dependencies
npm install

# Start dev server
npm run dev

# Should see:
# ready - started server on 0.0.0.0:3000
```

**Verify:** Open http://localhost:3000 (Landing page)

### 4. Start Node Agents (3 New Terminals)

```bash
# Terminal 1 - Node 1
cd apps/node-agent
python agent.py

# Terminal 2 - Node 2
cd apps/node-agent
python agent.py

# Terminal 3 - Node 3
cd apps/node-agent
python agent.py
```

**Verify:** Check http://localhost:3000/network (3 nodes HEALTHY)

---

## Two-Laptop Distributed Demo (Real Remote Nodes)

**This is the authentic ClusterCloud distributed execution demo.**

### Overview

```
┌─────────────────────────────────────┐
│        LAPTOP A (Control Plane)     │
│  ┌─────────────────────────────┐   │
│  │ FastAPI (port 8000)         │   │
│  │ SQLite Database             │   │
│  │ Next.js Web UI (port 3000)  │   │
│  └─────────────────────────────┘   │
│  LAN IP: 192.168.1.100              │
└─────────────────────────────────────┘
              ↑
              │ HTTP/WebSocket
              │ (LAN network)
              ↓
┌─────────────────────────────────────┐
│         LAPTOP B (Worker Node)      │
│  ┌─────────────────────────────┐   │
│  │ Node Agent (Python)         │   │
│  │ - Hardware Discovery        │   │
│  │ - Task Executor             │   │
│  │ - Heartbeat Monitor         │   │
│  └─────────────────────────────┘   │
│  Polls: http://192.168.1.100:8000   │
└─────────────────────────────────────┘
```

### Prerequisites

**Both laptops:**
- Python 3.11+
- Connected to same LAN/WiFi network
- Can ping each other

**Laptop A only:**
- Node.js 18+ (for web UI)

**Laptop B only:**
- Docker (optional, for workload isolation)

---

### Setup: Laptop A (Control Plane)

#### Step 1: Find Your LAN IP Address

**Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your active network adapter
# Example: 192.168.1.100
```

**macOS/Linux:**
```bash
ifconfig
# or
ip addr show
# Look for inet address (not 127.0.0.1)
# Example: 192.168.1.100
```

**Save this IP - you'll need it for Laptop B.**

#### Step 2: Configure Firewall

**Windows Firewall:**
```bash
# Allow Python (FastAPI) on port 8000
# Go to: Windows Defender Firewall → Advanced Settings → Inbound Rules
# New Rule → Port → TCP → Specific Ports: 8000 → Allow

# Or via PowerShell (as Administrator):
New-NetFirewallRule -DisplayName "ClusterCloud API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**macOS:**
```bash
# Usually no action needed for LAN
# If using firewall, allow Python and port 8000
```

**Linux:**
```bash
sudo ufw allow 8000/tcp
# or
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

#### Step 3: Start Backend

```bash
cd apps/api

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start server - BIND TO ALL INTERFACES
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Verify from Laptop A:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"clustercloud-api"}
```

#### Step 4: Start Frontend (Optional)

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000 on Laptop A to monitor the system.

---

### Setup: Laptop B (Worker Node)

#### Step 1: Configure Environment

Create file `apps/node-agent/.env`:

```bash
# CRITICAL: Replace with Laptop A's actual LAN IP
CONTROL_PLANE_URL=http://192.168.1.100:8000

# Node identity (optional - will auto-generate)
NODE_AGENT_ID=laptop-b-node-1

# API Key (if authentication enabled)
# NODE_AGENT_API_KEY=dev-node-agent-key

# Capacity
MAX_CONCURRENT_TASKS=2
COST_PER_TASK_CLSTR=10.0

# Heartbeat
HEARTBEAT_INTERVAL_SECONDS=5

# Logging
LOG_LEVEL=INFO
```

#### Step 2: Test Connectivity

**From Laptop B, test you can reach Laptop A:**

```bash
# Replace with your Laptop A IP
curl http://192.168.1.100:8000/health

# Expected: {"status":"healthy","service":"clustercloud-api"}
```

**If this fails:**
- Check both laptops on same network
- Verify firewall settings on Laptop A
- Try ping: `ping 192.168.1.100`
- Check Laptop A backend is running

#### Step 3: Start Node Agent

```bash
cd apps/node-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start agent
python agent.py
```

**Expected output:**
```
🚀 ClusterCloud Node Agent - Phase 5 (Distributed Execution)
============================================================
Configuration loaded:
  Control Plane: http://192.168.1.100:8000
  Provider ID: laptop-b-node-1
  Heartbeat Interval: 5s
  Max Concurrent Tasks: 2
============================================================
Hardware discovery complete
============================================================
Registering with control plane...
✓ Node registered: node-xxxxx
Task executor ready
============================================================
Starting agent services
Heartbeat interval: 5s
Task execution: ENABLED
============================================================
→ Heartbeat #1 sent successfully
→ Heartbeat #2 sent successfully
...
```

---

### Verification: Two-Laptop Registration

#### On Laptop A:

**Check registered nodes (API):**
```bash
curl http://localhost:8000/api/nodes | jq
```

**Expected:** Array with at least one node from Laptop B:
```json
{
  "nodes": [
    {
      "node_id": "node-xxxxx",
      "provider_id": "laptop-b-node-1",
      "name": "LAPTOP-B",
      "status": "HEALTHY",
      "is_healthy": true,
      "ip_address": "192.168.1.101",
      ...
    }
  ]
}
```

**Check web UI:**
1. Open http://localhost:3000/network
2. Should see node from Laptop B with GREEN status
3. Should show "Live" indicator (WebSocket connected)

#### On Laptop B:

**Check agent logs:**
- Should see: "Heartbeat #N sent successfully" every 5 seconds
- Should see: "Polling for tasks..." messages
- No error messages

---

### Running Distributed Job

#### Step 1: Create Job (from Laptop A)

**Option A: Web UI**
1. Open http://localhost:3000/build
2. Fill requirements:
   - Type: 3D Rendering
   - Frames: 20
   - Deadline: 1 hour
   - Budget: 500 CLSTR
   - Reliability: 85%
3. Click "Get Recommendation"
4. Click "Build My Cloud"

**Option B: API**
```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "demo-customer",
    "workload_type": "3d_rendering",
    "parameters": {
      "frame_count": 20,
      "resolution": "1920x1080",
      "deadline_minutes": 60,
      "budget_clstr": 500,
      "reliability_requirement": 0.85
    }
  }'
```

#### Step 2: Watch Execution

**On Laptop A (Web UI):**
- Navigate to http://localhost:3000/jobs
- Watch tasks being assigned to Laptop B node
- See progress bar advancing

**On Laptop B (Agent Terminal):**
```
→ Received task: task-xxxxx
→ Starting task task-xxxxx
→ Starting frame 1
→ Rendering complete, uploading...
→ Task task-xxxxx completed successfully
```

**On Laptop A (API):**
```bash
# Get job status
curl http://localhost:8000/api/jobs/{job_id} | jq

# Watch tasks
curl http://localhost:8000/api/jobs/{job_id}/tasks | jq
```

#### Step 3: Verify Distributed Execution

**Proof of remote execution:**
1. Laptop B agent logs show task execution
2. Laptop A does NOT execute tasks locally
3. Rendered frames appear on Laptop B filesystem:
   ```bash
   # On Laptop B
   ls apps/node-agent/rendered_frames/
   # Should see: frame_000001.png, frame_000002.png, etc.
   ```
4. Job completes successfully on Laptop A dashboard

---

### Simulating Node Failure (Two-Laptop Demo)

This demonstrates **automatic recovery** in a real distributed system.

#### Step 1: Start Job with Multiple Nodes

**Recommended:** Start 1-2 additional node agents on Laptop A for faster recovery:
```bash
# On Laptop A (separate terminal)
cd apps/node-agent
python agent.py
```

Now you have:
- 1 remote node on Laptop B
- 1-2 local nodes on Laptop A

#### Step 2: Create Large Job

Create job with 30-50 frames so Laptop B gets multiple tasks.

#### Step 3: Simulate Failure

**Option A: Manual Termination (Realistic)**

On Laptop B, while tasks are running:
```bash
# Press Ctrl+C in the agent terminal
# Or forcefully kill:
pkill -9 python
```

**Option B: Demo UI Trigger**

1. Open http://localhost:3000/demo on Laptop A
2. Click "Simulate Node Failure"
3. Select the Laptop B node
4. Click "Confirm"

#### Step 4: Watch Recovery

**On Laptop A (Web UI):**

1. **Detection (< 15 seconds):**
   - Laptop B node turns RED
   - Status: UNHEALTHY

2. **Incident Created:**
   - Incident panel appears
   - Shows affected tasks
   - "Recovery in progress..."

3. **Recovery (30-60 seconds):**
   - AI Recovery Agent recommends replacement
   - Tasks reassigned to healthy nodes (Laptop A agents)
   - Progress resumes

4. **Completion:**
   - Job completes successfully
   - Incident resolved
   - Economic settlement shown

**On Laptop A (API):**
```bash
# Check incidents
curl http://localhost:8000/api/incidents | jq

# Check node status
curl http://localhost:8000/api/nodes | jq '.[] | {node_id, status, is_healthy}'
```

**Expected Behavior:**
```json
{
  "incident_id": "incident-xxxxx",
  "incident_type": "node_failure",
  "status": "RESOLVED",
  "affected_tasks": 5,
  "resolution": "All 5 tasks successfully reassigned and restarted"
}
```

---

### Troubleshooting: Two-Laptop Setup

#### Issue: Laptop B Cannot Connect

**Symptom:** Agent shows "Connection refused" or timeout

**Diagnosis:**
```bash
# From Laptop B
ping 192.168.1.100  # Replace with Laptop A IP

# Test API directly
curl http://192.168.1.100:8000/health
```

**Fixes:**
1. **Firewall on Laptop A:**
   - Windows: Check Defender Firewall allowed apps
   - Temporarily disable to test: `netsh advfirewall set allprofiles state off`
   - Re-enable after: `netsh advfirewall set allprofiles state on`

2. **Backend not bound to 0.0.0.0:**
   - Must use `--host 0.0.0.0`, not `localhost` or `127.0.0.1`

3. **Wrong IP address:**
   - Verify Laptop A IP with `ipconfig` / `ifconfig`
   - Make sure using LAN IP, not VPN or virtual adapter

4. **Different subnets:**
   - Both laptops must be on same network (e.g., 192.168.1.x)

#### Issue: Node Registers but No Tasks

**Symptom:** Node shows HEALTHY but never receives work

**Diagnosis:**
```bash
# Check agent logs for "Polling for tasks..."
# Check backend logs for task assignment

# Verify node in system
curl http://192.168.1.100:8000/api/nodes
```

**Fixes:**
1. **No jobs running:** Create a job first
2. **Node incompatible:** Check node capabilities meet job requirements
3. **Node at capacity:** Check `current_task_count < max_concurrent_tasks`

#### Issue: Heartbeat Fails

**Symptom:** Node marked OFFLINE/UNHEALTHY immediately

**Diagnosis:**
```bash
# Check agent logs for heartbeat errors
# Check if heartbeat endpoint reachable
curl -X POST http://192.168.1.100:8000/api/nodes/{node_id}/heartbeat
```

**Fixes:**
1. **Intermittent connection:** Increase `HEARTBEAT_TIMEOUT_SECONDS`
2. **Slow network:** Increase `HEARTBEAT_INTERVAL_SECONDS`
3. **Backend overloaded:** Check backend logs for errors

#### Issue: WebSocket Not Updating on Laptop A

**Symptom:** Web UI doesn't show real-time updates

**Fixes:**
1. Check green "Live" indicator in header
2. Browser console: Check for WebSocket errors
3. Refresh page: WebSocket auto-reconnects
4. Check CORS: Backend allows `http://localhost:3000`

---

### Network Requirements Summary

**Required Ports:**
- **8000/TCP** - API (HTTP + WebSocket)
- **3000/TCP** - Frontend (optional, only for viewing on Laptop A)

**Network Configuration:**
- Both laptops on same LAN
- No VPN between laptops (can cause routing issues)
- Laptop A must be reachable from Laptop B on port 8000

**Security:**
- For demo: Open firewall on Laptop A for port 8000
- For production: Use VPN, mTLS, or private network

---

### Two-Laptop Demo Checklist

**Before demo:**
- [ ] Both laptops on same WiFi/LAN
- [ ] Laptop A IP known (e.g., 192.168.1.100)
- [ ] Firewall on Laptop A allows port 8000
- [ ] Backend running on Laptop A with `--host 0.0.0.0`
- [ ] Can curl health check from Laptop B
- [ ] Frontend running on Laptop A (optional)

**Start demo:**
- [ ] Laptop B agent starts successfully
- [ ] Laptop B node appears in `/network` view
- [ ] Node status: HEALTHY (green)
- [ ] Create job with 30+ frames
- [ ] Confirm Laptop B receives tasks

**Failure simulation:**
- [ ] Job has tasks in RUNNING state
- [ ] Kill Laptop B agent (Ctrl+C or force)
- [ ] Wait 15-20 seconds
- [ ] Laptop B node turns RED (UNHEALTHY)
- [ ] Incident created
- [ ] Tasks reassigned to remaining nodes
- [ ] Job continues and completes

**Success criteria:**
- ✅ Job completes despite Laptop B failure
- ✅ All frames rendered
- ✅ Economic settlement recorded
- ✅ Incident marked RESOLVED

---

## Detailed Setup

### Backend Setup

```bash
cd apps/api

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Configure environment
cp .env.development.example .env.development

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Alternative: with auto-reload
python main.py
```

**Environment Variables** (`.env.development`):
```bash
# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./clustercloud.db

# Security (Development - disabled)
ENABLE_NODE_AUTH=false

# AWS Bedrock (Optional - for AI features)
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret

# Resource Limits
MAX_TASK_MEMORY_MB=2048
MAX_TASK_CPU_CORES=2.0
TASK_TIMEOUT_SECONDS=120
```

### Frontend Setup

```bash
cd apps/web

# Install dependencies
npm install
# or
yarn install

# Optional: Configure API URL
cp .env.local.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev

# Alternative: production build
npm run build
npm start
```

### Node Agent Setup

```bash
cd apps/node-agent

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Optional: Configure
# Set CONTROL_PLANE_URL if API is not on localhost
export CONTROL_PLANE_URL=http://localhost:8000

# Start agent
python agent.py

# Agent will:
# 1. Detect hardware (CPU, RAM, GPU)
# 2. Register with control plane
# 3. Send heartbeats every 5 seconds
# 4. Poll for tasks every 3 seconds
```

**Multiple Nodes on Same Machine:**
Each agent process automatically gets a unique node_id. Just run `python agent.py` in multiple terminals.

---

## Verification Checklist

After starting all services:

### Backend Health

```bash
# Health check
curl http://localhost:8000/health

# Expected:
# {"status":"healthy","service":"clustercloud-api"}

# Check nodes
curl http://localhost:8000/api/nodes

# Expected: Array of registered nodes
```

### Frontend Connectivity

1. Open http://localhost:3000
2. Navigate to `/dashboard`
3. Check "Live" indicator in header (WebSocket connected)
4. Navigate to `/network`
5. Verify 3 nodes show as HEALTHY

### WebSocket Connection

1. Open browser DevTools (F12)
2. Go to Network tab → WS filter
3. Should see: `ws://localhost:8000/ws/events` connected
4. Should receive `connection_established` event

---

## Running the Demo

### Option 1: Guided Demo Page

1. Open http://localhost:3000/demo
2. Click "Start Demo Job"
3. Wait for job to start (RUNNING status)
4. Click "Simulate Node Failure"
5. Watch automatic recovery
6. Observe economic settlement

### Option 2: Manual Flow

1. Open http://localhost:3000/build
2. Fill in workload requirements:
   - Workload: 3D Rendering
   - Frames: 20
   - Deadline: 1 hour
   - Budget: 500 CLSTR
   - Reliability: 85%
3. Click "Get Recommendation"
4. Review AI analysis
5. Click "Build My Cloud"
6. Navigate to /jobs to watch progress
7. Use /demo to trigger failure

---

## Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Fix:**
```bash
cd apps/api
pip install -r requirements.txt
```

**Error:** `Address already in use: 8000`

**Fix:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9

# Or change port:
uvicorn main:app --port 8001
```

### Frontend Won't Start

**Error:** `Cannot find module 'next'`

**Fix:**
```bash
cd apps/web
rm -rf node_modules package-lock.json
npm install
```

**Error:** `EADDRINUSE: port 3000 already in use`

**Fix:**
```bash
# Change port:
npm run dev -- -p 3001
```

### Nodes Not Registering

**Check 1:** Backend running?
```bash
curl http://localhost:8000/health
```

**Check 2:** Agent errors?
```bash
# Look for error messages in agent terminal
# Common: Connection refused (backend not running)
```

**Check 3:** Environment variable?
```bash
# If backend is not on localhost:
export CONTROL_PLANE_URL=http://your-backend-ip:8000
python agent.py
```

### WebSocket Not Connecting

**Check 1:** Backend WebSocket endpoint
```bash
# Should return 426 Upgrade Required (correct)
curl http://localhost:8000/ws/events
```

**Check 2:** Browser console
- Open DevTools → Console
- Look for WebSocket errors
- Check Network → WS tab for connection status

**Fix:** Clear browser cache and reload

### No Tasks Executing

**Check 1:** Job created?
```bash
curl http://localhost:8000/api/jobs
```

**Check 2:** Tasks assigned?
```bash
curl http://localhost:8000/api/jobs/{job_id}/tasks
```

**Check 3:** Nodes polling?
- Agent terminal should show: "Polling for tasks..."
- If not, check CONTROL_PLANE_URL

### Demo Failure Not Working

**Check 1:** Job running?
- Must have active job with status=RUNNING
- Tasks must be ASSIGNED or RUNNING

**Check 2:** Node healthy?
- Selected node must be HEALTHY before failure
- Check /network page

**Check 3:** Backend logs
```bash
# Look for:
# "DEMO: Simulating failure for node..."
# "DEMO: Created incident..."
# "DEMO: Recovery result..."
```

---

## Performance Tuning

### Faster Demo

```bash
# Reduce task timeout for quicker completion
# In .env.development:
TASK_TIMEOUT_SECONDS=30

# Increase polling frequency
# In apps/node-agent/config.py:
POLL_INTERVAL_SECONDS = 1
```

### More Nodes

```bash
# Start 5+ nodes for more dramatic distribution
for i in {1..5}; do
    python agent.py &
done
```

### Slower Demo (For Presentation)

```bash
# Add artificial delay to show animations
# In apps/node-agent/executor.py, add:
time.sleep(5)  # Before completing task
```

---

## Docker Workload Isolation

### Enable Docker Isolation

1. Install Docker Desktop
2. Start Docker daemon
3. Pull demo image:
```bash
docker pull python:3.11-slim
```

4. Verify:
```bash
python -c "from apps.node-agent.docker_isolation import DockerIsolation; print(DockerIsolation.check_docker_available())"
```

### Disable Docker (Dev Mode)

In `config.py`:
```python
ENABLE_DOCKER_ISOLATION = False
```

Tasks will execute directly (faster but no isolation).

---

## Production Deployment

### Backend (Production)

```bash
cd apps/api

# Use production environment
cp .env.production.example .env.production

# Edit .env.production:
# - Set ENABLE_NODE_AUTH=true
# - Generate secure NODE_API_KEY
# - Use PostgreSQL DATABASE_URL
# - Set AWS credentials

# Install production dependencies
pip install -r requirements.txt
pip install gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (Production)

```bash
cd apps/web

# Build production bundle
npm run build

# Start production server
npm start

# Or deploy to Vercel/Netlify
vercel deploy
```

### Database Migration

```bash
# Export from SQLite
sqlite3 clustercloud.db .dump > backup.sql

# Import to PostgreSQL
psql -U user -d clustercloud < backup.sql

# Update DATABASE_URL
DATABASE_URL=postgresql://user:pass@host:5432/clustercloud
```

---

## Stopping Services

### Graceful Shutdown

```bash
# In each terminal, press Ctrl+C

# Backend will:
# - Complete current requests
# - Close database connections
# - Shutdown cleanly

# Frontend will:
# - Stop dev server
# - Keep build files

# Node agents will:
# - Send final heartbeat
# - Deregister from control plane
```

### Force Kill

```bash
# Windows
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# macOS/Linux
pkill -9 python
pkill -9 node
```

### Clean State

```bash
# Remove database
rm apps/api/clustercloud.db

# Clear node cache
rm -rf apps/node-agent/__pycache__

# Clear frontend cache
rm -rf apps/web/.next
```

---

## Directory Structure Quick Reference

```
hackathon-cluster-cloud/
├── apps/
│   ├── api/                   # FastAPI backend
│   │   ├── main.py           # Entry point
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   └── domains/          # Business logic
│   │       ├── jobs/
│   │       ├── tasks/
│   │       ├── nodes/
│   │       ├── scheduling/
│   │       ├── recovery/
│   │       ├── ai/
│   │       ├── ledger/
│   │       └── demo/
│   │
│   ├── web/                   # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/          # Pages
│   │   │   ├── components/   # UI components
│   │   │   ├── lib/          # API client, utils
│   │   │   └── hooks/        # React hooks
│   │   └── package.json
│   │
│   └── node-agent/            # Python worker agent
│       ├── agent.py          # Main entry point
│       ├── executor.py       # Task execution
│       ├── renderer.py       # Demo renderer
│       └── hardware.py       # Hardware detection
│
└── docs/
    ├── SECURITY.md           # Security documentation
    ├── DEMO_SCRIPT.md        # 8-minute demo guide
    ├── FINAL_ARCHITECTURE.md # Architecture details
    └── RUN_INSTRUCTIONS.md   # This file
```

---

## Quick Command Reference

```bash
# Start everything
cd apps/api && uvicorn main:app --reload &
cd apps/web && npm run dev &
cd apps/node-agent && python agent.py &
cd apps/node-agent && python agent.py &
cd apps/node-agent && python agent.py &

# Check status
curl http://localhost:8000/health
curl http://localhost:8000/api/stats
curl http://localhost:8000/api/nodes

# Watch logs
tail -f apps/api/clustercloud.log

# Reset demo
curl -X POST http://localhost:8000/api/demo/reset

# Stop everything
pkill -INT python node
```

---

## Getting Help

### Logs

**Backend:** Check terminal output or `apps/api/clustercloud.log`  
**Frontend:** Check terminal output and browser console  
**Node Agent:** Check terminal output

### Common Commands

```bash
# Backend health check
curl http://localhost:8000/health

# List nodes
curl http://localhost:8000/api/nodes | jq

# List jobs
curl http://localhost:8000/api/jobs | jq

# System stats
curl http://localhost:8000/api/stats | jq

# Demo status
curl http://localhost:8000/api/demo/status | jq
```

### Documentation

- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Architecture:** docs/FINAL_ARCHITECTURE.md
- **Security:** docs/SECURITY.md
- **Demo Script:** docs/DEMO_SCRIPT.md

---

**You're ready to demo! 🚀**
