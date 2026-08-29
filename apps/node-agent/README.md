# ClusterCloud Node Agent - Phase 1

Provider-side agent that registers with the control plane and maintains heartbeat.

## Phase 1 Scope

✅ Node configuration
✅ Hardware discovery (CPU, RAM, GPU, disk)
✅ Node registration with retry
✅ Heartbeat lifecycle
✅ Graceful shutdown
✅ Structured logging

❌ Task execution (Phase 2)
❌ Docker isolation (Phase 2)

## Architecture

```
agent.py                    # Main entry point, lifecycle management
├── config.py              # Configuration from environment
├── hardware.py            # Hardware discovery abstraction
├── registration.py        # Registration with retry logic
└── heartbeat.py           # Heartbeat management & failure tracking
```

## Hardware Discovery

Detects and reports:
- **CPU**: Cores (physical/logical), frequency, architecture
- **RAM**: Total, available, usage percentage
- **GPU**: NVIDIA GPUs via pynvml or nvidia-smi (optional)
- **VRAM**: GPU memory if detected
- **Disk**: Total, free space, usage
- **Network**: Hostname, IP address, FQDN

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with defaults
python agent.py

# Run with custom configuration
export CONTROL_PLANE_URL=http://api.clustercloud.io
export NODE_AGENT_ID=my-node-01
export LOG_LEVEL=DEBUG
python agent.py
```

## Configuration

All configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTROL_PLANE_URL` | `http://localhost:8000` | API endpoint |
| `NODE_AGENT_API_KEY` | `dev-node-agent-key` | Authentication key |
| `NODE_AGENT_ID` | System hostname | Provider identifier |
| `HEARTBEAT_INTERVAL_SECONDS` | `5` | Heartbeat frequency |
| `HEARTBEAT_TIMEOUT_SECONDS` | `10` | Request timeout |
| `MAX_HEARTBEAT_FAILURES` | `3` | Shutdown after N failures |
| `MAX_CONCURRENT_TASKS` | `2` | Task capacity |
| `COST_PER_TASK_CLSTR` | `10.0` | Pricing |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SIMULATE_FAILURE` | `false` | Demo: simulate failure |
| `FAILURE_AFTER_SECONDS` | `30` | Demo: when to fail |

## Heartbeat Lifecycle

```
1. Initialization
   ├── Load configuration
   └── Discover hardware

2. Registration
   ├── POST /api/nodes/register
   ├── Retry with exponential backoff
   └── Receive node_id

3. Heartbeat Loop
   ├── Every N seconds: POST /api/nodes/{node_id}/heartbeat
   ├── Track consecutive failures
   └── Shutdown if failures >= threshold

4. Graceful Shutdown
   ├── Handle SIGINT/SIGTERM
   ├── Log statistics
   └── Exit cleanly
```

## What Happens If Server Disappears?

The node agent is resilient to control plane failures:

### During Registration
- **Behavior**: Retry up to 10 times with exponential backoff
- **Backoff**: 5s → 10s → 20s → 40s → ...
- **Outcome**: Eventually exits if server never responds

### During Heartbeat
- **Behavior**: Track consecutive failures
- **Threshold**: Shutdown after 3 consecutive failures (configurable)
- **Rationale**: Prevents zombie nodes from running indefinitely without supervision
- **Recovery**: When server returns, node must be restarted to re-register

### Example Scenario

```
T+0s:   Heartbeat sent → Success
T+5s:   Heartbeat sent → Connection error (failure #1)
T+10s:  Heartbeat sent → Timeout (failure #2)
T+15s:  Heartbeat sent → Connection error (failure #3)
T+15s:  → SHUTDOWN (threshold reached)
```

If server returns after failure #1 or #2, normal operation resumes.

## Demo Mode

Simulate node failure for testing recovery:

```bash
SIMULATE_FAILURE=true FAILURE_AFTER_SECONDS=30 python agent.py
```

The node will:
1. Register successfully
2. Send heartbeats for 30 seconds
3. Abruptly terminate (simulating crash/network loss)

This allows testing:
- Heartbeat timeout detection
- Incident creation
- Task reassignment
- Reliability score updates

## Logging

Structured logging with levels:

- `DEBUG`: Heartbeat confirmations, detailed flow
- `INFO`: Registration, status changes, lifecycle events
- `WARNING`: Heartbeat failures, retry attempts
- `ERROR`: Fatal errors, shutdown conditions

Example output:

```
2026-08-29 14:23:45 - __main__ - INFO - 🚀 ClusterCloud Node Agent - Phase 1
2026-08-29 14:23:45 - __main__ - INFO - Configuration loaded:
2026-08-29 14:23:45 - __main__ - INFO -   Control Plane: http://localhost:8000
2026-08-29 14:23:45 - __main__ - INFO -   Provider ID: WORKSTATION-01
2026-08-29 14:23:45 - hardware - INFO - CPU: 8 cores
2026-08-29 14:23:45 - hardware - INFO - RAM: 16.0 GB
2026-08-29 14:23:45 - hardware - INFO - GPU: 1 device(s) detected
2026-08-29 14:23:46 - registration - INFO - ✅ Successfully registered
2026-08-29 14:23:46 - registration - INFO - Node ID: 550e8400-e29b-41d4-a716-446655440000
2026-08-29 14:23:46 - __main__ - INFO - Entering heartbeat loop
```

## Testing

```bash
# Run with test control plane
CONTROL_PLANE_URL=http://localhost:8000 python agent.py

# Test retry logic (control plane offline)
CONTROL_PLANE_URL=http://localhost:9999 python agent.py

# Test graceful shutdown
python agent.py
# Press Ctrl+C

# Test failure simulation
SIMULATE_FAILURE=true FAILURE_AFTER_SECONDS=10 python agent.py
```

## Phase 2 Additions (Future)

- Task polling endpoint
- Docker container execution
- Task result reporting
- Resource monitoring during execution
- Task timeout handling
