# ClusterCloud Hackathon Demo Script

**Target Duration:** 8 minutes  
**Audience:** Hackathon judges and attendees  
**Goal:** Demonstrate complete distributed cloud with automatic failure recovery

---

## Pre-Demo Setup (5 minutes before)

### 1. Start Backend
```bash
cd apps/api
uvicorn main:app --reload
# Should be running on http://localhost:8000
```

### 2. Start Frontend
```bash
cd apps/web
npm run dev
# Should be running on http://localhost:3000
```

### 3. Start Node Agents (3 nodes)
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

### 4. Verify Setup
- Open http://localhost:3000/demo
- Verify all 3 nodes show as HEALTHY
- Clear any old jobs/incidents

---

## Demo Flow (8 minutes)

### **MINUTE 0-1: Introduction & Problem Statement**

**What to say:**
> "Traditional cloud platforms force you to be a systems engineer. You need to know instance types, availability zones, auto-scaling groups... it's complex and error-prone.
>
> ClusterCloud flips this model. You tell us WHAT you want to render, and we handle EVERYTHING else. No Kubernetes. No AWS Console. Just simple English."

**What to show:**
- Open http://localhost:3000
- Show landing page briefly
- Navigate to /demo

---

### **MINUTE 1-2: Customer Request**

**What to say:**
> "Let's say I'm a 3D artist. I have 20 frames to render, and I need them in an hour. I have 500 CLSTR tokens. How reliable should it be? 85%."

**What to do:**
1. Click "Start Demo Job"
2. Show the job creation form (if using /build instead)
3. Fill in:
   - Workload: 3D Rendering
   - Frames: 20
   - Deadline: 1 hour
   - Budget: 500 CLSTR
   - Reliability: 85%

**What to say:**
> "That's it. Four questions. No EC2 instances. No YAML files."

---

### **MINUTE 2-3: AI Analysis & Cluster Composition**

**What to show:**
- Job created
- Status shows "ANALYZING" then "SCHEDULING"
- Point to the Activity Feed showing real-time events

**What to say:**
> "Behind the scenes, our AI analyzes the workload. How much compute? How long per frame? What deadline pressure?
>
> Then it composes the perfect cluster. It looks at available nodes, their reliability scores, their costs, and picks the optimal set. All automatic."

**What to point out in Activity Feed:**
- "Node selected" events
- "Task assigned" events

---

### **MINUTE 3-4: Live Distributed Execution**

**What to show:**
- Job progress bar filling up
- Frames completing in real-time
- Activity feed showing "task_completed" events
- Network nodes showing activity

**What to say:**
> "Now watch the distributed execution. Tasks are being assigned to multiple nodes. They're rendering frames in parallel. This is REAL computation happening across multiple machines.
>
> Notice the progress bar updating in real-time. No refresh needed. WebSockets push every event instantly."

**Let this run for ~30 seconds so progress reaches 30-40%**

---

### **MINUTE 4-5: THE DRAMA - Node Failure**

**What to say:**
> "Here's where it gets interesting. In distributed systems, failures are inevitable. Nodes crash. Networks partition. Hardware fails.
>
> Traditional clouds? You're on your own. Configure auto-scaling. Set up health checks. Hope your YAML is right.
>
> Watch what ClusterCloud does."

**What to do:**
1. Click "Simulate Node Failure" button
2. Confirm the dialog

**What to show immediately:**
- Node status changes from HEALTHY to UNHEALTHY (red)
- Incident card appears with "Node Failure Detected"
- Failed tasks count
- System pauses briefly

**What to say:**
> "Within seconds, ClusterCloud detected the failure. It identified which tasks were affected. And now... watch the recovery."

---

### **MINUTE 5-6: AI Recovery Decision**

**What to show:**
- Incident Recovery Visualization card
- Failed node on left (red)
- AI reasoning box appears

**What to say:**
> "Our AI Recovery Agent analyzes the situation. It looks at:
> - Which tasks failed
> - What the remaining deadline is
> - Which nodes are still healthy
> - Each node's reliability score
> - The budget constraints
>
> And it makes a decision."

**What to point out in the AI reasoning box:**
Read the actual AI reasoning aloud. It will say something like:
> "Node worker-1 failed with 3 tasks in progress. Selected worker-2 as replacement based on high reliability (0.92) and sufficient capacity. Estimated recovery time: 45 seconds."

**What to say:**
> "The AI chose a replacement node. Not randomly. Based on data. Based on reliability history. This is intelligent infrastructure."

---

### **MINUTE 6-7: Automatic Reassignment**

**What to show:**
- Replacement node appears on right (blue/green)
- Progress indicator showing "Reassigning tasks"
- Activity feed showing:
  - "replacement_selected"
  - "task_assigned" (to new node)
  - "task_completed" (on new node)
- Job progress bar continues filling

**What to say:**
> "Tasks are automatically reassigned to the replacement node. No human intervention. No downtime. The job continues.
>
> The customer doesn't have to do anything. They don't even need to know there was a failure. The system handled it."

**Let recovery complete - watch progress bar continue**

---

### **MINUTE 7-8: Economic Settlement & Completion**

**What to show:**
- Incident status changes to "RESOLVED"
- Economic Settlement section appears
- Show three numbers:
  - Provider Penalty: -20 CLSTR
  - Customer Compensation: +15 CLSTR
  - Recovery Reward: +10 CLSTR

**What to say:**
> "And here's the economics. This isn't just infrastructure. It's a marketplace.
>
> The failed provider? Penalized. They staked tokens when they joined. 20 CLSTR penalty.
>
> The customer? Compensated. 15 CLSTR refunded for the inconvenience.
>
> The replacement provider who saved the day? Rewarded. 10 CLSTR bonus on top of their normal payment.
>
> Every action is recorded. Every token movement is auditable. Complete transparency."

**What to show:**
- Job completes (100% progress)
- Final status: COMPLETED
- Total cost breakdown

**What to say:**
> "Job complete. 20 frames rendered. Distributed across multiple nodes. Automatic failure recovery. Fair economic settlement. All in under 2 minutes.
>
> The customer asked for 3D rendering. We delivered 3D rendering. Everything else? Handled automatically."

---

## Closing (30 seconds)

**What to say:**
> "ClusterCloud is distributed computing made simple. You focus on creating. We handle the infrastructure.
>
> No Kubernetes. No AWS Console. No YAML files.
>
> Just: What do you want to render? We'll build your cloud."

**What to show:**
- Navigate back to dashboard
- Show final statistics
- Point to live activity feed still updating

**End with:**
> "Thank you. Questions?"

---

## Key Talking Points

### 1. **Customer-First UX**
- "What are you rendering?" not "What instance type?"
- 4 questions vs 40 configuration parameters
- Plain English, not cloud jargon

### 2. **AI-Driven**
- Workload analysis is AI
- Cluster composition is AI
- Recovery decisions are AI
- But validated by deterministic logic (not blind trust)

### 3. **Distributed Execution**
- Real parallelism across nodes
- Real-time progress updates
- WebSocket event streaming

### 4. **Automatic Recovery**
- Failure detection in seconds
- AI chooses replacement
- Tasks automatically reassigned
- Job continues without customer action

### 5. **Economic Fairness**
- Penalties for failures
- Compensation for customers
- Rewards for recoverers
- Complete transparency
- Auditable ledger

### 6. **Real Technology**
- FastAPI backend
- React/Next.js frontend
- Docker isolation
- WebSocket real-time
- AWS Bedrock AI
- SQLite/PostgreSQL database

---

## Backup Slides / Fallback

### If Demo Breaks

**Have ready:**
- Video recording of successful demo
- Architecture diagram
- Code snippets showing key features

### If Questions Come Up

**Technical:**
- "How does scheduling work?" → Deterministic scoring algorithm
- "How does AI work?" → AWS Bedrock with structured outputs
- "How do you handle security?" → Docker isolation, resource limits, see SECURITY.md
- "How do economics work?" → Immutable ledger, every transaction recorded

**Business:**
- "Who is this for?" → Content creators, 3D artists, video editors
- "Why not AWS?" → AWS is for engineers, ClusterCloud is for creators
- "What's next?" → GPU support, Blender integration, real money settlements

---

## Common Issues & Fixes

### Nodes Not Registering
```bash
# Check control plane is running
curl http://localhost:8000/health

# Restart node agents
cd apps/node-agent
python agent.py
```

### Job Not Starting
- Check nodes are HEALTHY in /network
- Check customer balance in /balance
- Check logs: `tail -f apps/api/*.log`

### Failure Simulation Not Working
- Ensure job is RUNNING (not COMPLETED)
- Ensure selected node is HEALTHY
- Check browser console for errors
- Verify demo endpoint: `curl -X POST http://localhost:8000/api/demo/status`

### WebSocket Not Connecting
- Check /ws/events endpoint: open browser DevTools Network tab
- Restart backend if needed
- Clear browser cache

---

## Demo Success Criteria

✅ **Must Show:**
1. Job creation in seconds
2. Distributed execution across multiple nodes
3. Real-time progress updates
4. Node failure simulation
5. Automatic recovery
6. Economic settlement
7. Job completion

✅ **Must Emphasize:**
1. Customer-first UX (no cloud jargon)
2. AI-driven decisions (but validated)
3. Automatic recovery (no human needed)
4. Economic fairness (penalties & rewards)
5. Real technology (not smoke and mirrors)

✅ **Must Avoid:**
1. Technical jargon (unless asked)
2. Dwelling on failures
3. Apologizing for "just a hackathon project"
4. Overselling capabilities
5. Ignoring the UI (show, don't just talk)

---

## Time Management

| Minute | Content |
|--------|---------|
| 0-1 | Introduction & problem |
| 1-2 | Customer request |
| 2-3 | AI analysis & cluster composition |
| 3-4 | Live distributed execution |
| 4-5 | Node failure (THE DRAMA) |
| 5-6 | AI recovery decision |
| 6-7 | Automatic reassignment |
| 7-8 | Economic settlement & completion |

**Total: 8 minutes**

Practice to stay on time. Aim for 7:30 to leave buffer for questions.

---

## Post-Demo

### If Judges Want to Try
1. Let them click "Simulate Node Failure"
2. Let them explore the Activity Feed
3. Show them the code (GitHub)
4. Walk through SECURITY.md

### If They Want Details
- Show architecture diagram
- Explain state machines
- Discuss future roadmap
- Demo code quality (tests, types, docs)

---

**Good luck! You've built something impressive. Show it with confidence.** 🚀
