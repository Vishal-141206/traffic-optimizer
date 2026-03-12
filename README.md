# AI-Driven Dynamic Traffic Flow Optimizer & Emergency Green Corridor System

A production-quality intelligent traffic management system featuring real-time vehicle detection using YOLOv8, LSTM-based traffic forecasting, and adaptive signal control with emergency vehicle prioritization.

## 🚀 Features

### Core Functionality
- **Real-time Vehicle Detection**: YOLOv8-powered vehicle detection and classification (cars, motorcycles, buses, trucks, bicycles)
- **Traffic Forecasting**: LSTM neural network for predicting traffic patterns up to 6 hours ahead
- **Adaptive Signal Control**: Dynamic signal timing based on real-time traffic density analysis
- **Emergency Green Corridor**: Automatic detection and prioritization of emergency vehicles
- **Interactive Dashboard**: Streamlit-based real-time traffic insights and analytics

### Technical Highlights
- **Computer Vision**: YOLOv8 (Ultralytics) for accurate vehicle detection
- **Video Processing**: OpenCV for handling CCTV/traffic camera feeds
- **Deep Learning**: TensorFlow/Keras LSTM models for traffic prediction
- **Data Analytics**: NumPy & Pandas for efficient data handling
- **Visualization**: Plotly for interactive charts and graphs

## 📋 Tech Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Computer Vision & AI** | YOLOv8 (Ultralytics) | Vehicle Detection & Classification |
| | OpenCV | Video Processing & Traffic Feeds |
| **Programming & Backend** | Python | Traffic Analysis & AI Integration |
| **Machine Learning** | TensorFlow/Keras LSTM | Traffic Forecasting |
| **Data Processing** | NumPy & Pandas | Data Handling & Analytics |
| **Visualization & Dashboard** | Streamlit | Real-Time Traffic Insights |
| | Plotly | Interactive Charts |
| **Deployment** | City CCTV / Traffic Cameras | Live Traffic Feeds |

## 🏗️ Project Structure

```
IIC/
├── app.py                      # Main Streamlit dashboard application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── models/                     # AI/ML models
│   ├── __init__.py
│   ├── vehicle_detection.py    # YOLOv8 vehicle detection
│   └── traffic_forecasting.py  # LSTM traffic prediction
│
├── utils/                      # Utility modules
│   ├── __init__.py
│   ├── video_processor.py      # OpenCV video handling
│   └── data_handler.py         # Pandas data management
│
├── data/                       # Data storage (auto-created)
├── weights/                    # Model weights (auto-created)
└── logs/                       # Application logs (auto-created)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Webcam or video files for testing (optional)

### Installation

```bash
# Clone or navigate to project
cd IIC

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```bash
# Start Streamlit dashboard
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 📊 Dashboard Features

### 1. Main Dashboard
- Real-time traffic metrics (vehicle counts, density levels)
- Hourly traffic pattern visualization
- Vehicle type distribution charts
- 6-hour traffic forecast with confidence intervals
- Intersection signal status

### 2. Live Detection
- Upload images/videos for vehicle detection
- Real-time YOLOv8 inference
- Vehicle classification and counting
- Automatic signal timing recommendations

### 3. Analytics
- Historical traffic volume analysis
- Daily pattern heatmaps
- Density distribution charts
- Intersection comparison
- Data export functionality

### 4. Emergency Control
- Green corridor activation/deactivation
- Emergency vehicle simulation
- Emergency event history
- Real-time signal override

### 5. Settings
- YOLOv8 detection parameters
- Signal timing configuration
- Camera feed management

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Vehicle detection confidence
YOLO_CONFIDENCE = 0.5

# Traffic density thresholds
DENSITY_THRESHOLDS = {
    "low": 10,
    "medium": 25,
    "high": 40,
    "critical": 100
}

# Signal timing (seconds)
SIGNAL_TIMING = {
    "low": {"green": 15, "yellow": 3, "red": 45},
    "medium": {"green": 30, "yellow": 3, "red": 30},
    "high": {"green": 45, "yellow": 3, "red": 15},
    "critical": {"green": 60, "yellow": 3, "red": 10}
}
```

## 🚨 Emergency Vehicle Detection

The system automatically detects emergency vehicles through:
1. Color analysis (red/blue lights, white ambulance body)
2. Vehicle classification patterns
3. Manual activation via dashboard

When detected:
- All signals receive extended green phase
- Green corridor is established along the route
- Events are logged for analysis

## 📈 LSTM Traffic Forecasting

The forecasting model:
- Uses 24-hour historical sequences
- Predicts 6 hours ahead
- Incorporates hourly and day-of-week patterns
- Falls back to statistical methods when model unavailable

To train with your data:
```python
from models.traffic_forecasting import TrafficForecaster, generate_sample_data

# Generate or load your data
data = generate_sample_data(days=30)

# Train model
forecaster = TrafficForecaster()
history = forecaster.train(data)
```

## 🎥 Camera Integration

### Supported Sources
- **RTSP streams**: `rtsp://camera.ip/stream`
- **HTTP streams**: `http://camera.ip/feed`
- **Local files**: `path/to/video.mp4`
- **Webcam**: Device index `0`, `1`, etc.

### Example Usage
```python
from utils.video_processor import VideoProcessor

processor = VideoProcessor(source="rtsp://192.168.1.100/stream")
if processor.connect():
    for frame in processor.get_frames():
        # Process frame
        pass
```

## 🐳 GitHub Codespaces

This project includes devcontainer configuration for GitHub Codespaces:

1. Push to GitHub
2. Open repository in Codespaces
3. Wait for container setup
4. Run `streamlit run app.py`

## 📝 License

MIT License - see LICENSE file for details.
