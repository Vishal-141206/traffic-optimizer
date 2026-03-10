import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Car,
  AlertTriangle,
  Timer,
  TrendingUp,
  Activity,
  Gauge,
  Radio,
  Clock,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { useTrafficStore } from '@/store/trafficStore'
import { analyticsApi, videoApi } from '@/services/api'
import { cn, formatNumber, getCongestionColor, getCongestionBgColor } from '@/lib/utils'
import TrafficChart from '@/components/dashboard/TrafficChart'
import SignalStatus from '@/components/dashboard/SignalStatus'
import EmergencyPanel from '@/components/dashboard/EmergencyPanel'
import IntersectionSimulator from '@/components/dashboard/IntersectionSimulator'

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [simulationRunning, setSimulationRunning] = useState(false)

  const isConnected = useTrafficStore((state) => state.isConnected)
  const lastUpdate = useTrafficStore((state) => state.lastUpdate)

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchDashboardData = async () => {
    const { data, error } = await analyticsApi.getDashboard()
    if (data) {
      setDashboardData(data)
    }
    setLoading(false)
  }

  const startSimulation = async () => {
    setSimulationRunning(true)
    const { data, error } = await videoApi.startSimulation(1, 60)
    if (data) {
      console.log('Simulation started:', data)
    }
  }

  const stats = [
    {
      label: 'Active Intersections',
      value: dashboardData?.active_intersections || 0,
      icon: Radio,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'Vehicles Detected',
      value: dashboardData?.current_vehicles || 0,
      icon: Car,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      label: 'Active Emergencies',
      value: dashboardData?.active_emergencies || 0,
      icon: AlertTriangle,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
      alert: (dashboardData?.active_emergencies || 0) > 0,
    },
    {
      label: 'Congestion Level',
      value: dashboardData?.overall_congestion || 'low',
      icon: Gauge,
      color: getCongestionColor(dashboardData?.overall_congestion || 'low'),
      bgColor: getCongestionBgColor(dashboardData?.overall_congestion || 'low'),
      isStatus: true,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Traffic Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Real-time traffic monitoring and signal control
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm">
              {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : '--:--:--'}
            </span>
          </div>
          <Button
            onClick={startSimulation}
            disabled={simulationRunning}
            className="gap-2"
          >
            <Activity className="w-4 h-4" />
            {simulationRunning ? 'Simulating...' : 'Start Simulation'}
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card
              className={cn(
                "relative overflow-hidden transition-all duration-300 hover:shadow-lg",
                stat.alert && "border-red-500/50 animate-pulse"
              )}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      {stat.label}
                    </p>
                    {stat.isStatus ? (
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-sm font-semibold capitalize",
                          stat.color
                        )}
                      >
                        {stat.value}
                      </Badge>
                    ) : (
                      <p className="text-3xl font-bold">
                        {formatNumber(stat.value as number)}
                      </p>
                    )}
                  </div>
                  <div className={cn("p-3 rounded-xl", stat.bgColor)}>
                    <stat.icon className={cn("w-6 h-6", stat.color)} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Traffic Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Traffic Trends
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TrafficChart />
          </CardContent>
        </Card>

        {/* Signal Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Timer className="w-5 h-5" />
              Signal Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SignalStatus intersectionId={1} />
          </CardContent>
        </Card>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Intersection Simulator */}
        <Card>
          <CardHeader>
            <CardTitle>Intersection Simulation</CardTitle>
          </CardHeader>
          <CardContent>
            <IntersectionSimulator intersectionId={1} />
          </CardContent>
        </Card>

        {/* Emergency Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              Emergency Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <EmergencyPanel />
          </CardContent>
        </Card>
      </div>

      {/* Congestion Distribution */}
      {dashboardData?.congestion_distribution && (
        <Card>
          <CardHeader>
            <CardTitle>Congestion Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(dashboardData.congestion_distribution).map(
                ([level, count]: [string, any]) => {
                  const total = Object.values(
                    dashboardData.congestion_distribution
                  ).reduce((a: number, b: any) => a + b, 0) as number
                  const percentage = total > 0 ? (count / total) * 100 : 0

                  return (
                    <div key={level} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className={cn("capitalize font-medium", getCongestionColor(level))}>
                          {level}
                        </span>
                        <span className="text-muted-foreground">
                          {count} ({percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <Progress
                        value={percentage}
                        className={cn(
                          "h-2",
                          level === 'low' && "[&>div]:bg-green-500",
                          level === 'medium' && "[&>div]:bg-yellow-500",
                          level === 'high' && "[&>div]:bg-orange-500",
                          level === 'critical' && "[&>div]:bg-red-500"
                        )}
                      />
                    </div>
                  )
                }
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
