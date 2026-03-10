// Traffic System Types

export type CongestionLevel = 'low' | 'medium' | 'high' | 'critical'
export type SignalState = 'red' | 'yellow' | 'green' | 'flashing'
export type VehicleType = 'car' | 'bus' | 'truck' | 'motorcycle' | 'bicycle' | 'emergency'
export type EmergencyType = 'ambulance' | 'fire_truck' | 'police' | 'other'
export type Direction = 'north' | 'south' | 'east' | 'west'

export interface Intersection {
  id: number
  name: string
  location_lat: number
  location_lng: number
  description?: string
  num_lanes: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TrafficCamera {
  id: number
  intersection_id: number
  name: string
  stream_url?: string
  lane_id: number
  direction: Direction
  is_active: boolean
  last_frame_at?: string
  created_at: string
}

export interface VehicleCount {
  id: number
  camera_id: number
  vehicle_type: VehicleType
  count: number
  confidence: number
  timestamp: string
}

export interface SignalStateRecord {
  id: number
  intersection_id: number
  lane_id: number
  direction: Direction
  state: SignalState
  duration: number
  is_emergency_override: boolean
  started_at: string
  ended_at?: string
  time_remaining?: number
}

export interface TrafficMetric {
  id: number
  intersection_id: number
  lane_id: number
  direction: Direction
  vehicle_count: number
  congestion_level: CongestionLevel
  density: number
  average_speed?: number
  wait_time?: number
  throughput: number
  timestamp: string
}

export interface EmergencyEvent {
  id: number
  intersection_id: number
  emergency_type: EmergencyType
  vehicle_plate?: string
  approach_direction: Direction
  corridor_activated: boolean
  corridor_route?: number[]
  confidence: number
  detected_at: string
  resolved_at?: string
  notes?: string
}

// Dashboard Types
export interface DashboardSummary {
  active_intersections: number
  current_vehicles: number
  active_emergencies: number
  overall_congestion: CongestionLevel
  congestion_distribution: Record<CongestionLevel, number>
  recent_alerts: Alert[]
  timestamp: string
}

export interface Alert {
  type: 'emergency' | 'congestion' | 'system'
  message: string
  intersection_id?: number
  timestamp: string
  severity: 'low' | 'medium' | 'high'
}

// Analytics Types
export interface TrafficTrend {
  timestamp: string
  total_vehicles: number
  avg_density: number
  avg_congestion_score: number
}

export interface PeakHoursData {
  analysis_days: number
  peak_hours: number[]
  low_traffic_hours: number[]
  hourly_breakdown: {
    hour: number
    avg_vehicles: number
    avg_density: number
  }[]
}

export interface VehicleDistribution {
  period_hours: number
  total_vehicles: number
  distribution: Record<VehicleType, number>
  percentages: Record<VehicleType, number>
}

export interface IntersectionAnalytics {
  intersection_id: number
  intersection_name: string
  analysis_period_days: number
  total_vehicles_detected: number
  average_wait_time_seconds: number
  average_density: number
  congestion_distribution: Record<CongestionLevel, number>
  emergency_events: number
  signal_changes: number
  efficiency_score: number
}

// Real-time Updates
export interface RealtimeTrafficUpdate {
  type: 'traffic_update'
  data: {
    intersection_id: number
    vehicles: Record<VehicleType, number>
    total_vehicles: number
    congestion_level: CongestionLevel
    density: number
    emergency_detected: boolean
  }
  timestamp: string
}

export interface RealtimeSignalUpdate {
  type: 'signal_update'
  data: {
    intersection_id: number
    signals: Record<Direction, {
      phase: SignalState
      time_remaining: number
      is_emergency: boolean
    }>
  }
  timestamp: string
}

export interface RealtimeEmergencyAlert {
  type: 'emergency_alert'
  data: {
    event_id: number
    intersection_id: number
    emergency_type: EmergencyType
    approach_direction: Direction
    corridor_route?: number[]
    message: string
  }
  timestamp: string
}

// Simulation Types
export interface SimulationConfig {
  intersection_id: number
  duration_seconds: number
  traffic_intensity: 'low' | 'medium' | 'high'
  emergency_probability: number
}

export interface SimulationResult {
  simulation_id: string
  status: 'running' | 'completed' | 'error'
  progress: number
  results: TrafficMetric[]
}
