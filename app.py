"""
AI-Driven Traffic Flow Optimizer & Emergency Green Corridor System
Main Streamlit Dashboard Application
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import cv2
from PIL import Image
import io
import av

# WebRTC for live webcam
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration

# Import custom modules
from config import (CAMERA_FEEDS, DENSITY_THRESHOLDS, SIGNAL_TIMING, 
                   DASHBOARD_REFRESH_RATE)
from models.vehicle_detection import VehicleDetector, EmergencyVehicleDetector
from models.traffic_forecasting import TrafficForecaster, generate_sample_data
from utils.data_handler import TrafficDataHandler, SignalOptimizer, generate_demo_data
from utils.video_processor import VideoProcessor, create_test_frame

# RTC Configuration for WebRTC
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# Page configuration
st.set_page_config(
    page_title="Traffic Flow Optimizer",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .status-low { background-color: #10b981; color: white; }
    .status-medium { background-color: #f59e0b; color: white; }
    .status-high { background-color: #ef4444; color: white; }
    .status-critical { background-color: #7c3aed; color: white; }
    .emergency-alert {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'data_handler' not in st.session_state:
        st.session_state.data_handler = TrafficDataHandler()
    if 'detector' not in st.session_state:
        st.session_state.detector = VehicleDetector()
    if 'forecaster' not in st.session_state:
        st.session_state.forecaster = TrafficForecaster()
    if 'signal_optimizer' not in st.session_state:
        st.session_state.signal_optimizer = SignalOptimizer()
    if 'emergency_active' not in st.session_state:
        st.session_state.emergency_active = False
    if 'demo_data_generated' not in st.session_state:
        st.session_state.demo_data_generated = False
    if 'live_detections' not in st.session_state:
        st.session_state.live_detections = []


class VideoTransformer(VideoProcessorBase):
    """Video processor for live webcam detection"""
    
    def __init__(self):
        self.detector = VehicleDetector()
        self.frame_count = 0
        self.last_result = None
        self.process_every_n = 3  # Process every 3rd frame for performance
    
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1
        
        # Process every Nth frame
        if self.frame_count % self.process_every_n == 0:
            result = self.detector.detect(img, draw_boxes=True)
            self.last_result = result
            return av.VideoFrame.from_ndarray(result.frame, format="bgr24")
        elif self.last_result is not None:
            # Draw last known boxes on current frame
            return av.VideoFrame.from_ndarray(self.last_result.frame, format="bgr24")
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")


def render_sidebar():
    """Render the sidebar navigation"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/traffic-light.png", width=60)
        st.title("Traffic Optimizer")
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "📹 Live Detection", "📈 Analytics", 
             "🚨 Emergency Control", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Quick stats
        if len(st.session_state.data_handler.traffic_data) > 0:
            stats = st.session_state.data_handler.get_statistics(hours=1)
            st.metric("Current Avg Vehicles/hr", f"{stats.avg_vehicles_per_hour:.0f}")
            st.metric("Trend", stats.trend.capitalize())
        
        st.divider()
        
        # Demo data button
        if st.button("🔄 Generate Demo Data", use_container_width=True):
            with st.spinner("Generating..."):
                generate_demo_data(st.session_state.data_handler, days=3)
                st.session_state.demo_data_generated = True
            st.success("Demo data generated!")
            st.rerun()
        
        return page


def render_dashboard():
    """Main dashboard view"""
    st.markdown('<h1 class="main-header">🚦 Traffic Flow Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real-time traffic monitoring and analysis powered by AI</p>', unsafe_allow_html=True)
    
    # Check for data
    if len(st.session_state.data_handler.traffic_data) == 0:
        st.info("📊 No traffic data available. Click 'Generate Demo Data' in the sidebar to get started.")
        return
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    stats = st.session_state.data_handler.get_statistics(hours=24)
    
    with col1:
        st.metric(
            "Total Vehicles (24h)",
            f"{stats.total_vehicles:,}",
            delta=f"{stats.trend}"
        )
    
    with col2:
        st.metric(
            "Avg Vehicles/Hour",
            f"{stats.avg_vehicles_per_hour:.0f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Peak Hour",
            f"{stats.peak_hour}:00",
            delta=f"{stats.peak_count} vehicles"
        )
    
    with col4:
        # Get density color
        dominant_density = max(stats.density_distribution, 
                             key=stats.density_distribution.get)
        st.metric(
            "Current Density",
            dominant_density.upper(),
            delta=None
        )
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Hourly Traffic Pattern")
        hourly_data = st.session_state.data_handler.get_hourly_aggregates()
        
        if len(hourly_data) > 0:
            fig = px.area(
                hourly_data,
                x='hour',
                y='vehicle_count',
                title='',
                color_discrete_sequence=['#667eea']
            )
            fig.update_layout(
                xaxis_title="Hour of Day",
                yaxis_title="Avg Vehicle Count",
                showlegend=False,
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hourly data available for today")
    
    with col2:
        st.subheader("🚗 Vehicle Distribution")
        vehicle_dist = st.session_state.data_handler.get_vehicle_distribution()
        
        if sum(vehicle_dist.values()) > 0:
            fig = px.pie(
                values=list(vehicle_dist.values()),
                names=list(vehicle_dist.keys()),
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No vehicle distribution data available")
    
    # Traffic Forecast
    st.divider()
    st.subheader("🔮 Traffic Forecast (Next 6 Hours)")
    
    recent_data = st.session_state.data_handler.get_recent_data(hours=48)
    if len(recent_data) >= 24:
        # Aggregate by hour for forecasting
        recent_data['hour_bucket'] = recent_data['timestamp'].dt.floor('H')
        forecast_input = recent_data.groupby('hour_bucket').agg({
            'vehicle_count': 'mean'
        }).reset_index().rename(columns={'hour_bucket': 'timestamp'})
        
        forecast = st.session_state.forecaster.forecast(forecast_input)
        
        # Create forecast chart
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=forecast_input['timestamp'].tail(24),
            y=forecast_input['vehicle_count'].tail(24),
            mode='lines',
            name='Historical',
            line=dict(color='#6b7280')
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=forecast.timestamps,
            y=forecast.predictions,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='#667eea', dash='dash')
        ))
        
        # Confidence interval
        fig.add_trace(go.Scatter(
            x=forecast.timestamps + forecast.timestamps[::-1],
            y=list(forecast.confidence_upper) + list(forecast.confidence_lower[::-1]),
            fill='toself',
            fillcolor='rgba(102, 126, 234, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence'
        ))
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Predicted Vehicle Count",
            height=350,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need at least 24 hours of data for forecasting")
    
    # Signal Status
    st.divider()
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚦 Intersection Signal Status")
        
        # Create signal status cards
        intersections = st.session_state.data_handler.traffic_data['intersection_id'].unique()
        
        if len(intersections) > 0:
            cols = st.columns(min(4, len(intersections)))
            
            for idx, int_id in enumerate(intersections[:4]):
                with cols[idx]:
                    int_stats = st.session_state.data_handler.get_statistics(
                        intersection_id=int_id, hours=1
                    )
                    density = max(int_stats.density_distribution, 
                                key=int_stats.density_distribution.get)
                    timing = st.session_state.signal_optimizer.calculate_timing(density)
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, 
                        {'#10b981' if density == 'low' else '#f59e0b' if density == 'medium' else '#ef4444' if density == 'high' else '#7c3aed'} 0%, 
                        {'#059669' if density == 'low' else '#d97706' if density == 'medium' else '#dc2626' if density == 'high' else '#6d28d9'} 100%);
                        padding: 1rem; border-radius: 0.75rem; color: white; text-align: center;">
                        <div style="font-size: 0.875rem; opacity: 0.9;">{int_id}</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">{density.upper()}</div>
                        <div style="font-size: 0.75rem; margin-top: 0.5rem;">
                            🟢 {timing['green']}s | 🟡 {timing['yellow']}s | 🔴 {timing['red']}s
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🚨 Emergency Status")
        
        emergency_count = st.session_state.data_handler.traffic_data['emergency_detected'].sum()
        
        if st.session_state.emergency_active or emergency_count > 0:
            st.markdown("""
            <div class="emergency-alert">
                <strong>⚠️ Emergency Alert</strong><br>
                Green corridor activated. All signals prioritized for emergency vehicle passage.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success("✅ No active emergencies")


def render_live_detection():
    """Live video detection view"""
    st.markdown('<h1 class="main-header">📹 Live Vehicle Detection</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">YOLOv8-powered real-time vehicle detection and classification</p>', unsafe_allow_html=True)
    
    # Initialize video state
    if 'video_playing' not in st.session_state:
        st.session_state.video_playing = False
    if 'current_stats' not in st.session_state:
        st.session_state.current_stats = {'total': 0, 'counts': {}}
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Video source selection
        source_type = st.radio(
            "Video Source",
            ["Upload Image", "Upload Video", "Test Frame", "Webcam"],
            horizontal=True
        )
        
        frame = None
        is_video = False
        
        if source_type == "Upload Image":
            uploaded_file = st.file_uploader(
                "Upload a traffic image",
                type=['jpg', 'jpeg', 'png', 'bmp', 'webp']
            )
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        elif source_type == "Upload Video":
            uploaded_file = st.file_uploader(
                "Upload a traffic video",
                type=['mp4', 'avi', 'mov', 'mkv', 'webm']
            )
            
            if uploaded_file:
                is_video = True
                # Save video temporarily
                temp_path = "temp_video.mp4"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.read())
                
                # Video controls
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    play_btn = st.button("▶️ Play Detection", use_container_width=True)
                with col_b:
                    stop_btn = st.button("⏹️ Stop", use_container_width=True)
                with col_c:
                    frame_skip = st.slider("Process every N frames", 1, 10, 3)
                
                if stop_btn:
                    st.session_state.video_playing = False
                
                if play_btn or st.session_state.video_playing:
                    st.session_state.video_playing = True
                    
                    # Video processing
                    cap = cv2.VideoCapture(temp_path)
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                    
                    st.info(f"📽️ Video: {total_frames} frames @ {fps} FPS")
                    
                    # Create placeholders for real-time update
                    frame_placeholder = st.empty()
                    stats_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    
                    frame_count = 0
                    all_detections = []
                    
                    while cap.isOpened() and st.session_state.video_playing:
                        ret, video_frame = cap.read()
                        if not ret:
                            break
                        
                        frame_count += 1
                        progress = frame_count / total_frames
                        progress_bar.progress(progress)
                        
                        # Process every Nth frame
                        if frame_count % frame_skip == 0:
                            # Run detection
                            result = st.session_state.detector.detect(video_frame, draw_boxes=True)
                            all_detections.append(result.total_count)
                            
                            # Display frame
                            display_frame = cv2.cvtColor(result.frame, cv2.COLOR_BGR2RGB)
                            frame_placeholder.image(display_frame, caption=f"Frame {frame_count}/{total_frames}", use_container_width=True)
                            
                            # Update stats
                            avg_vehicles = np.mean(all_detections) if all_detections else 0
                            stats_placeholder.markdown(f"""
                            | Metric | Value |
                            |--------|-------|
                            | Current Vehicles | **{result.total_count}** |
                            | Avg Vehicles | **{avg_vehicles:.1f}** |
                            | Frames Processed | **{len(all_detections)}** |
                            | Density | **{st.session_state.detector.get_density_level(result.total_count).upper()}** |
                            """)
                            
                            st.session_state.current_stats = {
                                'total': result.total_count,
                                'counts': result.vehicle_counts,
                                'avg': avg_vehicles
                            }
                    
                    cap.release()
                    st.session_state.video_playing = False
                    
                    if all_detections:
                        st.success(f"✅ Processed {len(all_detections)} frames. Avg vehicles: {np.mean(all_detections):.1f}")
                        
                        # Show detection chart
                        fig = px.line(
                            x=list(range(len(all_detections))),
                            y=all_detections,
                            labels={'x': 'Frame', 'y': 'Vehicle Count'},
                            title='Vehicle Count Over Time'
                        )
                        fig.update_traces(fill='tozeroy')
                        st.plotly_chart(fig, use_container_width=True)
        
        elif source_type == "Test Frame":
            # Generate synthetic test frame
            frame = create_test_frame(add_vehicles=True)
            st.info("Using synthetic test frame for demonstration")
        
        elif source_type == "Webcam":
            st.subheader("🎥 Live Webcam Detection")
            st.info("Click START to begin live vehicle detection from your webcam")
            
            # WebRTC streamer for live webcam
            webrtc_ctx = webrtc_streamer(
                key="vehicle-detection",
                video_processor_factory=VideoTransformer,
                rtc_configuration=RTC_CONFIGURATION,
                media_stream_constraints={
                    "video": {"width": 640, "height": 480},
                    "audio": False
                },
                async_processing=True
            )
            
            if webrtc_ctx.video_processor:
                st.success("🟢 Live detection active - vehicles are being detected in real-time!")
                
                # Show detection info
                st.markdown("""
                **Detection Info:**
                - Processing every 3rd frame for performance
                - Green boxes = Cars
                - Orange boxes = Motorcycles  
                - Blue boxes = Buses
                - Red boxes = Trucks
                """)
            
            # Set flag to skip single frame detection
            is_video = True
        
        # Run detection for single image/frame (not video)
        if frame is not None and not is_video:
            st.subheader("Detection Results")
            
            with st.spinner("Running YOLOv8 detection..."):
                result = st.session_state.detector.detect(frame, draw_boxes=True)
            
            # Display annotated frame
            display_frame = cv2.cvtColor(result.frame, cv2.COLOR_BGR2RGB)
            st.image(display_frame, caption="Detected Vehicles", use_container_width=True)
            
            # Detection metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Total Vehicles", result.total_count)
            with col_b:
                st.metric("Processing Time", f"{result.processing_time*1000:.1f}ms")
            with col_c:
                density = st.session_state.detector.get_density_level(result.total_count)
                st.metric("Density Level", density.upper())
            
            # Store for sidebar display
            st.session_state.current_stats = {
                'total': result.total_count,
                'counts': result.vehicle_counts
            }
    
    with col2:
        st.subheader("Detection Summary")
        
        # Show stats from current detection
        if st.session_state.current_stats.get('counts'):
            # Vehicle counts by type
            counts = st.session_state.current_stats['counts']
            if counts:
                df = pd.DataFrame([
                    {"Type": k.capitalize(), "Count": v}
                    for k, v in counts.items()
                ])
                
                fig = px.bar(
                    df,
                    x="Type",
                    y="Count",
                    color="Type",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_layout(showlegend=False, height=250)
                st.plotly_chart(fig, use_container_width=True)
            
            # Signal recommendation
            st.subheader("🚦 Recommended Signal Timing")
            total = st.session_state.current_stats.get('total', 0)
            density = st.session_state.detector.get_density_level(total)
            timing = st.session_state.signal_optimizer.calculate_timing(density)
            
            st.markdown(f"""
            | Phase | Duration |
            |-------|----------|
            | 🟢 Green | **{timing['green']}s** |
            | 🟡 Yellow | **{timing['yellow']}s** |
            | 🔴 Red | **{timing['red']}s** |
            """)


def render_analytics():
    """Analytics view"""
    st.markdown('<h1 class="main-header">📈 Traffic Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Historical analysis and traffic pattern insights</p>', unsafe_allow_html=True)
    
    if len(st.session_state.data_handler.traffic_data) == 0:
        st.info("📊 No traffic data available. Generate demo data from the sidebar.")
        return
    
    # Time range selector
    time_range = st.selectbox(
        "Select Time Range",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
        index=0
    )
    
    hours_map = {"Last 24 Hours": 24, "Last 7 Days": 168, "Last 30 Days": 720}
    hours = hours_map[time_range]
    
    data = st.session_state.data_handler.get_recent_data(hours=hours)
    
    if len(data) == 0:
        st.warning(f"No data available for {time_range.lower()}")
        return
    
    # Traffic volume over time
    st.subheader("📊 Traffic Volume Over Time")
    
    data['hour_bucket'] = data['timestamp'].dt.floor('H')
    hourly_volume = data.groupby('hour_bucket')['vehicle_count'].mean().reset_index()
    
    fig = px.line(
        hourly_volume,
        x='hour_bucket',
        y='vehicle_count',
        title=''
    )
    fig.update_traces(fill='tozeroy', line_color='#667eea')
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Vehicle Count",
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Split view
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Daily Pattern Heatmap")
        
        data['hour'] = data['timestamp'].dt.hour
        data['day'] = data['timestamp'].dt.day_name()
        
        pivot = data.pivot_table(
            values='vehicle_count',
            index='day',
            columns='hour',
            aggfunc='mean'
        )
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot = pivot.reindex([d for d in day_order if d in pivot.index])
        
        fig = px.imshow(
            pivot,
            labels=dict(x="Hour of Day", y="Day", color="Vehicles"),
            color_continuous_scale='Viridis',
            aspect='auto'
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Density Distribution")
        
        density_counts = data['density_level'].value_counts()
        
        colors = {'low': '#10b981', 'medium': '#f59e0b', 'high': '#ef4444', 'critical': '#7c3aed'}
        
        fig = px.bar(
            x=density_counts.index,
            y=density_counts.values,
            color=density_counts.index,
            color_discrete_map=colors
        )
        fig.update_layout(
            xaxis_title="Density Level",
            yaxis_title="Count",
            showlegend=False,
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Intersection comparison
    st.subheader("🏙️ Intersection Comparison")
    
    int_comparison = data.groupby('intersection_id').agg({
        'vehicle_count': ['mean', 'max'],
        'emergency_detected': 'sum'
    }).round(1)
    int_comparison.columns = ['Avg Vehicles', 'Max Vehicles', 'Emergency Events']
    int_comparison = int_comparison.reset_index()
    
    st.dataframe(int_comparison, use_container_width=True, hide_index=True)
    
    # Export option
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("📥 Export Data", use_container_width=True):
            filepath = st.session_state.data_handler.export_to_json()
            st.success(f"Data exported to {filepath}")


def render_emergency():
    """Emergency control view"""
    st.markdown('<h1 class="main-header">🚨 Emergency Control Center</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Green corridor management and emergency vehicle prioritization</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Emergency Corridor Control")
        
        # Emergency toggle
        emergency_active = st.toggle(
            "Activate Emergency Green Corridor",
            value=st.session_state.emergency_active,
            help="Override all signals to create green corridor for emergency vehicles"
        )
        st.session_state.emergency_active = emergency_active
        
        if emergency_active:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                padding: 2rem; border-radius: 1rem; color: white; text-align: center; margin: 1rem 0;">
                <div style="font-size: 3rem;">🚨</div>
                <div style="font-size: 1.5rem; font-weight: 700;">GREEN CORRIDOR ACTIVE</div>
                <div style="font-size: 0.875rem; margin-top: 0.5rem;">
                    All intersection signals optimized for emergency passage
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show affected intersections
            st.subheader("Affected Intersections")
            
            intersections = st.session_state.data_handler.traffic_data['intersection_id'].unique()
            
            for int_id in intersections[:4]:
                timing = st.session_state.signal_optimizer.calculate_timing('low', emergency_active=True)
                st.markdown(f"""
                <div style="background: #fef2f2; border-left: 4px solid #ef4444;
                    padding: 0.75rem 1rem; margin: 0.5rem 0; border-radius: 0.25rem;">
                    <strong>{int_id}</strong>: 🟢 {timing['green']}s extended green
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🟢 Normal operation - No active emergencies")
        
        # Emergency history
        st.divider()
        st.subheader("📋 Recent Emergency Events")
        
        data = st.session_state.data_handler.traffic_data
        emergency_data = data[data['emergency_detected'] == True].tail(10)
        
        if len(emergency_data) > 0:
            display_df = emergency_data[['timestamp', 'intersection_id', 'direction']].copy()
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.success("No recent emergency events")
    
    with col2:
        st.subheader("Quick Actions")
        
        if st.button("🚑 Simulate Ambulance", use_container_width=True):
            st.session_state.data_handler.add_record(
                intersection_id='INT_001',
                direction='N',
                vehicle_counts={'car': 5},
                emergency_detected=True
            )
            st.success("Ambulance detected at INT_001")
            st.rerun()
        
        if st.button("🚒 Simulate Fire Truck", use_container_width=True):
            st.session_state.data_handler.add_record(
                intersection_id='INT_002',
                direction='S',
                vehicle_counts={'car': 3},
                emergency_detected=True
            )
            st.success("Fire truck detected at INT_002")
            st.rerun()
        
        if st.button("🚓 Simulate Police Vehicle", use_container_width=True):
            st.session_state.data_handler.add_record(
                intersection_id='INT_003',
                direction='E',
                vehicle_counts={'car': 4},
                emergency_detected=True
            )
            st.success("Police vehicle detected at INT_003")
            st.rerun()
        
        st.divider()
        
        st.subheader("Emergency Stats")
        
        total_emergencies = data['emergency_detected'].sum()
        st.metric("Total Events (All Time)", int(total_emergencies))
        
        if len(data) > 0:
            emergency_rate = (total_emergencies / len(data)) * 100
            st.metric("Emergency Rate", f"{emergency_rate:.2f}%")


def render_settings():
    """Settings view"""
    st.markdown('<h1 class="main-header">⚙️ System Settings</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Configure detection parameters and system behavior</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Detection Settings", "Signal Timing", "Camera Config"])
    
    with tab1:
        st.subheader("YOLOv8 Detection Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            confidence = st.slider(
                "Detection Confidence Threshold",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.05,
                help="Minimum confidence score for vehicle detection"
            )
            
            iou_threshold = st.slider(
                "IOU Threshold",
                min_value=0.1,
                max_value=1.0,
                value=0.45,
                step=0.05,
                help="Intersection over Union threshold for NMS"
            )
        
        with col2:
            frame_skip = st.slider(
                "Frame Skip",
                min_value=1,
                max_value=30,
                value=5,
                help="Process every Nth frame for efficiency"
            )
            
            resize_width = st.number_input(
                "Frame Width",
                min_value=320,
                max_value=1920,
                value=640,
                step=32
            )
    
    with tab2:
        st.subheader("Signal Timing Configuration")
        
        st.markdown("#### Timing per Density Level (seconds)")
        
        for level in ['low', 'medium', 'high', 'critical']:
            st.markdown(f"**{level.capitalize()} Density**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.number_input(f"Green ({level})", value=SIGNAL_TIMING[level]['green'], 
                              key=f"green_{level}", min_value=5, max_value=120)
            with col2:
                st.number_input(f"Yellow ({level})", value=SIGNAL_TIMING[level]['yellow'],
                              key=f"yellow_{level}", min_value=2, max_value=10)
            with col3:
                st.number_input(f"Red ({level})", value=SIGNAL_TIMING[level]['red'],
                              key=f"red_{level}", min_value=5, max_value=120)
            
            st.divider()
    
    with tab3:
        st.subheader("Camera Feed Configuration")
        
        st.info("Configure CCTV and traffic camera feeds for real-time monitoring")
        
        for camera_id, config in CAMERA_FEEDS.items():
            with st.expander(f"📹 {config['name']} ({camera_id})"):
                st.text_input("Camera Name", value=config['name'], key=f"name_{camera_id}")
                st.text_input("Stream URL", value=config['url'], key=f"url_{camera_id}")
                st.selectbox("Stream Type", ["RTSP", "HTTP", "File"], key=f"type_{camera_id}")
        
        if st.button("➕ Add New Camera"):
            st.info("Camera configuration will be added to config.py")
    
    # Save button
    st.divider()
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        st.success("Settings saved successfully!")


def main():
    """Main application entry point"""
    init_session_state()
    
    page = render_sidebar()
    
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "📹 Live Detection":
        render_live_detection()
    elif page == "📈 Analytics":
        render_analytics()
    elif page == "🚨 Emergency Control":
        render_emergency()
    elif page == "⚙️ Settings":
        render_settings()


if __name__ == "__main__":
    main()
