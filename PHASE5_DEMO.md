# Phase 5: Distributed Frame Execution - Demo Guide

## Overview

Phase 5 implements actual distributed frame rendering across multiple worker nodes with:
- Task assignment and polling
- Real frame rendering (PNG images) or CPU-intensive mock rendering
- Progress updates during execution
- Result storage and metadata
- Multi-node parallelism

---

## Architecture: How One Frame Travels Through the System

```
1. CUSTOMER SUBMITS JOB
   ↓
   POST /api/jobs
   {frame_count: 100, resolution: 1920x1080}
   ↓
   Job created in SUBMITTED status

2. SCHEDULER CREATES ALLOCATION PLAN
   ↓
   POST /api/scheduling/schedule-and-execute
   ↓
   - Finds compatible nodes (CPU/RAM/GPU requirements)
   - Scores nodes (reliability 40%, cost 30%, capacity 30%)
   - Distributes tasks round-robin
   - Creates 100 tasks in ASSIGNED status
   ↓
   Example distribution:
   - Node A: tasks [1,4,7,10,13...]  (34 tasks)
   - Node B: tasks [2,5,8,11,14...]  (33 tasks)
   - Node C: tasks [3,6,9,12,15...]  (33 tasks)

3. NODE POLLS FOR WORK
   ↓
   POST /api/tasks/poll
   {node_id: "node-A"}
   ↓
   Returns: Task {task_id, job_id, frame_number: 1, parameters: {...}}

4. NODE STARTS EXECUTION
   ↓
   PUT /api/tasks/{task_id}/status
   {status: "RUNNING"}
   ↓
   Task transitions: ASSIGNED → RUNNING

5. NODE RENDERS FRAME
   ↓
   FrameRenderer.render_frame(frame_number=1)
   ↓
   - Creates 1920x1080 PNG image
   - Animated gradient based on frame number
   - Overlays: frame #, node ID, timestamp
   - CPU/GPU workload based on complexity setting
   ↓
   Progress updates sent:
   POST /api/tasks/{task_id}/progress
   {progress_percent: 0, message: "Starting..."}
   {progress_percent: 50, message: "Rendering..."}
   {progress_percent: 80, message: "Uploading..."}

6. FRAME COMPLETE
   ↓
   PUT /api/tasks/{task_id}/status
   {
     status: "COMPLETED",
     result: {
       filename: "frame_000001.png",
       checksum: "sha256:...",
       file_size_bytes: 245678,
       resolution: "1920x1080",
       render_time_seconds: 2.34,
       node_id: "node-A"
     }
   }
   ↓
   Task transitions: RUNNING → COMPLETED

7. NODE POLLS FOR NEXT TASK
   ↓
   Repeats steps 3-6 for next assigned task
   ↓
   All nodes work in parallel

8. JOB COMPLETION
   ↓
   When all 100 tasks are COMPLETED
   ↓
   Job status: RUNNING → COMPLETED
   ↓
   Customer can download/aggregate results
```

---

## Quick Start: Automated Demo

Run the complete end-to-end demo:

```bash
python demo_distributed_rendering.py
```

This automatically:
1. Starts API backend
2. Starts 3 node agents
3. Submits 12-frame rendering job
4. Monitors execution in real-time
5. Verifies results
6. Cleans up processes

---

## Manual Demo: Step by Step

### Terminal 1: Start API Backend

```bash
cd apps/api
python -m uvicorn main:app --reload
```

Wait for: `Application startup complete`

### Terminal 2: Start Node Agent 1

```bash
cd apps/node-agent
export PROVIDER_ID="node-alice"
export CONTROL_PLANE_URL="http://localhost:8000"
export HEARTBEAT_INTERVAL="5"
export MAX_CONCURRENT_TASKS="2"
python agent.py
```

### Terminal 3: Start Node Agent 2

```bash
cd apps/node-agent
export PROVIDER_ID="node-bob"
export CONTROL_PLANE_URL="http://localhost:8000"
export HEARTBEAT_INTERVAL="5"
export MAX_CONCURRENT_TASKS="2"
python agent.py
```

### Terminal 4: Start Node Agent 3

```bash
cd apps/node-agent
export PROVIDER_ID="node-charlie"
export CONTROL_PLANE_URL="http://localhost:8000"
export HEARTBEAT_INTERVAL="5"
export MAX_CONCURRENT_TASKS="2"
python agent.py
```

### Terminal 5: Submit Job and Watch

```bash
# Create job
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "demo-customer",
    "workload_type": "frame_rendering",
    "parameters": {
      "frame_count": 12,
      "width": 1280,
      "height": 720,
      "complexity": "medium"
    },
    "budget_clstr": 500,
    "deadline_seconds": 120
  }'

# Save job_id from response

# Schedule and execute
curl -X POST http://localhost:8000/api/scheduling/schedule-and-execute \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "<JOB_ID>",
    "cpu_cores_min": 2,
    "ram_gb_min": 2,
    "task_count": 12,
    "estimated_task_duration_seconds": 10,
    "budget_clstr": 500,
    "reliability_min": 0.5
  }'

# Watch tasks
watch -n 2 'curl -s http://localhost:8000/api/tasks?job_id=<JOB_ID> | python -m json.tool'
```

---

## Verification

### Check Nodes

```bash
curl http://localhost:8000/api/nodes | python -m json.tool
```

Expected: 3 nodes in AVAILABLE status

### Check Tasks

```bash
curl "http://localhost:8000/api/tasks?job_id=<JOB_ID>" | python -m json.tool
```

Watch status transitions:
- ASSIGNED → RUNNING → COMPLETED

### Check Rendered Frames

```bash
ls -lh apps/node-agent/rendered_frames/
```

Expected: `frame_000000.png` through `frame_000011.png`

Each frame shows:
- Animated gradient background
- Frame number overlay
- Node ID watermark
- Timestamp

---

## Frame Renderer Details

### Real Renderer (with Pillow)

When Pillow is installed:
- Generates actual PNG images
- Resolution: configurable (default 1920x1080)
- Content:
  - Animated gradient (varies per frame)
  - Optional patterns based on complexity
  - Text overlays with frame #, node ID, timestamp
- Output: `frame_NNNNNN.png`
- Performance: ~2-5 seconds per frame on modern CPU

### Mock Renderer (fallback)

When Pillow not available:
- CPU-intensive hash computation
- Simulates rendering workload
- Output: `frame_NNNNNN.mock` text file
- Performance: configurable via complexity parameter

### Complexity Settings

- **low**: 1M iterations, ~0.5-1s
- **medium**: 5M iterations, ~2-3s  
- **high**: 10M iterations + patterns, ~5-10s

---

## Task Distribution Example

For 12 frames across 3 nodes:

```
Node A (node-alice):
  - Task 1 → Frame 0
  - Task 4 → Frame 3
  - Task 7 → Frame 6
  - Task 10 → Frame 9
  Total: 4 frames

Node B (node-bob):
  - Task 2 → Frame 1
  - Task 5 → Frame 4
  - Task 8 → Frame 7
  - Task 11 → Frame 10
  Total: 4 frames

Node C (node-charlie):
  - Task 3 → Frame 2
  - Task 6 → Frame 5
  - Task 9 → Frame 8
  - Task 12 → Frame 11
  Total: 4 frames
```

All nodes work in parallel, reducing total time by ~3x compared to single node.

---

## API Endpoints Added

### `POST /api/tasks/poll`

Node polls for next assigned task.

Request:
```json
{"node_id": "node-abc123"}
```

Response:
```json
{
  "task_id": "task-xyz",
  "job_id": "job-123",
  "task_number": 5,
  "parameters": {
    "frame_number": 4,
    "width": 1920,
    "height": 1080,
    "complexity": "medium"
  },
  "status": "ASSIGNED"
}
```

### `PUT /api/tasks/{task_id}/status`

Update task status.

Request:
```json
{
  "status": "RUNNING"
}
```

Or with completion:
```json
{
  "status": "COMPLETED",
  "result": {
    "filename": "frame_000004.png",
    "checksum": "sha256:abc...",
    "file_size_bytes": 234567,
    "render_time_seconds": 2.45
  }
}
```

### `POST /api/tasks/{task_id}/progress`

Report rendering progress.

Request:
```json
{
  "progress_percent": 50,
  "message": "Rendering frame 4..."
}
```

---

## Troubleshooting

### No tasks being assigned

Check that scheduler created tasks:
```bash
curl "http://localhost:8000/api/tasks?job_id=<JOB_ID>"
```

Verify task status is ASSIGNED and has node_id set.

### Nodes not registering

Check node agent logs for connection errors.

Verify API is reachable:
```bash
curl http://localhost:8000/health
```

### Rendering fails

Check node agent output for errors.

If Pillow not installed, mock renderer will be used automatically.

Install Pillow for real rendering:
```bash
pip install Pillow
```

---

## Performance Metrics

On typical hardware:
- 1280x720 medium complexity: ~2-3s per frame
- 1920x1080 medium complexity: ~3-5s per frame
- 1920x1080 high complexity: ~8-12s per frame

With 3 nodes:
- 12 frames sequential: ~36s
- 12 frames distributed: ~12s (3x speedup)

With 10 nodes:
- 100 frames sequential: ~500s
- 100 frames distributed: ~50s (10x speedup)

---

## Next Steps: Phase 6

Phase 5 focuses on happy path execution. Phase 6 will add:
- Automatic failure detection
- Task retry logic
- Node failure recovery
- Heartbeat timeout handling
- Zombie task cleanup
- Incident tracking
