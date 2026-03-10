import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  Ambulance,
  Flame,
  Shield,
  Clock,
  MapPin,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { emergencyApi } from '@/services/api'
import { useTrafficStore } from '@/store/trafficStore'
import { cn } from '@/lib/utils'

interface EmergencyEvent {
  id: number
  vehicle_type: string
  status: string
  route: number[]
  created_at: string
  priority: number
}

const vehicleIcons: Record<string, any> = {
  ambulance: Ambulance,
  fire_truck: Flame,
  police: Shield,
}

const vehicleColors: Record<string, string> = {
  ambulance: 'text-blue-500 bg-blue-500/10',
  fire_truck: 'text-orange-500 bg-orange-500/10',
  police: 'text-indigo-500 bg-indigo-500/10',
}

export default function EmergencyPanel() {
  const [emergencies, setEmergencies] = useState<EmergencyEvent[]>([])
  const [loading, setLoading] = useState(true)
  const emergencyEvents = useTrafficStore((state) => state.emergencyEvents)

  useEffect(() => {
    fetchEmergencies()
    const interval = setInterval(fetchEmergencies, 10000)
    return () => clearInterval(interval)
  }, [])

  // Sync with real-time emergency events
  useEffect(() => {
    if (emergencyEvents.length > 0) {
      const formattedEvents = emergencyEvents.map((e) => ({
        id: e.id,
        vehicle_type: e.vehicle_type,
        status: e.status,
        route: e.route || [],
        created_at: e.created_at,
        priority: e.priority,
      }))
      setEmergencies(formattedEvents)
    }
  }, [emergencyEvents])

  const fetchEmergencies = async () => {
    const { data } = await emergencyApi.getActiveEvents()
    if (data) {
      setEmergencies(data)
    }
    setLoading(false)
  }

  const handleResolve = async (id: number) => {
    await emergencyApi.resolveEvent(id)
    setEmergencies((prev) => prev.filter((e) => e.id !== id))
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTimeSince = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (seconds < 60) return `${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    return `${hours}h ago`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (emergencies.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[200px] text-center">
        <CheckCircle2 className="w-12 h-12 text-green-500 mb-3" />
        <p className="text-lg font-medium">No Active Emergencies</p>
        <p className="text-sm text-muted-foreground">
          All routes are clear
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3 max-h-[300px] overflow-y-auto">
      <AnimatePresence>
        {emergencies.map((emergency, index) => {
          const Icon = vehicleIcons[emergency.vehicle_type] || AlertTriangle
          const colorClass = vehicleColors[emergency.vehicle_type] || 'text-red-500 bg-red-500/10'
          
          return (
            <motion.div
              key={emergency.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "p-3 rounded-lg border",
                emergency.status === 'active' && "border-red-500/50 bg-red-500/5 animate-pulse"
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn("p-2 rounded-lg", colorClass)}>
                  <Icon className="w-5 h-5" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="font-medium capitalize">
                      {emergency.vehicle_type.replace('_', ' ')}
                    </h4>
                    <Badge
                      variant={emergency.status === 'active' ? 'danger' : 'secondary'}
                      className="capitalize"
                    >
                      {emergency.status}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {getTimeSince(emergency.created_at)}
                    </span>
                    {emergency.route?.length > 0 && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {emergency.route.length} intersections
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      Priority: {emergency.priority}
                    </span>
                  </div>
                  
                  {emergency.route?.length > 0 && (
                    <div className="flex items-center gap-1 mt-2">
                      {emergency.route.slice(0, 5).map((id, idx) => (
                        <span key={idx}>
                          <Badge variant="outline" className="text-xs px-1.5">
                            #{id}
                          </Badge>
                          {idx < Math.min(emergency.route.length - 1, 4) && (
                            <span className="text-muted-foreground mx-0.5">→</span>
                          )}
                        </span>
                      ))}
                      {emergency.route.length > 5 && (
                        <span className="text-xs text-muted-foreground">
                          +{emergency.route.length - 5} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleResolve(emergency.id)}
                  className="text-green-500 hover:text-green-600 hover:bg-green-500/10"
                >
                  <CheckCircle2 className="w-4 h-4" />
                </Button>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
