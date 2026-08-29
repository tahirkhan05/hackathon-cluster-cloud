#!/bin/bash
# Start a full demo environment with 4 nodes

set -e

echo "🎬 Starting ClusterCloud Demo Environment"
echo "========================================="

# Start infrastructure
echo "Starting Docker services..."
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 5

# Start API in background
echo "Starting API..."
cd apps/api
source venv/bin/activate
python main.py &
API_PID=$!
cd ../..

sleep 3

# Start 4 node agents
echo "Starting Node Agents..."
cd apps/node-agent
source venv/bin/activate

NODE_AGENT_ID=node-a python agent.py &
NODE_A_PID=$!

NODE_AGENT_ID=node-b python agent.py &
NODE_B_PID=$!

NODE_AGENT_ID=node-c python agent.py &
NODE_C_PID=$!

NODE_AGENT_ID=node-d python agent.py &
NODE_D_PID=$!

cd ../..

sleep 3

# Start frontend
echo "Starting Frontend..."
cd apps/web
npm run dev &
WEB_PID=$!
cd ../..

echo ""
echo "✅ Demo environment running!"
echo ""
echo "API: http://localhost:8000"
echo "Dashboard: http://localhost:3000"
echo ""
echo "Processes:"
echo "  API: $API_PID"
echo "  Node A: $NODE_A_PID"
echo "  Node B: $NODE_B_PID"
echo "  Node C: $NODE_C_PID (kill this during demo)"
echo "  Node D: $NODE_D_PID"
echo "  Web: $WEB_PID"
echo ""
echo "To stop all: kill $API_PID $NODE_A_PID $NODE_B_PID $NODE_C_PID $NODE_D_PID $WEB_PID"
echo ""

# Save PIDs for cleanup
echo "$API_PID $NODE_A_PID $NODE_B_PID $NODE_C_PID $NODE_D_PID $WEB_PID" > .demo_pids

# Wait for user interrupt
trap "kill $API_PID $NODE_A_PID $NODE_B_PID $NODE_C_PID $NODE_D_PID $WEB_PID 2>/dev/null; exit" INT TERM

wait
