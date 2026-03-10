import { create } from 'zustand'
import type {
  Intersection,
  TrafficCamera,
  TrafficMetric,
  SignalStateRecord,
  EmergencyEvent,
  DashboardSummary,
  CongestionLevel,
  Direction,
  SignalState,
  VehicleType,
} from '@/types'

interface TrafficState {
  // Data
  intersections: Intersection[]
  cameras: TrafficCamera[]
  currentMetrics: Record<number, TrafficMetric[]> // by intersection_id
  signalStates: Record<number, Record<Direction, SignalStateRecord>> // by intersection_id, then direction
  emergencyEvents: EmergencyEvent[]
  dashboardSummary: DashboardSummary | null
  
  // WebSocket state
  isConnected: boolean
  lastUpdate: string | null
  
  // Actions
  setIntersections: (intersections: Intersection[]) => void
  setCameras: (cameras: TrafficCamera[]) => void
  updateMetrics: (intersectionId: number, metrics: TrafficMetric[]) => void
  updateSignalStates: (intersectionId: number, signals: Record<Direction, SignalStateRecord>) => void
  addEmergencyEvent: (event: EmergencyEvent) => void
  resolveEmergencyEvent: (eventId: number) => void
  setDashboardSummary: (summary: DashboardSummary) => void
  setConnected: (connected: boolean) => void
  setLastUpdate: (timestamp: string) => void
  
  // Real-time update handlers
  handleTrafficUpdate: (data: {
    intersection_id: number
    vehicles: Record<VehicleType, number>
    total_vehicles: number
    congestion_level: CongestionLevel
    density: number
  }) => void
  handleSignalUpdate: (data: {
    intersection_id: number
    signals: Record<Direction, { phase: SignalState; time_remaining: number; is_emergency: boolean }>
  }) => void
  handleEmergencyAlert: (data: {
    event_id: number
    intersection_id: number
    emergency_type: string
    approach_direction: Direction
    message: string
  }) => void
}

export const useTrafficStore = create<TrafficState>((set, get) => ({
  // Initial state
  intersections: [],
  cameras: [],
  currentMetrics: {},
  signalStates: {},
  emergencyEvents: [],
  dashboardSummary: null,
  isConnected: false,
  lastUpdate: null,
  
  // Actions
  setIntersections: (intersections) => set({ intersections }),
  setCameras: (cameras) => set({ cameras }),
  
  updateMetrics: (intersectionId, metrics) => set((state) => ({
    currentMetrics: {
      ...state.currentMetrics,
      [intersectionId]: metrics,
    },
  })),
  
  updateSignalStates: (intersectionId, signals) => set((state) => ({
    signalStates: {
      ...state.signalStates,
      [intersectionId]: signals,
    },
  })),
  
  addEmergencyEvent: (event) => set((state) => ({
    emergencyEvents: [event, ...state.emergencyEvents.slice(0, 99)],
  })),
  
  resolveEmergencyEvent: (eventId) => set((state) => ({
    emergencyEvents: state.emergencyEvents.map((e) =>
      e.id === eventId ? { ...e, resolved_at: new Date().toISOString() } : e
    ),
  })),
  
  setDashboardSummary: (summary) => set({ dashboardSummary: summary }),
  setConnected: (connected) => set({ isConnected: connected }),
  setLastUpdate: (timestamp) => set({ lastUpdate: timestamp }),
  
  // Real-time handlers
  handleTrafficUpdate: (data) => {
    const { intersection_id, total_vehicles, congestion_level, density } = data
    
    set((state) => {
      const newMetric: TrafficMetric = {
        id: Date.now(),
        intersection_id,
        lane_id: 1,
        direction: 'north',
        vehicle_count: total_vehicles,
        congestion_level,
        density,
        throughput: 0,
        timestamp: new Date().toISOString(),
      }
      
      const existing = state.currentMetrics[intersection_id] || []
      
      return {
        currentMetrics: {
          ...state.currentMetrics,
          [intersection_id]: [newMetric, ...existing.slice(0, 49)],
        },
        lastUpdate: new Date().toISOString(),
      }
    })
  },
  
  handleSignalUpdate: (data) => {
    const { intersection_id, signals } = data
    
    set((state) => {
      const convertedSignals: Record<Direction, SignalStateRecord> = {} as Record<Direction, SignalStateRecord>
      
      for (const [direction, signal] of Object.entries(signals)) {
        convertedSignals[direction as Direction] = {
          id: Date.now(),
          intersection_id,
          lane_id: ['north', 'south', 'east', 'west'].indexOf(direction) + 1,
          direction: direction as Direction,
          state: signal.phase,
          duration: signal.time_remaining,
          is_emergency_override: signal.is_emergency,
          started_at: new Date().toISOString(),
          time_remaining: signal.time_remaining,
        }
      }
      
      return {
        signalStates: {
          ...state.signalStates,
          [intersection_id]: convertedSignals,
        },
        lastUpdate: new Date().toISOString(),
      }
    })
  },
  
  handleEmergencyAlert: (data) => {
    const event: EmergencyEvent = {
      id: data.event_id,
      intersection_id: data.intersection_id,
      emergency_type: data.emergency_type as EmergencyEvent['emergency_type'],
      approach_direction: data.approach_direction,
      corridor_activated: true,
      confidence: 0.9,
      detected_at: new Date().toISOString(),
    }
    
    get().addEmergencyEvent(event)
  },
}))

// Selectors
export const selectActiveEmergencies = (state: TrafficState) =>
  state.emergencyEvents.filter((e) => !e.resolved_at)

export const selectIntersectionById = (id: number) => (state: TrafficState) =>
  state.intersections.find((i) => i.id === id)

export const selectSignalsForIntersection = (id: number) => (state: TrafficState) =>
  state.signalStates[id]

export const selectMetricsForIntersection = (id: number) => (state: TrafficState) =>
  state.currentMetrics[id] || []
