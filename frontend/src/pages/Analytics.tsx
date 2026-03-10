import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Car,
  Calendar,
  Download,
  RefreshCw,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { analyticsApi } from '@/services/api'
import { useThemeStore } from '@/store/themeStore'
import { cn } from '@/lib/utils'

// Generate mock hourly data
const generateHourlyData = () => {
  return Array.from({ length: 24 }, (_, i) => {
    const hour = i
    const isPeak = (hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 19)
    const baseTraffic = isPeak ? 150 : hour >= 10 && hour <= 16 ? 80 : 30
    
    return {
      hour: `${String(hour).padStart(2, '0')}:00`,
      vehicles: baseTraffic + Math.floor(Math.random() * 30 - 15),
      avgSpeed: isPeak ? 25 + Math.random() * 10 : 45 + Math.random() * 15,
      waitTime: isPeak ? 45 + Math.random() * 30 : 15 + Math.random() * 10,
    }
  })
}

// Generate weekly data
const generateWeeklyData = () => {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  return days.map((day, i) => ({
    day,
    vehicles: i < 5 ? 8000 + Math.floor(Math.random() * 2000) : 4000 + Math.floor(Math.random() * 1500),
    incidents: Math.floor(Math.random() * 5),
    emergencies: Math.floor(Math.random() * 3),
  }))
}

// Congestion distribution data
const congestionData = [
  { name: 'Low', value: 45, color: '#22c55e' },
  { name: 'Medium', value: 30, color: '#f59e0b' },
  { name: 'High', value: 18, color: '#f97316' },
  { name: 'Critical', value: 7, color: '#ef4444' },
]

// Direction distribution
const directionData = [
  { direction: 'North', count: 2500 },
  { direction: 'South', count: 2300 },
  { direction: 'East', count: 1800 },
  { direction: 'West', count: 1900 },
]

export default function Analytics() {
  const isDark = useThemeStore((state) => state.isDark)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('day')
  const [hourlyData] = useState(generateHourlyData())
  const [weeklyData] = useState(generateWeeklyData())

  const chartColors = {
    primary: isDark ? '#3b82f6' : '#2563eb',
    secondary: isDark ? '#22c55e' : '#16a34a',
    warning: '#f59e0b',
    danger: '#ef4444',
    grid: isDark ? '#374151' : '#e5e7eb',
    text: isDark ? '#9ca3af' : '#6b7280',
  }

  useEffect(() => {
    // Simulate loading
    setTimeout(() => setLoading(false), 500)
  }, [])

  const stats = [
    {
      label: 'Total Vehicles Today',
      value: '12,847',
      change: '+12%',
      trend: 'up',
      icon: Car,
    },
    {
      label: 'Average Wait Time',
      value: '28s',
      change: '-8%',
      trend: 'down',
      icon: Clock,
    },
    {
      label: 'Peak Hour Traffic',
      value: '1,245',
      change: '+5%',
      trend: 'up',
      icon: TrendingUp,
    },
    {
      label: 'Signal Efficiency',
      value: '94%',
      change: '+3%',
      trend: 'up',
      icon: TrendingUp,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Traffic patterns and performance insights
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Time Range Selector */}
      <Tabs value={timeRange} onValueChange={(v) => setTimeRange(v as any)}>
        <TabsList>
          <TabsTrigger value="day">Today</TabsTrigger>
          <TabsTrigger value="week">This Week</TabsTrigger>
          <TabsTrigger value="month">This Month</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    {stat.label}
                  </p>
                  <p className="text-3xl font-bold mt-1">{stat.value}</p>
                </div>
                <div
                  className={cn(
                    "p-3 rounded-xl",
                    stat.trend === 'up' ? 'bg-green-500/10' : 'bg-blue-500/10'
                  )}
                >
                  <stat.icon
                    className={cn(
                      "w-6 h-6",
                      stat.trend === 'up' ? 'text-green-500' : 'text-blue-500'
                    )}
                  />
                </div>
              </div>
              <div className="flex items-center gap-1 mt-2">
                {stat.trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 text-green-500" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-green-500" />
                )}
                <span
                  className={cn(
                    "text-sm font-medium",
                    stat.trend === 'up' ? 'text-green-500' : 'text-green-500'
                  )}
                >
                  {stat.change}
                </span>
                <span className="text-sm text-muted-foreground">
                  vs last period
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Traffic */}
        <Card>
          <CardHeader>
            <CardTitle>Hourly Traffic Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={hourlyData}>
                  <defs>
                    <linearGradient id="colorVehicles" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={chartColors.primary} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={chartColors.primary} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                  <XAxis
                    dataKey="hour"
                    stroke={chartColors.text}
                    fontSize={12}
                    tickLine={false}
                  />
                  <YAxis
                    stroke={chartColors.text}
                    fontSize={12}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: isDark ? '#1f2937' : '#fff',
                      border: `1px solid ${chartColors.grid}`,
                      borderRadius: '8px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="vehicles"
                    stroke={chartColors.primary}
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorVehicles)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Congestion Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Congestion Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex items-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={congestionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {congestionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: isDark ? '#1f2937' : '#fff',
                      border: `1px solid ${chartColors.grid}`,
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Comparison */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Traffic Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                  <XAxis
                    dataKey="day"
                    stroke={chartColors.text}
                    fontSize={12}
                    tickLine={false}
                  />
                  <YAxis
                    stroke={chartColors.text}
                    fontSize={12}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: isDark ? '#1f2937' : '#fff',
                      border: `1px solid ${chartColors.grid}`,
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  <Bar
                    dataKey="vehicles"
                    fill={chartColors.primary}
                    radius={[4, 4, 0, 0]}
                    name="Vehicles"
                  />
                  <Bar
                    dataKey="emergencies"
                    fill={chartColors.danger}
                    radius={[4, 4, 0, 0]}
                    name="Emergencies"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Direction Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Traffic by Direction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={directionData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                  <XAxis
                    type="number"
                    stroke={chartColors.text}
                    fontSize={12}
                    tickLine={false}
                  />
                  <YAxis
                    dataKey="direction"
                    type="category"
                    stroke={chartColors.text}
                    fontSize={12}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: isDark ? '#1f2937' : '#fff',
                      border: `1px solid ${chartColors.grid}`,
                      borderRadius: '8px',
                    }}
                  />
                  <Bar
                    dataKey="count"
                    fill={chartColors.secondary}
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={hourlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                <XAxis
                  dataKey="hour"
                  stroke={chartColors.text}
                  fontSize={12}
                  tickLine={false}
                />
                <YAxis
                  yAxisId="left"
                  stroke={chartColors.text}
                  fontSize={12}
                  tickLine={false}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke={chartColors.text}
                  fontSize={12}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: isDark ? '#1f2937' : '#fff',
                    border: `1px solid ${chartColors.grid}`,
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="avgSpeed"
                  stroke={chartColors.primary}
                  strokeWidth={2}
                  dot={false}
                  name="Avg Speed (km/h)"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="waitTime"
                  stroke={chartColors.warning}
                  strokeWidth={2}
                  dot={false}
                  name="Wait Time (s)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
