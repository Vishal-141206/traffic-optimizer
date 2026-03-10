import { useEffect, useState } from 'react'
import {
  Camera,
  Plus,
  Search,
  Video,
  VideoOff,
  Settings,
  Eye,
  RefreshCw,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { camerasApi } from '@/services/api'
import { cn } from '@/lib/utils'

interface CameraInfo {
  id: number
  name: string
  intersection_id: number
  direction: string
  status: string
  fps: number
  resolution: string
  last_maintenance: string
}

export default function Cameras() {
  const [cameras, setCameras] = useState<CameraInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCamera, setSelectedCamera] = useState<CameraInfo | null>(null)

  useEffect(() => {
    fetchCameras()
  }, [])

  const fetchCameras = async () => {
    const { data, error } = await camerasApi.getAll()
    if (data) {
      setCameras(data)
    } else {
      // Mock data
      setCameras([
        {
          id: 1,
          name: 'CAM-001-N',
          intersection_id: 1,
          direction: 'north',
          status: 'online',
          fps: 30,
          resolution: '1920x1080',
          last_maintenance: '2024-01-15',
        },
        {
          id: 2,
          name: 'CAM-001-S',
          intersection_id: 1,
          direction: 'south',
          status: 'online',
          fps: 30,
          resolution: '1920x1080',
          last_maintenance: '2024-01-15',
        },
        {
          id: 3,
          name: 'CAM-001-E',
          intersection_id: 1,
          direction: 'east',
          status: 'online',
          fps: 30,
          resolution: '1920x1080',
          last_maintenance: '2024-01-15',
        },
        {
          id: 4,
          name: 'CAM-001-W',
          intersection_id: 1,
          direction: 'west',
          status: 'offline',
          fps: 0,
          resolution: '1920x1080',
          last_maintenance: '2024-01-10',
        },
        {
          id: 5,
          name: 'CAM-002-N',
          intersection_id: 2,
          direction: 'north',
          status: 'online',
          fps: 25,
          resolution: '1280x720',
          last_maintenance: '2024-01-12',
        },
        {
          id: 6,
          name: 'CAM-002-S',
          intersection_id: 2,
          direction: 'south',
          status: 'online',
          fps: 25,
          resolution: '1280x720',
          last_maintenance: '2024-01-12',
        },
      ])
    }
    setLoading(false)
  }

  const filteredCameras = cameras.filter((camera) =>
    camera.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const onlineCameras = cameras.filter((c) => c.status === 'online').length
  const offlineCameras = cameras.filter((c) => c.status === 'offline').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cameras</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage traffic cameras
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Add Camera
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Camera className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{cameras.length}</p>
                <p className="text-xs text-muted-foreground">Total Cameras</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <Video className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{onlineCameras}</p>
                <p className="text-xs text-muted-foreground">Online</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/10">
                <VideoOff className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{offlineCameras}</p>
                <p className="text-xs text-muted-foreground">Offline</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/10">
                <Eye className="w-5 h-5 text-purple-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {cameras.reduce((sum, c) => sum + (c.status === 'online' ? c.fps : 0), 0)}
                </p>
                <p className="text-xs text-muted-foreground">Total FPS</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search cameras..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Camera Grid */}
      <Tabs defaultValue="grid">
        <TabsList>
          <TabsTrigger value="grid">Grid View</TabsTrigger>
          <TabsTrigger value="list">List View</TabsTrigger>
        </TabsList>

        <TabsContent value="grid" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {loading ? (
              [...Array(8)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <div className="aspect-video bg-muted" />
                  <CardContent className="p-4">
                    <div className="h-4 bg-muted rounded w-3/4 mb-2" />
                    <div className="h-3 bg-muted rounded w-1/2" />
                  </CardContent>
                </Card>
              ))
            ) : (
              filteredCameras.map((camera, index) => (
                <motion.div
                  key={camera.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card
                    className={cn(
                      "overflow-hidden hover:shadow-lg transition-all cursor-pointer",
                      selectedCamera?.id === camera.id && "ring-2 ring-primary"
                    )}
                    onClick={() => setSelectedCamera(camera)}
                  >
                    {/* Camera Feed Placeholder */}
                    <div className="relative aspect-video bg-muted">
                      {camera.status === 'online' ? (
                        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
                          <div className="text-center">
                            <Video className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
                            <p className="text-xs text-muted-foreground">
                              Live Feed
                            </p>
                          </div>
                          {/* Recording indicator */}
                          <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 rounded-full bg-red-500/20 text-red-500">
                            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                            <span className="text-xs font-medium">REC</span>
                          </div>
                        </div>
                      ) : (
                        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                          <div className="text-center">
                            <VideoOff className="w-12 h-12 text-red-500 mx-auto mb-2" />
                            <p className="text-xs text-muted-foreground">
                              Offline
                            </p>
                          </div>
                        </div>
                      )}
                      {/* FPS Badge */}
                      <Badge
                        className="absolute bottom-2 left-2"
                        variant={camera.status === 'online' ? 'success' : 'secondary'}
                      >
                        {camera.fps} FPS
                      </Badge>
                    </div>

                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold">{camera.name}</h3>
                          <p className="text-xs text-muted-foreground capitalize">
                            {camera.direction} • Intersection #{camera.intersection_id}
                          </p>
                        </div>
                        <Badge
                          variant={camera.status === 'online' ? 'success' : 'danger'}
                          className="capitalize"
                        >
                          {camera.status}
                        </Badge>
                      </div>
                      
                      <div className="flex gap-2 mt-3">
                        <Button variant="outline" size="sm" className="flex-1 gap-1">
                          <Eye className="w-3 h-3" />
                          View
                        </Button>
                        <Button variant="outline" size="sm" className="gap-1">
                          <Settings className="w-3 h-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="list" className="mt-4">
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-4 font-medium">Camera</th>
                    <th className="text-left p-4 font-medium">Intersection</th>
                    <th className="text-left p-4 font-medium">Direction</th>
                    <th className="text-left p-4 font-medium">Status</th>
                    <th className="text-left p-4 font-medium">Resolution</th>
                    <th className="text-left p-4 font-medium">FPS</th>
                    <th className="text-left p-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCameras.map((camera) => (
                    <tr key={camera.id} className="border-b hover:bg-muted/30">
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <Camera className="w-4 h-4 text-muted-foreground" />
                          <span className="font-medium">{camera.name}</span>
                        </div>
                      </td>
                      <td className="p-4 text-muted-foreground">
                        #{camera.intersection_id}
                      </td>
                      <td className="p-4 capitalize text-muted-foreground">
                        {camera.direction}
                      </td>
                      <td className="p-4">
                        <Badge
                          variant={camera.status === 'online' ? 'success' : 'danger'}
                        >
                          {camera.status}
                        </Badge>
                      </td>
                      <td className="p-4 text-muted-foreground">
                        {camera.resolution}
                      </td>
                      <td className="p-4 text-muted-foreground">{camera.fps}</td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <RefreshCw className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Settings className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
