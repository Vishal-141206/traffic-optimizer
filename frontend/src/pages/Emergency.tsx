import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  Ambulance,
  Flame,
  Shield,
  Plus,
  MapPin,
  Clock,
  CheckCircle2,
  XCircle,
  History,
  Radio,
  Navigation,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { emergencyApi } from '@/services/api'
import { useTrafficStore } from '@/store/trafficStore'
import { cn } from '@/lib/utils'

interface EmergencyEvent {
  id: number
  vehicle_type: string
  status: string
  route: number[]
  created_at: string
  resolved_at?: string
  priority: number
}

const vehicleIcons: Record<string, any> = {
  ambulance: Ambulance,
  fire_truck: Flame,
  police: Shield,
}

const vehicleColors: Record<string, { text: string; bg: string }> = {
  ambulance: { text: 'text-blue-500', bg: 'bg-blue-500/10' },
  fire_truck: { text: 'text-orange-500', bg: 'bg-orange-500/10' },
  police: { text: 'text-indigo-500', bg: 'bg-indigo-500/10' },
}

export default function Emergency() {
  const [events, setEvents] = useState<EmergencyEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedType, setSelectedType] = useState<string>('ambulance')
  const emergencyEvents = useTrafficStore((state) => state.emergencyEvents)

  useEffect(() => {
    fetchEvents()
  }, [])

  // Sync with real-time data
  useEffect(() => {
    if (emergencyEvents.length > 0) {
      setEvents((prev) => {
        const newEvents = emergencyEvents.filter(
          (e) => !prev.find((p) => p.id === e.id)
        )
        return [...newEvents, ...prev]
      })
    }
  }, [emergencyEvents])

  const fetchEvents = async () => {
    const { data } = await emergencyApi.getActiveEvents()
    if (data) {
      setEvents(data)
    } else {
      // Mock data
      setEvents([
        {
          id: 1,
          vehicle_type: 'ambulance',
          status: 'active',
          route: [1, 2, 3],
          created_at: new Date(Date.now() - 5 * 60000).toISOString(),
          priority: 1,
        },
        {
          id: 2,
          vehicle_type: 'fire_truck',
          status: 'active',
          route: [2, 4, 5, 6],
          created_at: new Date(Date.now() - 12 * 60000).toISOString(),
          priority: 1,
        },
        {
          id: 3,
          vehicle_type: 'police',
          status: 'resolved',
          route: [1, 3],
          created_at: new Date(Date.now() - 45 * 60000).toISOString(),
          resolved_at: new Date(Date.now() - 30 * 60000).toISOString(),
          priority: 2,
        },
      ])
    }
    setLoading(false)
  }

  const handleCreateEvent = async () => {
    const { data } = await emergencyApi.createEvent({
      vehicle_type: selectedType,
      route: [1, 2, 3], // In a real app, this would be calculated
    })
    if (data) {
      setEvents((prev) => [data, ...prev])
    } else {
      // Mock creation
      const newEvent: EmergencyEvent = {
        id: Date.now(),
        vehicle_type: selectedType,
        status: 'active',
        route: [1, 2, 3],
        created_at: new Date().toISOString(),
        priority: 1,
      }
      setEvents((prev) => [newEvent, ...prev])
    }
    setShowCreateModal(false)
  }

  const handleResolve = async (id: number) => {
    await emergencyApi.resolveEvent(id)
    setEvents((prev) =>
      prev.map((e) =>
        e.id === id
          ? { ...e, status: 'resolved', resolved_at: new Date().toISOString() }
          : e
      )
    )
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

  const activeEvents = events.filter((e) => e.status === 'active')
  const resolvedEvents = events.filter((e) => e.status === 'resolved')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Emergency Management
          </h1>
          <p className="text-muted-foreground mt-1">
            Green corridor control for emergency vehicles
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="gap-2">
          <Plus className="w-4 h-4" />
          Create Emergency Event
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card
          className={cn(
            activeEvents.length > 0 && "border-red-500/50 bg-red-500/5"
          )}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/10">
                <AlertTriangle className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{activeEvents.length}</p>
                <p className="text-xs text-muted-foreground">Active</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Ambulance className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {events.filter((e) => e.vehicle_type === 'ambulance').length}
                </p>
                <p className="text-xs text-muted-foreground">Ambulance</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-500/10">
                <Flame className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {events.filter((e) => e.vehicle_type === 'fire_truck').length}
                </p>
                <p className="text-xs text-muted-foreground">Fire Truck</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{resolvedEvents.length}</p>
                <p className="text-xs text-muted-foreground">Resolved Today</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-background rounded-xl p-6 w-full max-w-md shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-bold mb-4">Create Emergency Event</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Select the type of emergency vehicle to create a green corridor.
              </p>

              <div className="grid grid-cols-3 gap-3 mb-6">
                {Object.entries(vehicleIcons).map(([type, Icon]) => {
                  const colors = vehicleColors[type]
                  return (
                    <button
                      key={type}
                      onClick={() => setSelectedType(type)}
                      className={cn(
                        "p-4 rounded-xl border-2 transition-all",
                        selectedType === type
                          ? `border-current ${colors.bg} ${colors.text}`
                          : "border-transparent bg-muted hover:bg-muted/80"
                      )}
                    >
                      <Icon className={cn("w-8 h-8 mx-auto mb-2", colors.text)} />
                      <span className="text-xs font-medium capitalize">
                        {type.replace('_', ' ')}
                      </span>
                    </button>
                  )
                })}
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button className="flex-1 gap-2" onClick={handleCreateEvent}>
                  <Radio className="w-4 h-4" />
                  Activate Corridor
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Events Tabs */}
      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active" className="gap-2">
            <AlertTriangle className="w-4 h-4" />
            Active ({activeEvents.length})
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <History className="w-4 h-4" />
            History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-4">
          {activeEvents.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">
                  No Active Emergencies
                </h3>
                <p className="text-muted-foreground">
                  All routes are clear and operating normally.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {activeEvents.map((event, index) => {
                const Icon = vehicleIcons[event.vehicle_type] || AlertTriangle
                const colors = vehicleColors[event.vehicle_type] || {
                  text: 'text-red-500',
                  bg: 'bg-red-500/10',
                }

                return (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="border-red-500/50 bg-red-500/5">
                      <CardContent className="p-6">
                        <div className="flex items-start gap-4">
                          <div className={cn("p-3 rounded-xl", colors.bg)}>
                            <Icon className={cn("w-8 h-8", colors.text)} />
                          </div>

                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="text-lg font-semibold capitalize">
                                {event.vehicle_type.replace('_', ' ')} Emergency
                              </h3>
                              <div className="flex items-center gap-2">
                                <Badge variant="danger" className="animate-pulse">
                                  Active
                                </Badge>
                                <Badge variant="outline">
                                  Priority {event.priority}
                                </Badge>
                              </div>
                            </div>

                            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                              <span className="flex items-center gap-1">
                                <Clock className="w-4 h-4" />
                                {getTimeSince(event.created_at)}
                              </span>
                              <span className="flex items-center gap-1">
                                <MapPin className="w-4 h-4" />
                                {event.route.length} intersections
                              </span>
                            </div>

                            {/* Route Visualization */}
                            <div className="flex items-center gap-2 mb-4">
                              <Navigation className="w-4 h-4 text-green-500" />
                              <div className="flex items-center gap-1">
                                {event.route.map((id, idx) => (
                                  <span key={idx} className="flex items-center">
                                    <Badge
                                      variant="outline"
                                      className="text-xs bg-green-500/10 text-green-500"
                                    >
                                      #{id}
                                    </Badge>
                                    {idx < event.route.length - 1 && (
                                      <span className="mx-1 text-green-500">→</span>
                                    )}
                                  </span>
                                ))}
                              </div>
                            </div>

                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-green-500 hover:text-green-600 hover:bg-green-500/10"
                                onClick={() => handleResolve(event.id)}
                              >
                                <CheckCircle2 className="w-4 h-4 mr-1" />
                                Mark Resolved
                              </Button>
                              <Button variant="outline" size="sm">
                                <MapPin className="w-4 h-4 mr-1" />
                                View Route
                              </Button>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-4 font-medium">Type</th>
                    <th className="text-left p-4 font-medium">Created</th>
                    <th className="text-left p-4 font-medium">Resolved</th>
                    <th className="text-left p-4 font-medium">Duration</th>
                    <th className="text-left p-4 font-medium">Route</th>
                    <th className="text-left p-4 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => {
                    const Icon = vehicleIcons[event.vehicle_type] || AlertTriangle
                    const colors = vehicleColors[event.vehicle_type]
                    const created = new Date(event.created_at)
                    const resolved = event.resolved_at
                      ? new Date(event.resolved_at)
                      : null
                    const duration = resolved
                      ? Math.floor((resolved.getTime() - created.getTime()) / 60000)
                      : null

                    return (
                      <tr key={event.id} className="border-b hover:bg-muted/30">
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div className={cn("p-1.5 rounded-lg", colors?.bg)}>
                              <Icon className={cn("w-4 h-4", colors?.text)} />
                            </div>
                            <span className="capitalize">
                              {event.vehicle_type.replace('_', ' ')}
                            </span>
                          </div>
                        </td>
                        <td className="p-4 text-muted-foreground">
                          {created.toLocaleString()}
                        </td>
                        <td className="p-4 text-muted-foreground">
                          {resolved?.toLocaleString() || '-'}
                        </td>
                        <td className="p-4 text-muted-foreground">
                          {duration ? `${duration} min` : '-'}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-1">
                            {event.route.slice(0, 3).map((id, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                #{id}
                              </Badge>
                            ))}
                            {event.route.length > 3 && (
                              <span className="text-xs text-muted-foreground">
                                +{event.route.length - 3}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge
                            variant={
                              event.status === 'active' ? 'danger' : 'success'
                            }
                          >
                            {event.status}
                          </Badge>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
