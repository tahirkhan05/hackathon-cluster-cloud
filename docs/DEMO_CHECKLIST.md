# ClusterCloud - Demo Checklist

**Demo Duration:** 8 minutes  
**Format:** Live execution with manual failure trigger  
**Audience:** Hackathon judges

---

## Pre-Demo Setup (30 Minutes Before)

### 1. Environment Check

```bash
# Verify all services installed
python --version    # 3.11+
node --version      # 18+
docker --version    # 20+

# Check disk space (minimum 2GB free)
df -h

# Check network connectivity
ping google.com
```

### 2. Start Backend

```bash
cd apps/api

# Clear old database for fresh demo
rm clustercloud.db 2>/dev/null

# Start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Wait for: "Application startup complete"
# Verify: curl http://localhost:8000/health
```

**Expected Output:**
```json
{"status":"healthy","service":"clustercloud-api"}
```

### 3. Start Frontend

```bash
cd apps/web

# Start Next.js
npm run dev

# Wait for: "ready - started server on 0.0.0.0:3000"
# Verify: Open http://localhost:3000
```

**Expected:** Landing page loads successfully

### 4. Start Node Agents (3 Nodes Minimum)

```bash
# Terminal 1
cd apps/node-agent
python agent.py
# Wait for: "Node registered: node-xxxxx"

# Terminal 2
cd apps/node-agent
python agent.py
# Wait for: "Node registered: node-yyyyy"

# Terminal 3
cd apps/node-agent
python agent.py
# Wait for: "Node registered: node-zzzzz"
```

**Verify Nodes:**
```bash
curl http://localhost:8000/api/nodes | jq length
# Expected: 3
```

### 5. Pre-Load Demo Page

```bash
# Open in browser
open http://localhost:3000/demo

# Verify all elements visible:
# ✓ "Start Demo Job" button
# ✓ "Simulate Node Failure" button (disabled)
# ✓ Network visualization
# ✓ Job status panel
```

### 6. Test WebSocket Connection

**Browser Console (F12):**
```javascript
// Should see WebSocket connected
// Network tab → WS filter → Status: 101
```

**Look for:**
- ✓ Green "Live" indicator in header
- ✓ No console errors
- ✓ Nodes showing HEALTHY status

### 7. Final Verification

**Checklist:**
- [ ] Backend health: `curl http://localhost:8000/health` returns 200
- [ ] Frontend loads: http://localhost:3000 shows landing
- [ ] 3 nodes registered: http://localhost:3000/network shows 3 HEALTHY
- [ ] WebSocket connected: Green "Live" indicator
- [ ] Demo page ready: http://localhost:3000/demo loads
- [ ] Browser window clean (no other tabs visible)
- [ ] Terminal windows organized and visible
- [ ] Zoom/screen share ready

---

## During Demo (8 Minutes)

### Minute 0-1: Introduction

**Script:**
> "ClusterCloud is a distributed rendering platform that automatically handles cluster composition, failure recovery, and economic settlement. Let me show you."

**Action:**
- Show landing page (http://localhost:3000)
- Highlight: "Build My Cloud" button

### Minute 1-2: Job Creation

**Action:**
1. Click "Build My Cloud"
2. Fill form:
   - **Type:** 3D Rendering
   - **Frames:** 20
   - **Deadline:** 1 hour
   - **Budget:** 500 CLSTR
   - **Reliability:** 85%
3. Click "Get Recommendation"

**Script:**
> "The system uses AI to analyze the workload, then deterministically selects the optimal nodes based on reliability, cost, and capacity."

**Expected:**
- AI analysis appears (~2 seconds)
- Node recommendations shown
- "Build My Cloud" button enabled

**Action:**
4. Click "Build My Cloud"
5. Navigate to `/demo` page

### Minute 2-4: Live Execution

**Script:**
> "Tasks are now executing across multiple nodes. Watch the real-time updates."

**Show:**
- Job status: RUNNING
- Task distribution across 3 nodes
- Progress bar advancing
- Live event feed

**Expected:**
- Tasks completing every 3-5 seconds
- Progress: 0% → 30-50%
- Multiple tasks in RUNNING state

### Minute 4-6: Failure Simulation

**Script:**
> "Now let's simulate a node failure—this is the critical moment. Watch what happens."

**Action:**
1. Click "Simulate Node Failure" button
2. Select a node with active tasks
3. Click "Confirm"

**Expected (within 15 seconds):**
1. ✓ Selected node turns RED (UNHEALTHY)
2. ✓ Incident created (incident panel appears)
3. ✓ "Recovery in progress..." message
4. ✓ Affected tasks identified
5. ✓ AI recovery decision displayed
6. ✓ Tasks reassigned to healthy node
7. ✓ Recovery complete message

**Highlight:**
- Failed node visualization
- Affected task count
- AI reasoning for recovery
- New node selection
- Economic transactions

### Minute 6-7: Economic Settlement

**Script:**
> "Notice the economic system in action. The failed provider is penalized, the customer is compensated, and the replacement provider is rewarded—all automatically."

**Show:**
- Navigate to `/dashboard` → Economic tab
- Point out:
  - Provider penalty: -20 CLSTR
  - Customer compensation: +15 CLSTR
  - Recovery reward: +10 CLSTR
  - Ledger entries (immutable)

### Minute 7-8: Job Completion

**Script:**
> "The job continues to completion despite the failure. This is true self-healing infrastructure."

**Show:**
- Job status: RUNNING → COMPLETED
- All 20 frames rendered
- Total execution time
- Final cost settlement

**Closing:**
> "Questions?"

---

## Troubleshooting During Demo

### Issue: Job Not Starting

**Symptom:** Click "Build My Cloud" → nothing happens

**Fix:**
1. Check browser console for errors
2. Verify backend running: `curl http://localhost:8000/health`
3. Check WebSocket: Look for green "Live" indicator
4. Fallback: Restart backend and retry

**Recovery Time:** 30 seconds

### Issue: No Nodes Available

**Symptom:** "No compatible nodes found"

**Fix:**
1. Check nodes: `curl http://localhost:8000/api/nodes`
2. If empty: Restart node agents
3. Wait 10 seconds for registration

**Recovery Time:** 15 seconds

### Issue: Failure Button Disabled

**Symptom:** "Simulate Node Failure" button grayed out

**Cause:** No active job with running tasks

**Fix:**
1. Wait for tasks to start executing
2. Check job status is RUNNING
3. Ensure at least one task is ASSIGNED or RUNNING

**Recovery Time:** Immediate (just wait)

### Issue: WebSocket Disconnected

**Symptom:** Red "Disconnected" indicator

**Fix:**
1. Backend still running? Check terminal
2. Refresh browser page (F5)
3. WebSocket auto-reconnects in 5 seconds

**Recovery Time:** 5-10 seconds

### Issue: Tasks Not Completing

**Symptom:** Progress stuck at 0%

**Fix:**
1. Check node agent terminals for errors
2. Verify nodes polling: Should see "Polling for tasks..."
3. Check backend logs: Look for task assignment messages

**Recovery Time:** N/A (restart demo)

### Issue: Recovery Fails

**Symptom:** "Recovery failed" message after failure simulation

**Cause:** No healthy nodes with capacity

**Fix:**
1. Check available nodes: `curl http://localhost:8000/api/nodes`
2. Start additional node agent
3. Retry failure simulation

**Recovery Time:** 20 seconds

---

## Fallback Procedures

### Level 1: Quick Fix (< 30 seconds)

**Issue:** Minor UI glitch, WebSocket disconnect

**Action:**
1. Refresh browser (F5)
2. Wait for WebSocket reconnect
3. Continue demo

**Use When:** UI out of sync but backend working

### Level 2: Service Restart (< 2 minutes)

**Issue:** Backend error, database lock, service crash

**Action:**
1. **Apologize:** "Let me restart the service quickly."
2. Stop backend (Ctrl+C)
3. Restart: `python -m uvicorn main:app --reload`
4. Wait for "Application startup complete"
5. Refresh browser
6. Resume demo (nodes auto-reconnect)

**Use When:** Backend errors but database intact

### Level 3: Full Reset (< 5 minutes)

**Issue:** Database corruption, state inconsistency

**Action:**
1. **Apologize:** "Let me reset to a clean state."
2. Stop all services (Ctrl+C on all terminals)
3. Remove database: `rm apps/api/clustercloud.db`
4. Restart backend
5. Restart node agents
6. Refresh browser
7. Start from beginning

**Use When:** Unrecoverable state errors

### Level 4: Slide Deck (Immediate)

**Issue:** Complete system failure, no recovery possible

**Action:**
1. **Switch to slides:** "Let me show you the architecture while we troubleshoot."
2. Show architecture diagram
3. Explain system design
4. Walk through code (if judges interested)
5. Answer questions

**Use When:** No time to fix technical issues

**Have Ready:**
- PDF slides with architecture
- Screenshots of working demo
- Screen recording of successful run

---

## Post-Demo

### Immediate (During Q&A)

**Common Questions & Answers:**
1. **"How does AI work here?"**
   - AWS Bedrock (Claude 3.5 Sonnet)
   - Workload analysis and recovery decisions
   - Always validated by deterministic scheduler

2. **"Is this production-ready?"**
   - MVP ready for hackathon
   - Need: authentication, TLS, PostgreSQL, monitoring
   - See SECURITY.md for hardening checklist

3. **"Can it scale?"**
   - Tested: 10 nodes, 100 tasks
   - Architecture supports: 100+ nodes
   - Bottleneck: SQLite (use PostgreSQL for scale)

4. **"What happens if control plane fails?"**
   - Nodes continue executing assigned tasks
   - Need: HA control plane (multiple replicas)
   - Add: health checks and failover

### Later (After Presentation)

**Cleanup:**
```bash
# Stop all services
pkill -INT python node

# Optional: Clear database
rm apps/api/clustercloud.db

# Optional: Archive demo state
cp apps/api/clustercloud.db backups/demo-$(date +%s).db
```

**Review:**
- [ ] Save any judge feedback
- [ ] Note any technical issues encountered
- [ ] Update documentation if needed
- [ ] Commit any last-minute fixes

---

## Practice Run Checklist

**Do This 24 Hours Before:**

1. [ ] Full setup from scratch
2. [ ] Time each demo segment
3. [ ] Practice failure simulation 3 times
4. [ ] Test all fallback procedures
5. [ ] Record backup screen capture
6. [ ] Prepare 3 different failure scenarios
7. [ ] Test with different node counts (3, 5, 7)
8. [ ] Practice Q&A responses
9. [ ] Test on presentation laptop/environment
10. [ ] Have backup machine ready

**Time Goal:** Complete setup in < 5 minutes

---

## Emergency Contacts

**Technical Issues:**
- GitHub: https://github.com/tahirkhan05/hackathon-cluster-cloud
- Issues: Check existing issues for known bugs

**Demo Assets:**
- Live URL: http://localhost:3000/demo
- API Docs: http://localhost:8000/docs
- Architecture: docs/FINAL_ARCHITECTURE.md

---

**Good luck! 🚀**
