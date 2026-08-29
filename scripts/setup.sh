#!/bin/bash
# ClusterCloud Setup Script
# Run this after cloning the repository

set -e

echo "🚀 ClusterCloud Setup"
echo "===================="

# Check prerequisites
echo "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }

echo "✅ Prerequisites satisfied"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration before continuing"
    exit 0
fi

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d postgres redis

echo "Waiting for database..."
sleep 5

# Setup API
echo "Setting up API..."
cd apps/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate
cd ../..

# Setup Node Agent
echo "Setting up Node Agent..."
cd apps/node-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

# Setup Frontend
echo "Setting up Frontend..."
cd apps/web
npm install
cd ../..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start ClusterCloud:"
echo "  1. Terminal 1: cd apps/api && source venv/bin/activate && python main.py"
echo "  2. Terminal 2: cd apps/node-agent && source venv/bin/activate && python agent.py"
echo "  3. Terminal 3: cd apps/web && npm run dev"
echo "  4. Open http://localhost:3000"
echo ""
