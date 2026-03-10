#!/bin/bash
set -e

echo "🚀 Setting up Traffic Flow Optimizer..."

# Backend setup
echo "📦 Setting up backend..."
cd /workspace/backend
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file for backend
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/traffic_db
REDIS_URL=redis://redis:6379
SECRET_KEY=dev-secret-key-change-in-production
YOLO_MODEL_PATH=./models/yolov8n.pt
EOF

# Frontend setup
echo "📦 Setting up frontend..."
cd /workspace/frontend
npm install

# Create .env file for frontend
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF

echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "  Frontend: cd frontend && npm run dev -- --host 0.0.0.0"
