const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ApiResponse<T> {
  data?: T
  error?: string
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return { data }
  } catch (error) {
    console.error('API request failed:', error)
    return { error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

// Intersections API
export const intersectionsApi = {
  getAll: (activeOnly = true) =>
    apiRequest<any[]>(`/api/intersections/?active_only=${activeOnly}`),
  
  getById: (id: number) =>
    apiRequest<any>(`/api/intersections/${id}`),
  
  create: (data: any) =>
    apiRequest<any>('/api/intersections/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: number, data: any) =>
    apiRequest<any>(`/api/intersections/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  delete: (id: number) =>
    apiRequest<void>(`/api/intersections/${id}`, { method: 'DELETE' }),
  
  getStatus: (id: number) =>
    apiRequest<any>(`/api/intersections/${id}/status`),
}

// Cameras API
export const camerasApi = {
  getAll: (intersectionId?: number) =>
    apiRequest<any[]>(`/api/cameras/${intersectionId ? `?intersection_id=${intersectionId}` : ''}`),
  
  getById: (id: number) =>
    apiRequest<any>(`/api/cameras/${id}`),
  
  create: (data: any) =>
    apiRequest<any>('/api/cameras/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: number, data: any) =>
    apiRequest<any>(`/api/cameras/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
}

// Traffic API
export const trafficApi = {
  getMetrics: (intersectionId?: number, hours = 24) =>
    apiRequest<any[]>(
      `/api/traffic/metrics?hours=${hours}${intersectionId ? `&intersection_id=${intersectionId}` : ''}`
    ),
  
  getCurrent: (intersectionId?: number) =>
    apiRequest<any>(
      `/api/traffic/current${intersectionId ? `?intersection_id=${intersectionId}` : ''}`
    ),
  
  getCongestionSummary: (hours = 1) =>
    apiRequest<any>(`/api/traffic/congestion-summary?hours=${hours}`),
  
  getDensityHistory: (intersectionId: number, hours = 24) =>
    apiRequest<any>(
      `/api/traffic/density-history?intersection_id=${intersectionId}&hours=${hours}`
    ),
}

// Signals API
export const signalsApi = {
  getCurrent: (intersectionId: number) =>
    apiRequest<any>(`/api/signals/${intersectionId}/current`),
  
  getHistory: (intersectionId: number, hours = 24) =>
    apiRequest<any>(`/api/signals/${intersectionId}/history?hours=${hours}`),
  
  triggerEmergencyOverride: (intersectionId: number, direction: string) =>
    apiRequest<any>(`/api/signals/${intersectionId}/emergency-override?direction=${direction}`, {
      method: 'POST',
    }),
  
  resetSignals: (intersectionId: number) =>
    apiRequest<any>(`/api/signals/${intersectionId}/reset`, { method: 'POST' }),
}

// Emergency API
export const emergencyApi = {
  getAll: (activeOnly = false, hours = 24) =>
    apiRequest<any[]>(`/api/emergency/?active_only=${activeOnly}&hours=${hours}`),
  
  getActive: () =>
    apiRequest<any>('/api/emergency/active'),
  
  create: (data: any) =>
    apiRequest<any>('/api/emergency/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  activateCorridor: (eventId: number, route: number[]) =>
    apiRequest<any>(`/api/emergency/${eventId}/activate-corridor`, {
      method: 'POST',
      body: JSON.stringify({ corridor_route: route }),
    }),
  
  resolve: (eventId: number, notes?: string) =>
    apiRequest<any>(`/api/emergency/${eventId}/resolve?notes=${notes || ''}`, {
      method: 'POST',
    }),
  
  getStats: (hours = 168) =>
    apiRequest<any>(`/api/emergency/stats/summary?hours=${hours}`),
}

// Analytics API
export const analyticsApi = {
  getDashboard: () =>
    apiRequest<any>('/api/analytics/dashboard'),
  
  getTrafficTrends: (hours = 24, intervalMinutes = 30) =>
    apiRequest<any>(`/api/analytics/traffic-trends?hours=${hours}&interval_minutes=${intervalMinutes}`),
  
  getPeakHours: (days = 7) =>
    apiRequest<any>(`/api/analytics/peak-hours?days=${days}`),
  
  getIntersectionAnalytics: (id: number, days = 7) =>
    apiRequest<any>(`/api/analytics/intersection/${id}?days=${days}`),
  
  getVehicleDistribution: (hours = 24) =>
    apiRequest<any>(`/api/analytics/vehicle-distribution?hours=${hours}`),
  
  getCongestionHeatmap: (hours = 24) =>
    apiRequest<any>(`/api/analytics/congestion-heatmap?hours=${hours}`),
}

// Video Feed API
export const videoApi = {
  uploadVideo: async (file: File, cameraId = 1, intersectionId = 1) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(
      `${API_BASE_URL}/api/video/upload?camera_id=${cameraId}&intersection_id=${intersectionId}`,
      {
        method: 'POST',
        body: formData,
      }
    )
    
    if (!response.ok) {
      throw new Error('Upload failed')
    }
    
    return response.json()
  },
  
  getStatus: (fileId: string) =>
    apiRequest<any>(`/api/video/status/${fileId}`),
  
  getResults: (fileId: string) =>
    apiRequest<any>(`/api/video/results/${fileId}`),
  
  startSimulation: (intersectionId = 1, durationSeconds = 60) =>
    apiRequest<any>(
      `/api/video/simulate?intersection_id=${intersectionId}&duration_seconds=${durationSeconds}`,
      { method: 'POST' }
    ),
}

export { API_BASE_URL }
