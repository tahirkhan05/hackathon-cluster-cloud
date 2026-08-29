# ClusterCloud Demo Script

## Preparation (Before Demo)

1. **Start all services**
   ```bash
   docker-compose up -d
   python apps/api/main.py
   ```

2. **Start 4 node agents** (in separate terminals)
   ```bash
   # Node A
   NODE_AGENT_ID=node-a python apps/node-agent/agent.py

   # Node B
   NODE_AGENT_ID=node-b python apps/node-agent/agent.py

   # Node C (will be killed mid-demo)
   NODE_AGENT_ID=node-c python apps/node-agent/agent.py

   # Node D
   NODE_AGENT_ID=node-d python apps/node-agent/agent.py
   ```

3. **Open dashboard**
   ```
   http://localhost:3000
   ```

4. **Verify all nodes show as "Available"** in dashboard

## Demo Flow (5-7 minutes)

### Act 1: The Setup (1 min)

**Narration**:
> "ClusterCloud lets anyone share their computer's power and earn CLSTR tokens. Right now we have 4 community members who've installed our Node Agent and are ready to help with rendering."

**Show**: Dashboard with 4 green nodes, capacity overview

**Narration**:
> "I'm a 3D artist and I need to render 100 frames for my animation. Instead of waiting hours on my laptop, I'll use ClusterCloud."

### Act 2: Job Submission (1 min)

**Action**: Click "New Job" → Select "Frame Rendering"

**Fill form**:
- Frames: 100
- Resolution: 1920x1080
- Quality: High
- Budget: 1000 CLSTR
- Deadline: 10 minutes

**Action**: Click "Build My Cloud"

**Show**: AI analysis panel appears

**Narration**:
> "ClusterCloud's AI analyzes my workload. It recognizes this is perfectly parallelizable—each frame is independent. It recommends splitting the work across all 4 available nodes."

**Show**: 
- AI reasoning text
- Recommended distribution: 25 frames per node
- Estimated cost: 800 CLSTR
- Estimated time: 5 minutes

**Action**: Click "Approve & Execute"

### Act 3: Execution Begins (1 min)

**Show**: Job status changes to "Executing"

**Narration**:
> "The system automatically distributes the work. Node A gets frames 1-25, Node B gets 26-50, Node C gets 51-75, and Node D gets 76-100."

**Show**: Task distribution visualization

**Show**: Progress bars filling for each node

**Show**: Live event stream:
```
[10:01:23] Task #1 assigned to Node A
[10:01:23] Task #2 assigned to Node B
[10:01:23] Task #3 assigned to Node C
[10:01:23] Task #4 assigned to Node D
[10:01:25] Node A started rendering frames 1-25
[10:01:26] Node B started rendering frames 26-50
[10:01:26] Node C started rendering frames 51-75
[10:01:27] Node D started rendering frames 76-100
[10:01:30] Node A completed frame 1
[10:01:31] Node B completed frame 26
```

**Narration**:
> "All nodes are working in parallel. You can see frames completing in real-time."

### Act 4: The Failure (30 seconds)

**Action**: (After ~15 frames completed per node) Kill Node C process

**Show**: Node C turns red in dashboard

**Show**: Incident alert appears:
```
⚠️ INCIDENT DETECTED
Node C heartbeat timeout
15 frames incomplete (51-65)
Status: Analyzing recovery options
```

**Narration**:
> "Uh oh—Node C just went offline. Maybe their power went out, or their internet dropped. But watch what happens next."

### Act 5: Automatic Recovery (1 min)

**Show**: Recovery agent analysis panel appears

**Narration**:
> "ClusterCloud immediately detects the failure and activates the recovery agent. The AI analyzes which tasks were incomplete and finds the best replacement."

**Show**: AI reasoning:
```
Analysis:
- Node C failed with 15 incomplete frames
- Nodes A, B, D still operational
- Node D has highest reliability score (0.98)
- Node D has available capacity
- Recommendation: Assign frames 51-65 to Node D
- Estimated completion: +2 minutes
```

**Action**: (Automatic) Recovery executes

**Show**: Event stream:
```
[10:03:15] Incident #1: Node C offline
[10:03:16] Recovery agent analyzing...
[10:03:17] Frames 51-65 reassigned to Node D
[10:03:18] Node D accepted additional tasks
[10:03:19] Rendering resumed
[10:03:22] Node D completed frame 51
```

**Show**: Progress bar for Node D extends

**Narration**:
> "Node D picks up where Node C left off. The job continues without any manual intervention."

### Act 6: Economic Consequences (1 min)

**Show**: Ledger updates panel

**Narration**:
> "Behind the scenes, ClusterCloud updates everyone's reputation and token balance."

**Show**: Ledger transactions:
```
Ledger Updates:

Node C:
- Reliability: 0.95 → 0.87 (-8%)
- Penalty: -50 CLSTR (from staked amount)
- Status: Temporary suspension

Customer (You):
- Compensation: +20 CLSTR (delay refund)

Node D:
- Bonus: +30 CLSTR (recovery assist)
- Reliability: 0.96 → 0.98 (+2%)
- Status: Trusted provider

Platform:
- Broker fee: +40 CLSTR
```

**Narration**:
> "Node C loses reputation and pays a penalty. I get compensated for the delay. Node D earns a bonus for helping with recovery. Everything is transparent and automatic."

### Act 7: Completion (30 seconds)

**Show**: All progress bars reach 100%

**Show**: Job status: "Completed"

**Show**: Final summary:
```
Job Completed Successfully

Total frames: 100
Duration: 7 minutes 23 seconds
Nodes used: 4 (1 replacement)
Total cost: 795 CLSTR
Incidents: 1 (automatically recovered)

Downloads: 
✓ All frames ready (ZIP)
✓ Composition preview (MP4)
```

**Narration**:
> "And we're done! All 100 frames rendered successfully, despite the failure. I didn't have to monitor it or intervene. The system handled everything automatically."

**Action**: Click "Download Results"

**Narration**:
> "That's ClusterCloud—community cloud computing that just works, even when things go wrong."

## Talking Points

### Key Messages

1. **Accessible**: No cloud expertise required
2. **Resilient**: Automatic failure recovery
3. **Fair**: Economic incentives for good behavior
4. **Transparent**: Live visibility into everything
5. **Intelligent**: AI assists with complex decisions
6. **Community-driven**: Anyone can contribute resources

### Technical Highlights

- Distributed task execution
- Real-time heartbeat monitoring
- Sub-10-second failure detection
- Deterministic recovery logic
- Auditable token economics
- WebSocket live updates
- Docker isolation for security

### Questions to Anticipate

**Q: What if multiple nodes fail?**
A: Recovery agent would iterate, finding replacements for each failure until job completes or no nodes remain.

**Q: What prevents malicious providers?**
A: Stake requirements, reputation tracking, result verification (hash checking in production), and automatic penalties.

**Q: Can this run other workloads besides rendering?**
A: Yes! The architecture supports any parallelizable workload. Rendering is our MVP focus.

**Q: How does pricing work?**
A: MVP uses fixed CLSTR rates. Production would use dynamic market-based pricing.

**Q: Is this blockchain?**
A: No. CLSTR is an internal ledger for the MVP. Future versions could integrate blockchain for decentralized trust.

## Demo Variants

### Quick Demo (2 minutes)
- Skip AI explanation details
- Kill node immediately after task assignment
- Show recovery and completion only

### Technical Deep Dive (15 minutes)
- Show API endpoints in browser dev tools
- Display WebSocket messages
- Show database state changes
- Explain AI prompts and responses
- Walk through code architecture

### Business Pitch (10 minutes)
- Focus on market opportunity
- Show cost comparison vs AWS/Azure
- Emphasize community ownership
- Discuss tokenomics in detail
- Project future scaling
