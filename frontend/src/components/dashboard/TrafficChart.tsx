import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { useThemeStore } from '@/store/themeStore'
import { analyticsApi } from '@/services/api'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface TrafficDataPoint {
  time: string
  vehicles: number
  north: number
  south: number
  east: number
  west: number
}

function generateMockData(): TrafficDataPoint[] {
  const currentHour = new Date().getHours()
  return Array.from({ length: 12 }, (_, i) => {
    const hour = (currentHour - 11 + i + 24) % 24
    const baseTraffic = 
      (hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 19)
        ? 80
        : hour >= 10 && hour <= 16
        ? 50
        : 20
    
    const variance = () => Math.floor(Math.random() * 20 - 10)
    
    return {
      time: `${String(hour).padStart(2, '0')}:00`,
      vehicles: baseTraffic + variance(),
      north: Math.floor((baseTraffic + variance()) / 4),
      south: Math.floor((baseTraffic + variance()) / 4),
      east: Math.floor((baseTraffic + variance()) / 4),
      west: Math.floor((baseTraffic + variance()) / 4),
    }
  })
}

export default function TrafficChart() {
  const isDark = useThemeStore((state) => state.isDark)
  const [data, setData] = useState<TrafficDataPoint[]>([])
  const [activeView, setActiveView] = useState<'total' | 'directions'>('total')

  useEffect(() => {
    // Initial mock data
    setData(generateMockData())

    // Fetch real data
    fetchTrafficTrends()
    
    // Update every 30 seconds
    const interval = setInterval(() => {
      setData(generateMockData())
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const fetchTrafficTrends = async () => {
    const { data: trends } = await analyticsApi.getTrafficTrends('1', 'hour')
    if (trends && trends.length > 0) {
      const formattedData = trends.map((item: any) => ({
        time: new Date(item.timestamp).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
        }),
        vehicles: item.vehicle_count || 0,
        north: item.direction_counts?.north || 0,
        south: item.direction_counts?.south || 0,
        east: item.direction_counts?.east || 0,
        west: item.direction_counts?.west || 0,
      }))
      setData(formattedData)
    }
  }

  const chartColors = {
    total: isDark ? '#3b82f6' : '#2563eb',
    north: '#22c55e',
    south: '#f59e0b',
    east: '#8b5cf6',
    west: '#ec4899',
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#6b7280',
  }

  return (
    <div className="h-[300px]">
      <Tabs value={activeView} onValueChange={(v) => setActiveView(v as any)}>
        <TabsList className="mb-4">
          <TabsTrigger value="total">Total Traffic</TabsTrigger>
          <TabsTrigger value="directions">By Direction</TabsTrigger>
        </TabsList>
        
        <TabsContent value="total" className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorVehicles" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColors.total} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={chartColors.total} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={chartColors.grid}
                vertical={false}
              />
              <XAxis
                dataKey="time"
                stroke={chartColors.text}
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke={chartColors.text}
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                  borderRadius: '8px',
                }}
              />
              <Area
                type="monotone"
                dataKey="vehicles"
                stroke={chartColors.total}
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorVehicles)"
                name="Vehicles"
              />
            </AreaChart>
          </ResponsiveContainer>
        </TabsContent>
        
        <TabsContent value="directions" className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={chartColors.grid}
                vertical={false}
              />
              <XAxis
                dataKey="time"
                stroke={chartColors.text}
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke={chartColors.text}
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? '#1f2937' : '#ffffff',
                  border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="north"
                stroke={chartColors.north}
                strokeWidth={2}
                dot={false}
                name="North"
              />
              <Line
                type="monotone"
                dataKey="south"
                stroke={chartColors.south}
                strokeWidth={2}
                dot={false}
                name="South"
              />
              <Line
                type="monotone"
                dataKey="east"
                stroke={chartColors.east}
                strokeWidth={2}
                dot={false}
                name="East"
              />
              <Line
                type="monotone"
                dataKey="west"
                stroke={chartColors.west}
                strokeWidth={2}
                dot={false}
                name="West"
              />
            </LineChart>
          </ResponsiveContainer>
        </TabsContent>
      </Tabs>
    </div>
  )
}
