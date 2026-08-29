# 🚀 Two-Laptop Demo - Quick Start Guide

**Goal:** Run ClusterCloud with real distributed execution across 2 laptops.

**Time:** 15 minutes

---

## 📋 What You Need

- **Laptop A:** Control plane (API + Database + Web UI)
- **Laptop B:** Remote worker node
- Both on **same WiFi/LAN network**
- Both have Python 3.11+ and Node.js 18+ installed

---

## 🖥️ LAPTOP A SETUP (Control Plane)

This is your "current" laptop where the code is.

### Step 1: Find Your IP Address

**Windows:**
```bash
ipconfig
```
Look for **"IPv4 Address"** under your WiFi adapter.  
Example: `192.168.1.100`

**Write this down - you'll need it for Laptop B!**

### Step 2: Allow Firewall Access

**Windows (Run as Administrator in PowerShell):**
```powershell
New-NetFirewallRule -DisplayName "ClusterCloud API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

Or manually:
1. Windows Security → Firewall → Advanced Settings
2. Inbound Rules → New Rule
3. Port → TCP → 8000 → Allow

### Step 3: Start Backend

```bash
cd apps\api

# Install dependencies (first time only)
python -m pip install -r requirements.txt

# Start API (IMPORTANT: bind to 0.0.0.0, not localhost!)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Wait for:** `Application startup complete`

**Verify:** Open http://localhost:8000/docs in your browser

### Step 4: Start Frontend (Optional but recommended)

Open a **new terminal** on Laptop A:

```bash
cd apps\web

# Install dependencies (first time only)
npm install

# Start web UI
npm run dev
```

**Wait for:** `ready - started server on 0.0.0.0:3000`

**Verify:** Open http://localhost:3000

---

## 🖥️ LAPTOP B SETUP (Worker Node)

This is your second laptop (or another machine on the network).

### Step 1: Get the Code

**Option A - Clone from GitHub:**
```bash
git clone https://github.com/tahirkhan05/hackathon-cluster-cloud.git
cd cluster_cloud
```

**Option B - Copy from Laptop A:**
- Copy the entire `apps/node-agent` folder to Laptop B via USB/network share
- Or use GitHub Desktop to clone

### Step 2: Create Environment File

Go to the node-agent folder and create a `.env` file:

```bash
cd apps\node-agent
```

Create a file named `.env` with this content (replace with YOUR Laptop A IP):

```bash
# CRITICAL: Replace with Laptop A's actual IP address
CONTROL_PLANE_URL=http://192.168.1.100:8000

# Node identity (optional - will auto-generate if not provided)
NODE_AGENT_ID=laptop-b-node

# Heartbeat settings
HEARTBEAT_INTERVAL_SECONDS=5

# Capacity
MAX_CONCURRENT_TASKS=2
COST_PER_TASK_CLSTR=10.0

# Logging
LOG_LEVEL=INFO
```

**Replace `192.168.1.100` with the IP you found in Laptop A Step 1!**

### Step 3: Install Dependencies

```bash
# Create virtual environment (first time only)
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Test Connection

Before starting the agent, test if Laptop B can reach Laptop A:

```bash
curl http://192.168.1.100:8000/health
```

**Expected:** `{"status":"healthy","service":"clustercloud-api"}`

**If this fails:**
- Check Laptop A firewall
- Verify both laptops on same network
- Try `ping 192.168.1.100` from Laptop B

### Step 5: Start Node Agent

```bash
python agent.py
```

**Expected output:**
```
🚀 ClusterCloud Node Agent - Phase 5 (Distributed Execution)
============================================================
Configuration loaded:
  Control Plane: http://192.168.1.100:8000
  Provider ID: laptop-b-node
  Heartbeat Interval: 5s
============================================================
Hardware discovery complete
============================================================
✓ Node registered: node-xxxxx
Task executor ready
============================================================
→ Heartbeat #1 sent successfully
→ Heartbeat #2 sent successfully
```

---

## ✅ VERIFICATION

### On Laptop A

**Check Web UI:**
1. Open http://localhost:3000/network
2. You should see **2 nodes**:
   - One local node (Laptop A)
   - One remote node (Laptop B) ✨

**Check API directly:**
```bash
curl http://localhost:8000/api/nodes
```
Should show array with 2 nodes.

### On Laptop B

**Check agent logs:**
- Should see "Heartbeat #N sent successfully" every 5 seconds
- Should see "Polling for tasks..." messages
- No error messages

---

## 🎬 RUN THE DEMO

### Step 1: Create a Job (from Laptop A)

**Option A - Web UI:**
1. Go to http://localhost:3000/build
2. Fill in:
   - Workload: 3D Rendering
   - Frames: 20
   - Deadline: 1 hour
   - Budget: 500 CLSTR
   - Reliability: 85%
3. Click "Get Recommendation"
4. Click "Build My Cloud"

**Option B - API:**
```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\": \"demo\", \"workload_type\": \"3d_rendering\", \"parameters\": {\"frame_count\": 20, \"resolution\": \"1920x1080\", \"deadline_minutes\": 60, \"budget_clstr\": 500}}"
```

### Step 2: Watch Execution

**On Laptop A (Web UI):**
- Go to http://localhost:3000/jobs
- Watch progress bar advance
- See tasks being distributed

**On Laptop B (Terminal):**
You'll see:
```
→ Received task: task-xxxxx
→ Starting task task-xxxxx
→ Starting frame 5
→ Rendering complete, uploading...
→ Task task-xxxxx completed successfully
```

**Rendered frames appear on Laptop B:**
```bash
# On Laptop B
dir rendered_frames
# Should see: frame_000001.png, frame_000002.png, etc.
```

### Step 3: Simulate Failure (The Cool Part!)

**Option A - Manual (Realistic):**

On Laptop B, press `Ctrl+C` to kill the node agent while tasks are running.

**Option B - Demo UI:**

1. On Laptop A, go to http://localhost:3000/demo
2. Click "Simulate Node Failure"
3. Select the Laptop B node
4. Click "Confirm"

### Step 4: Watch Recovery

**On Laptop A (Web UI):**

1. **Detection (< 15 seconds):**
   - Laptop B node turns RED
   - Status: UNHEALTHY

2. **Impact Analysis Panel Appears:**
   - Shows affected tasks
   - **Decision window countdown** (e.g., 01:14)
   - **DO NOTHING scenario:** 19min delay, 2 deadline breaches
   - **RECOVER NOW scenario:** 6min delay, 0 breaches
   - **Time saved:** 13 minutes
   - **AI explanation:** "Recovering now limits impact..."

3. **Click "EXECUTE RECOVERY":**
   - Tasks reassigned to remaining nodes
   - Job continues

4. **Job Completes:**
   - All frames rendered
   - Economic settlement shown

---

## 🐛 TROUBLESHOOTING

### Issue: Laptop B Can't Connect

**Symptom:** `Connection refused` or timeout

**Fixes:**

1. **Check Laptop A is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify IP address:**
   - Run `ipconfig` again on Laptop A
   - Make sure you used the correct IP in Laptop B's `.env`

3. **Check firewall:**
   - Temporarily disable Windows Firewall on Laptop A to test
   - If that works, add the rule properly

4. **Check network:**
   ```bash
   # From Laptop B
   ping 192.168.1.100
   ```
   Should get replies. If not, network issue.

5. **Verify backend binding:**
   - Make sure you used `--host 0.0.0.0`, not `--host localhost`
   - Restart backend with correct binding

### Issue: Node Registers but Gets No Tasks

**Symptom:** Node shows HEALTHY but never receives work

**Fixes:**

1. **Create a job first** - no tasks without a job
2. **Check node capacity:** Make sure `current_task_count < max_concurrent_tasks`
3. **Check job is running:** Go to /jobs, verify status is RUNNING

### Issue: Firewall Still Blocking

**Symptom:** Everything else works but Laptop B can't connect

**Quick test:**
```powershell
# On Laptop A (as Administrator)
netsh advfirewall set allprofiles state off
```

If Laptop B connects now, it's definitely the firewall. Add the rule properly, then:
```powershell
netsh advfirewall set allprofiles state on
```

### Issue: Wrong Python Version

**Symptom:** Import errors or syntax errors

**Fix:**
```bash
python --version
# Should be 3.11 or higher

# If not, try:
python3 --version
python3.11 --version

# Use the right one
python3.11 -m venv venv
```

---

## 🎯 Quick Reference Card

**Print this and keep visible:**

```
┌─────────────────────────────────────────┐
│      TWO-LAPTOP DEMO QUICK REF          │
├─────────────────────────────────────────┤
│ LAPTOP A (Control Plane)                │
│   1. Find IP: ipconfig                  │
│   2. Allow port 8000 in firewall        │
│   3. cd apps\api                        │
│   4. python -m uvicorn main:app \       │
│      --host 0.0.0.0 --port 8000         │
│   5. Open http://localhost:3000         │
├─────────────────────────────────────────┤
│ LAPTOP B (Worker Node)                  │
│   1. cd apps\node-agent                 │
│   2. Create .env with:                  │
│      CONTROL_PLANE_URL=http://IP:8000   │
│   3. python -m venv venv                │
│   4. venv\Scripts\activate              │
│   5. pip install -r requirements.txt    │
│   6. python agent.py                    │
├─────────────────────────────────────────┤
│ VERIFY                                  │
│   Laptop A: curl http://IP:8000/health  │
│   Laptop B: curl http://IP:8000/health  │
│   Web UI: http://localhost:3000/network │
│   Should see: 2 nodes HEALTHY           │
├─────────────────────────────────────────┤
│ DEMO                                    │
│   1. Create job (20 frames)            │
│   2. Watch distributed execution       │
│   3. Kill Laptop B (Ctrl+C)            │
│   4. Watch impact analysis             │
│   5. Click EXECUTE RECOVERY            │
│   6. Job completes successfully        │
└─────────────────────────────────────────┘
```

---

## 📝 Environment Variables Summary

### Laptop A (.env in apps/api) - Optional

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./clustercloud.db

# Security (Development - disabled for demo)
ENABLE_NODE_AUTH=false
ENABLE_DEMO_ENDPOINTS=true

# AWS Bedrock (Optional - for AI features)
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret

# Resource Limits
MAX_TASK_MEMORY_MB=2048
MAX_TASK_CPU_CORES=2.0
TASK_TIMEOUT_SECONDS=120
```

### Laptop B (.env in apps/node-agent) - REQUIRED

```bash
# CRITICAL: Replace with Laptop A's IP
CONTROL_PLANE_URL=http://192.168.1.100:8000

# Node identity (optional)
NODE_AGENT_ID=laptop-b-node

# API Key (only if ENABLE_NODE_AUTH=true on backend)
# NODE_AGENT_API_KEY=dev-node-agent-key

# Capacity
MAX_CONCURRENT_TASKS=2
COST_PER_TASK_CLSTR=10.0

# Heartbeat
HEARTBEAT_INTERVAL_SECONDS=5

# Logging
LOG_LEVEL=INFO
```

---

## 🔥 Common Mistakes to Avoid

1. ❌ **Using `localhost` in CONTROL_PLANE_URL**
   - ✅ Use actual IP: `http://192.168.1.100:8000`

2. ❌ **Backend bound to localhost**
   - ✅ Use: `--host 0.0.0.0`

3. ❌ **Firewall blocking port 8000**
   - ✅ Add firewall rule for port 8000

4. ❌ **Different WiFi networks**
   - ✅ Both laptops on same network

5. ❌ **Not activating virtual environment**
   - ✅ Run `venv\Scripts\activate` first

6. ❌ **Wrong Python version**
   - ✅ Use Python 3.11+

---

## ✨ Success Checklist

Before demo:
- [ ] Laptop A IP known (e.g., 192.168.1.100)
- [ ] Firewall on Laptop A allows port 8000
- [ ] Backend running with `--host 0.0.0.0`
- [ ] Can curl health check from Laptop B
- [ ] Frontend running on Laptop A
- [ ] Laptop B node agent starts successfully
- [ ] Web UI shows 2 nodes HEALTHY
- [ ] Can create job and see distributed execution
- [ ] Killing Laptop B triggers impact analysis
- [ ] Recovery executes successfully

**If all checked: YOU'RE READY TO DEMO! 🎉**

---

## 📚 More Help

- **Detailed Setup:** See [docs/RUN_INSTRUCTIONS.md](docs/RUN_INSTRUCTIONS.md)
- **Demo Script:** See [docs/DEMO_CHECKLIST.md](docs/DEMO_CHECKLIST.md)
- **Troubleshooting:** See [docs/DEMO_FALLBACK.md](docs/DEMO_FALLBACK.md)
- **Architecture:** See [docs/FINAL_ARCHITECTURE.md](docs/FINAL_ARCHITECTURE.md)

---

**You got this! 🚀 Now go demo the world's smartest distributed cloud!**
