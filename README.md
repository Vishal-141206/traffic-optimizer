# AI-Driven Dynamic Traffic Flow Optimizer & Emergency Green Corridor System

A production-quality intelligent traffic management system featuring real-time vehicle detection, adaptive signal timing, and emergency vehicle prioritization.

![Dashboard Preview](docs/dashboard-preview.png)

## 🚀 Features

### Core Functionality
- **Real-time Traffic Monitoring**: Process video feeds using YOLOv8 for vehicle detection and counting
- **Adaptive Signal Control**: Dynamic signal timing based on real-time traffic density analysis
- **Emergency Green Corridor**: Automatic detection and prioritization of emergency vehicles (ambulance, fire truck, police)
- **Smart Dashboard**: Professional analytics dashboard with real-time visualizations
- **Historical Analytics**: Comprehensive traffic pattern analysis and trend visualization

### Technical Highlights
- **WebSocket Real-time Updates**: Instant traffic data streaming via WebSocket connections
- **Redis Pub/Sub**: Efficient event broadcasting across system components
- **Intersection Simulation**: Visual simulation of traffic flow and signal states
- **Multi-directional Analysis**: Traffic monitoring for all four directions (N, S, E, W)

## 📋 Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18 | UI Framework |
| Vite | Build Tool |
| TypeScript | Type Safety |
| TailwindCSS | Styling |
| shadcn/ui | Component Library |
| Recharts | Data Visualization |
| Zustand | State Management |
| Framer Motion | Animations |
| React Router | Navigation |

### Backend
| Technology | Purpose |
|------------|---------|
| Python FastAPI | API Framework |
| SQLAlchemy (Async) | ORM |
| PostgreSQL | Primary Database |
| Redis | Caching & Pub/Sub |
| WebSockets | Real-time Communication |
| Pydantic | Data Validation |

### AI/Computer Vision
| Technology | Purpose |
|------------|---------|
| YOLOv8 | Object Detection |
| OpenCV | Image Processing |
| PyTorch | Deep Learning |
| Ultralytics | YOLO Implementation |

## 🏗️ Project Structure

```
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/             # Reusable UI components (button, card, etc.)
│   │   │   ├── layout/         # Layout components (sidebar, navbar)
│   │   │   └── dashboard/      # Dashboard-specific components
│   │   ├── pages/              # Page components
│   │   │   ├── Dashboard.tsx   # Main dashboard
│   │   │   ├── Intersections.tsx
│   │   │   ├── Cameras.tsx
│   │   │   ├── Analytics.tsx
│   │   │   ├── Emergency.tsx
│   │   │   └── Settings.tsx
│   │   ├── services/           # API & WebSocket services
│   │   ├── store/              # Zustand state management
│   │   ├── lib/                # Utility functions
│   │   └── types/              # TypeScript definitions
│   ├── Dockerfile
│   └── nginx.conf
│
├── backend/                    # FastAPI backend
│   ├── api/                    # API route handlers
│   │   ├── intersections.py
│   │   ├── cameras.py
│   │   ├── traffic.py
│   │   ├── signals.py
│   │   ├── emergency.py
│   │   ├── analytics.py
│   │   ├── websocket.py
│   │   └── video_feed.py
│   ├── core/                   # Core configurations
│   │   ├── config.py
│   │   ├── database.py
│   │   └── redis.py
│   ├── models/                 # Database models
│   │   ├── models.py
│   │   └── schemas.py
│   ├── services/               # Business logic
│   │   ├── traffic_processor.py
│   │   └── signal_optimizer.py
│   ├── vision/                 # Computer vision modules
│   │   ├── vehicle_detection.py
│   │   ├── traffic_density.py
│   │   └── emergency_detection.py
│   ├── main.py                 # FastAPI application entry
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml          # Docker orchestration
└── README.md

```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (recommended)
- Node.js 18+ (for manual frontend setup)
- Python 3.10+ (for manual backend setup)
- PostgreSQL 15+
- Redis 7+

### Using Docker (Recommended)

```bash
# Navigate to project directory
cd IIC

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/traffic_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📊 API Documentation

Once the backend is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/traffic_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
YOLO_MODEL_PATH=./models/yolov8n.pt
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 📈 Dashboard Features

1. **Real-time Metrics**
   - Vehicle counts by type
   - Congestion levels
   - Signal states
   - Emergency alerts

2. **Visualizations**
   - Traffic density charts
   - Intersection heatmaps
   - Signal cycle timelines
   - Historical trends

3. **Intersection Panel**
   - Live traffic simulation
   - Vehicle movement animation
   - Signal state indicators

## 🚨 Emergency Vehicle Detection

The system automatically detects emergency vehicles (ambulances, fire trucks) and:
- Overrides normal signal cycles
- Creates a green corridor
- Logs emergency events
- Sends real-time alerts to the dashboard

## 📝 License

MIT License - see LICENSE file for details.
