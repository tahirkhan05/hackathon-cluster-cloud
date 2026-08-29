# ClusterCloud Node Agent

Simple Python agent that registers with the control plane and simulates work.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run agent
python agent.py

# Run with custom ID
NODE_AGENT_ID=node-a python agent.py

# Simulate failure after 30 seconds
SIMULATE_FAILURE=true FAILURE_AFTER_SECONDS=30 python agent.py
```

## Environment Variables

- `CONTROL_PLANE_URL` - API endpoint (default: http://localhost:8000)
- `NODE_AGENT_ID` - Unique node identifier
- `HEARTBEAT_INTERVAL_SECONDS` - Heartbeat frequency (default: 5)
- `SIMULATE_FAILURE` - Set to "true" to simulate failure
- `FAILURE_AFTER_SECONDS` - When to fail (default: 30)

## Demo Usage

Run 4 agents for the demo:

```bash
# Terminal 1
NODE_AGENT_ID=node-a python agent.py

# Terminal 2
NODE_AGENT_ID=node-b python agent.py

# Terminal 3 (will fail during demo)
NODE_AGENT_ID=node-c SIMULATE_FAILURE=true python agent.py

# Terminal 4
NODE_AGENT_ID=node-d python agent.py
```
