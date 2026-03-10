import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  MapPin,
  Plus,
  Search,
  Filter,
  MoreVertical,
  Trash2,
  Edit2,
  Radio,
  Activity,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { intersectionsApi } from '@/services/api'
import { cn, getCongestionColor, getCongestionBgColor } from '@/lib/utils'

interface Intersection {
  id: number
  name: string
  location: { lat: number; lng: number }
  status: string
  congestion_level: string
  active_cameras: number
  vehicle_count: number
}

export default function Intersections() {
  const [intersections, setIntersections] = useState<Intersection[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<string | null>(null)

  useEffect(() => {
    fetchIntersections()
  }, [])

  const fetchIntersections = async () => {
    const { data, error } = await intersectionsApi.getAll()
    if (data) {
      setIntersections(data)
    } else {
      // Mock data for development
      setIntersections([
        {
          id: 1,
          name: 'Main St & 1st Ave',
          location: { lat: 40.7128, lng: -74.006 },
          status: 'active',
          congestion_level: 'medium',
          active_cameras: 4,
          vehicle_count: 45,
        },
        {
          id: 2,
          name: 'Oak Blvd & Park Rd',
          location: { lat: 40.7148, lng: -74.008 },
          status: 'active',
          congestion_level: 'low',
          active_cameras: 2,
          vehicle_count: 12,
        },
        {
          id: 3,
          name: 'Highway 101 & Exit 5',
          location: { lat: 40.7168, lng: -74.01 },
          status: 'active',
          congestion_level: 'high',
          active_cameras: 6,
          vehicle_count: 87,
        },
        {
          id: 4,
          name: 'Central Ave & 5th St',
          location: { lat: 40.7188, lng: -74.012 },
          status: 'maintenance',
          congestion_level: 'low',
          active_cameras: 0,
          vehicle_count: 0,
        },
      ])
    }
    setLoading(false)
  }

  const filteredIntersections = intersections.filter((intersection) => {
    const matchesSearch = intersection.name
      .toLowerCase()
      .includes(searchQuery.toLowerCase())
    const matchesFilter = !filterStatus || intersection.status === filterStatus
    return matchesSearch && matchesFilter
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Intersections</h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor traffic intersections
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Add Intersection
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search intersections..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={filterStatus === null ? 'default' : 'outline'}
            onClick={() => setFilterStatus(null)}
          >
            All
          </Button>
          <Button
            variant={filterStatus === 'active' ? 'default' : 'outline'}
            onClick={() => setFilterStatus('active')}
          >
            Active
          </Button>
          <Button
            variant={filterStatus === 'maintenance' ? 'default' : 'outline'}
            onClick={() => setFilterStatus('maintenance')}
          >
            Maintenance
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Radio className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{intersections.length}</p>
                <p className="text-xs text-muted-foreground">Total</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <Activity className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {intersections.filter((i) => i.status === 'active').length}
                </p>
                <p className="text-xs text-muted-foreground">Active</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-500/10">
                <Activity className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {intersections.filter((i) => i.congestion_level === 'high').length}
                </p>
                <p className="text-xs text-muted-foreground">High Traffic</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/10">
                <MapPin className="w-5 h-5 text-purple-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {intersections.reduce((sum, i) => sum + i.active_cameras, 0)}
                </p>
                <p className="text-xs text-muted-foreground">Cameras</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Intersections Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          [...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-6 bg-muted rounded w-3/4 mb-4" />
                <div className="h-4 bg-muted rounded w-1/2 mb-2" />
                <div className="h-4 bg-muted rounded w-1/3" />
              </CardContent>
            </Card>
          ))
        ) : filteredIntersections.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <MapPin className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium">No intersections found</h3>
            <p className="text-sm text-muted-foreground">
              Try adjusting your search or filters
            </p>
          </div>
        ) : (
          filteredIntersections.map((intersection, index) => (
            <motion.div
              key={intersection.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          "p-2 rounded-lg",
                          getCongestionBgColor(intersection.congestion_level)
                        )}
                      >
                        <MapPin
                          className={cn(
                            "w-5 h-5",
                            getCongestionColor(intersection.congestion_level)
                          )}
                        />
                      </div>
                      <div>
                        <h3 className="font-semibold">{intersection.name}</h3>
                        <p className="text-xs text-muted-foreground">
                          ID: #{intersection.id}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Status</span>
                      <Badge
                        variant={
                          intersection.status === 'active'
                            ? 'success'
                            : 'secondary'
                        }
                        className="capitalize"
                      >
                        {intersection.status}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">
                        Congestion
                      </span>
                      <Badge
                        variant="outline"
                        className={cn(
                          "capitalize",
                          getCongestionColor(intersection.congestion_level)
                        )}
                      >
                        {intersection.congestion_level}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">
                        Vehicles
                      </span>
                      <span className="font-medium">
                        {intersection.vehicle_count}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">
                        Cameras
                      </span>
                      <span className="font-medium">
                        {intersection.active_cameras}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2 mt-4 pt-4 border-t">
                    <Button variant="outline" size="sm" className="flex-1 gap-1">
                      <Edit2 className="w-3 h-3" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 gap-1 text-red-500 hover:text-red-600"
                    >
                      <Trash2 className="w-3 h-3" />
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
      </div>
    </div>
  )
}
