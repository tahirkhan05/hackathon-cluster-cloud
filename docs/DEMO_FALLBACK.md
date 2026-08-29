# ClusterCloud - Demo Fallback Procedures

**Purpose:** Recover from technical failures during live demo  
**Priority:** Minimize downtime, maintain judge confidence  
**Max Recovery Time:** 2 minutes

---

## Failure Classification

### Green (Minor) - Continue Demo
- UI visual glitch
- WebSocket brief disconnect
- Single task failure

**Action:** Continue, mention it's self-healing

### Yellow (Moderate) - Quick Fix Required
- WebSocket won't reconnect
- Job won't start
- Node won't register

**Action:** Apply Level 1 or 2 fix (see below)

### Red (Critical) - Use Fallback
- Backend crash
- Database corruption
- Multiple cascading failures

**Action:** Switch to fallback mode immediately

---

## Level 1: Browser Refresh (10 seconds)

### When to Use
- UI frozen or out of sync
- WebSocket shows disconnected but backend running
- Demo page not loading properly

### Procedure

1. **Acknowledge:**
   > "Let me refresh the view..."

2. **Action:**
   ```bash
   # In browser: F5 or Cmd+R
   ```

3. **Verify:**
   - Green "Live" indicator appears
   - Nodes show correct status
   - Job status updates

4. **Continue:**
   > "And we're back. As you can see..."

### Recovery Time: 10 seconds

---

## Level 2: Backend Quick Restart (30 seconds)

### When to Use
- Backend error in terminal
- 500 Internal Server Error
- API endpoints not responding
- WebSocket won't establish

### Procedure

1. **Acknowledge:**
   > "I'm seeing a connection issue. Let me restart the service—this simulates a control plane failover."

2. **Action:**
   ```bash
   # Terminal with backend:
   Ctrl+C
   
   # Restart immediately:
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   
   # Wait for:
   # "Application startup complete"
   ```

3. **Browser:**
   ```bash
   # Refresh: F5
   # Wait for WebSocket reconnect (automatic)
   ```

4. **Verify:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

5. **Continue:**
   > "Nodes automatically reconnect. Let's continue where we left off."

### Recovery Time: 30 seconds

### Notes
- Database persists (job state preserved)
- Nodes auto-reconnect
- Can resume mid-demo

---

## Level 3: Full System Reset (2 minutes)

### When to Use
- Database locked or corrupted
- State inconsistency (wrong task counts, etc.)
- Multiple services crashed
- Level 2 didn't fix the issue

### Procedure

1. **Acknowledge:**
   > "Let me do a full reset to demonstrate from a clean state."

2. **Stop All Services:**
   ```bash
   # Backend terminal: Ctrl+C
   # Frontend terminal: Ctrl+C  
   # Node agent terminals: Ctrl+C (all)
   ```

3. **Clean State:**
   ```bash
   # Remove database
   cd apps/api
   rm clustercloud.db
   ```

4. **Restart Backend:**
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   # Wait: "Application startup complete"
   ```

5. **Restart Frontend:**
   ```bash
   cd apps/web
   npm run dev
   # Wait: "ready - started server"
   ```

6. **Restart Nodes (3x):**
   ```bash
   cd apps/node-agent
   python agent.py  # In 3 separate terminals
   # Wait for registration messages
   ```

7. **Verify:**
   ```bash
   curl http://localhost:8000/api/nodes | jq length
   # Expected: 3
   ```

8. **Continue:**
   > "Now let's start the demo. This is a fresh environment..."

### Recovery Time: 2 minutes

### Notes
- All state lost (start demo from beginning)
- Fastest way to recover from corruption
- Practice this procedure beforehand

---

## Level 4: Slides + Code Walkthrough (Immediate)

### When to Use
- No time to fix (< 3 minutes left in presentation)
- Cascading failures
- Infrastructure unavailable (WiFi down, etc.)
- System completely unrecoverable

### Procedure

1. **Acknowledge:**
   > "Rather than troubleshoot, let me show you the architecture and code directly."

2. **Switch to Slides:**
   - Open `docs/FINAL_ARCHITECTURE.md` in browser
   - Or: Pre-prepared PDF slides

3. **Show Architecture:**
   > "Here's the system design. We have three layers..."
   
   **Cover:**
   - Control plane (FastAPI)
   - Node agents (Python)
   - Frontend (Next.js)
   - Key workflows

4. **Code Walkthrough:**
   ```bash
   # Open in VS Code or editor
   code apps/api/domains/recovery/recovery_service.py
   ```
   
   > "This is the recovery service. When a node fails..."
   
   **Highlight:**
   - Recovery algorithm (line 50-100)
   - Node selection logic
   - Economic settlement

5. **Show Test Results:**
   ```bash
   # If tests exist and pass
   pytest apps/api/test_recovery.py -v
   ```

6. **Backup Video:**
   - If available: Play pre-recorded demo
   - Show successful execution
   - Narrate what's happening

### Recovery Time: Immediate

### Notes
- Keep judge engagement high
- Focus on technical depth
- Demonstrate understanding of code
- Show engineering decisions

---

## Specific Failure Scenarios

### Scenario 1: No Nodes Register

**Symptom:**
- Start node agents
- No nodes appear in `/network`

**Diagnosis:**
```bash
# Check backend health
curl http://localhost:8000/health

# Check node agent terminal for errors
# Look for: Connection refused, 404, etc.
```

**Fix:**
```bash
# Option A: Backend not running
# Start backend first, then nodes

# Option B: Wrong CONTROL_PLANE_URL
export CONTROL_PLANE_URL=http://localhost:8000
python agent.py

# Option C: Registration endpoint broken
# Check backend logs for errors
```

**Fallback:** Use Level 2 (Backend Restart)

---

### Scenario 2: Job Won't Start

**Symptom:**
- Click "Build My Cloud"
- Job never appears or stuck in SUBMITTED

**Diagnosis:**
```bash
# Check jobs
curl http://localhost:8000/api/jobs

# Check backend terminal for errors
# Look for: AI errors, scheduling errors
```

**Fix:**
```bash
# Option A: AI service unavailable
# Check AWS credentials
# Fallback: AI has fallback logic, should still work

# Option B: No nodes available
curl http://localhost:8000/api/nodes
# If empty: Start node agents

# Option C: Browser cache
# Hard refresh: Ctrl+Shift+R
```

**Fallback:** Use Level 3 (Full Reset)

---

### Scenario 3: Tasks Don't Execute

**Symptom:**
- Job status: RUNNING
- Tasks stay in ASSIGNED state
- Progress: 0%

**Diagnosis:**
```bash
# Check nodes polling
# Node agent terminal should show:
# "Polling for tasks..."

# Check task assignment
curl http://localhost:8000/api/jobs/{job_id}/tasks
```

**Fix:**
```bash
# Option A: Nodes not polling
# Restart node agents

# Option B: Task execution error
# Check node agent terminal for exceptions

# Option C: Docker not available
# Check Docker daemon: docker ps
# Or disable Docker: Set ENABLE_DOCKER_ISOLATION=false
```

**Fallback:** Use Level 2 (Backend Restart) + restart nodes

---

### Scenario 4: Failure Simulation Doesn't Work

**Symptom:**
- Click "Simulate Node Failure"
- Nothing happens or error message

**Diagnosis:**
```bash
# Check demo endpoint
curl -X POST http://localhost:8000/api/demo/simulate-failure/{node_id}

# Check backend logs
# Look for: DEMO: Simulating failure...
```

**Fix:**
```bash
# Option A: No active tasks
# Wait for tasks to start executing
# Job must be in RUNNING state

# Option B: Node already failed
# Check node status: must be HEALTHY
# Reset: POST /api/demo/reset

# Option C: Recovery service error
# Check backend logs for stack trace
```

**Fallback:** 
1. Explain what *would* happen
2. Show code in `recovery_service.py`
3. Show economic ledger logic
4. Use Level 4 (Slides)

---

### Scenario 5: WebSocket Won't Connect

**Symptom:**
- Red "Disconnected" indicator
- No real-time updates
- Network tab shows WS failed

**Diagnosis:**
```bash
# Check WebSocket endpoint
curl http://localhost:8000/ws/events
# Should return: 426 Upgrade Required (this is correct)

# Check browser console
# Look for: WebSocket connection errors
```

**Fix:**
```bash
# Option A: Backend WebSocket not enabled
# Should be enabled by default
# Check main.py for WebSocket route

# Option B: CORS issue
# Check backend CORS configuration
# Should allow localhost:3000

# Option C: Browser issue
# Try different browser
# Clear cache and reload
```

**Fallback:** Continue without real-time updates, manually refresh

---

## Pre-Demo Preparation

### Backup Assets

**Create Before Demo:**

1. **Database Snapshot:**
   ```bash
   # Create working state
   # Start services, create demo job
   # Stop before completion
   cp apps/api/clustercloud.db backups/demo-ready.db
   
   # Restore if needed:
   cp backups/demo-ready.db apps/api/clustercloud.db
   ```

2. **Screen Recording:**
   ```bash
   # Record successful demo run
   # Save as: demo-backup.mp4
   # Use if live demo fails
   ```

3. **Architecture Slides:**
   ```bash
   # Convert FINAL_ARCHITECTURE.md to PDF
   # Have open in background tab
   ```

4. **Code Snippets:**
   ```bash
   # Prepare gists or files with:
   # - Recovery algorithm
   # - AI prompts
   # - Economic logic
   # - Task scheduling
   ```

### Emergency Scripts

**Create: `demo-reset.sh`**
```bash
#!/bin/bash
# Emergency demo reset script

echo "Stopping all services..."
pkill -INT python node

echo "Cleaning state..."
rm apps/api/clustercloud.db

echo "Starting backend..."
cd apps/api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

sleep 5

echo "Starting node agents..."
cd apps/node-agent
python agent.py &
python agent.py &
python agent.py &

echo "Done! Refresh browser and start demo."
```

**Create: `demo-check.sh`**
```bash
#!/bin/bash
# Quick health check script

echo "=== Backend Health ==="
curl -s http://localhost:8000/health | jq

echo "=== Registered Nodes ==="
curl -s http://localhost:8000/api/nodes | jq length

echo "=== Active Jobs ==="
curl -s http://localhost:8000/api/jobs | jq length

echo "=== System Stats ==="
curl -s http://localhost:8000/api/stats | jq
```

---

## Confidence Recovery

### Judge Perception Management

**If Level 1-2 Fix:**
> "You can see the system automatically recovers. This resilience is built into the architecture."

**If Level 3 Fix:**
> "Let me show you from a clean state. In production, we'd have automated health checks and restarts."

**If Level 4 Fallback:**
> "Rather than debug live, let me show you the engineering decisions and code architecture directly."

### Maintain Authority

**DO:**
- Stay calm and confident
- Explain what you're doing
- Use as learning opportunity
- Show code and architecture
- Answer questions during fix

**DON'T:**
- Panic or apologize excessively
- Blame tools or environment
- Make excuses
- Go silent while debugging
- Give up

### Turn It Into a Feature

**Script:**
> "This actually demonstrates an important point. In distributed systems, failures happen. What matters is how quickly you detect and recover—which is exactly what ClusterCloud does automatically."

---

## Post-Failure Analysis

### After Demo Completes

**Document:**
1. What failed?
2. Why did it fail?
3. How was it fixed?
4. How to prevent in future?

**Update:**
- This document
- Pre-demo checklist
- Known issues list

**Practice:**
- Recreate failure
- Test fix procedure
- Time recovery
- Improve scripts

---

## Quick Reference Card

**Print and keep visible during demo:**

```
┌─────────────────────────────────────────────┐
│        DEMO FALLBACK QUICK REFERENCE        │
├─────────────────────────────────────────────┤
│ Level 1: Browser Refresh (F5)    10s       │
│ Level 2: Backend Restart          30s       │
│ Level 3: Full Reset               2min      │
│ Level 4: Slides/Code              NOW       │
├─────────────────────────────────────────────┤
│ Backend Health:                             │
│   curl http://localhost:8000/health         │
│                                             │
│ Quick Reset:                                │
│   ./demo-reset.sh                           │
│                                             │
│ Emergency Slides:                           │
│   docs/FINAL_ARCHITECTURE.md                │
│                                             │
│ Backup Video:                               │
│   demo-backup.mp4                           │
└─────────────────────────────────────────────┘
```

---

**Stay calm. You've got this. 🚀**
