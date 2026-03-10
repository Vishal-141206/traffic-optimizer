import { useEffect, useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { signalsApi } from '@/services/api'
import { useTrafficStore } from '@/store/trafficStore'
import { cn, getSignalColor } from '@/lib/utils'

interface IntersectionSimulatorProps {
  intersectionId: number
}

interface Vehicle {
  id: number
  x: number
  y: number
  direction: 'north' | 'south' | 'east' | 'west'
  speed: number
  waiting: boolean
}

interface SignalState {
  direction: string
  state: string
  remaining_time: number
}

export default function IntersectionSimulator({ intersectionId }: IntersectionSimulatorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [signals, setSignals] = useState<SignalState[]>([
    { direction: 'north', state: 'green', remaining_time: 25 },
    { direction: 'south', state: 'green', remaining_time: 25 },
    { direction: 'east', state: 'red', remaining_time: 25 },
    { direction: 'west', state: 'red', remaining_time: 25 },
  ])
  const signalStates = useTrafficStore((state) => state.signalStates)
  const animationRef = useRef<number>()

  // Update signals from real-time data
  useEffect(() => {
    const realtimeSignals = signalStates.filter(
      (s) => s.intersection_id === intersectionId
    )
    if (realtimeSignals.length > 0) {
      setSignals(
        realtimeSignals.map((s) => ({
          direction: s.direction,
          state: s.state,
          remaining_time: s.remaining_time,
        }))
      )
    }
  }, [signalStates, intersectionId])

  // Generate random vehicles
  useEffect(() => {
    const interval = setInterval(() => {
      const directions: Vehicle['direction'][] = ['north', 'south', 'east', 'west']
      const direction = directions[Math.floor(Math.random() * directions.length)]
      
      const startPositions = {
        north: { x: 110, y: 0 },
        south: { x: 140, y: 250 },
        east: { x: 250, y: 110 },
        west: { x: 0, y: 140 },
      }
      
      const { x, y } = startPositions[direction]
      
      setVehicles((prev) => {
        if (prev.length > 12) return prev
        return [
          ...prev,
          {
            id: Date.now(),
            x,
            y,
            direction,
            speed: 1 + Math.random(),
            waiting: false,
          },
        ]
      })
    }, 800)

    return () => clearInterval(interval)
  }, [])

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // Draw road
      drawRoad(ctx, canvas.width, canvas.height)
      
      // Draw signals
      drawSignals(ctx)
      
      // Update and draw vehicles
      setVehicles((prev) => {
        return prev.filter((vehicle) => {
          const signal = signals.find(
            (s) => s.direction === vehicle.direction
          )
          const isGreen = signal?.state === 'green'
          
          // Check if vehicle should stop
          const stopPositions = {
            north: 80,
            south: 170,
            east: 170,
            west: 80,
          }
          
          const stopPos = stopPositions[vehicle.direction]
          const shouldStop =
            !isGreen &&
            ((vehicle.direction === 'north' && vehicle.y < stopPos && vehicle.y > stopPos - 30) ||
            (vehicle.direction === 'south' && vehicle.y > stopPos && vehicle.y < stopPos + 30) ||
            (vehicle.direction === 'east' && vehicle.x > stopPos && vehicle.x < stopPos + 30) ||
            (vehicle.direction === 'west' && vehicle.x < stopPos && vehicle.x > stopPos - 30))
          
          vehicle.waiting = shouldStop
          
          if (!shouldStop) {
            // Move vehicle
            switch (vehicle.direction) {
              case 'north':
                vehicle.y += vehicle.speed
                break
              case 'south':
                vehicle.y -= vehicle.speed
                break
              case 'east':
                vehicle.x -= vehicle.speed
                break
              case 'west':
                vehicle.x += vehicle.speed
                break
            }
          }
          
          // Draw vehicle
          drawVehicle(ctx, vehicle)
          
          // Remove if out of bounds
          return (
            vehicle.x >= -20 &&
            vehicle.x <= canvas.width + 20 &&
            vehicle.y >= -20 &&
            vehicle.y <= canvas.height + 20
          )
        })
      })
      
      animationRef.current = requestAnimationFrame(animate)
    }
    
    animationRef.current = requestAnimationFrame(animate)
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [signals])

  const drawRoad = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    // Background
    ctx.fillStyle = '#1a1a2e'
    ctx.fillRect(0, 0, width, height)
    
    // Roads
    ctx.fillStyle = '#4a4a6a'
    
    // Horizontal road
    ctx.fillRect(0, 90, width, 70)
    
    // Vertical road
    ctx.fillRect(90, 0, 70, height)
    
    // Center lines
    ctx.strokeStyle = '#fcd34d'
    ctx.lineWidth = 2
    ctx.setLineDash([10, 10])
    
    // Horizontal center line
    ctx.beginPath()
    ctx.moveTo(0, 125)
    ctx.lineTo(90, 125)
    ctx.moveTo(160, 125)
    ctx.lineTo(width, 125)
    ctx.stroke()
    
    // Vertical center line
    ctx.beginPath()
    ctx.moveTo(125, 0)
    ctx.lineTo(125, 90)
    ctx.moveTo(125, 160)
    ctx.lineTo(125, height)
    ctx.stroke()
    
    ctx.setLineDash([])
    
    // Stop lines
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 3
    
    // North
    ctx.beginPath()
    ctx.moveTo(90, 85)
    ctx.lineTo(125, 85)
    ctx.stroke()
    
    // South
    ctx.beginPath()
    ctx.moveTo(125, 165)
    ctx.lineTo(160, 165)
    ctx.stroke()
    
    // East
    ctx.beginPath()
    ctx.moveTo(165, 90)
    ctx.lineTo(165, 125)
    ctx.stroke()
    
    // West
    ctx.beginPath()
    ctx.moveTo(85, 125)
    ctx.lineTo(85, 160)
    ctx.stroke()
  }

  const drawSignals = (ctx: CanvasRenderingContext2D) => {
    const signalPositions = {
      north: { x: 70, y: 70 },
      south: { x: 180, y: 180 },
      east: { x: 180, y: 70 },
      west: { x: 70, y: 180 },
    }
    
    signals.forEach((signal) => {
      const pos = signalPositions[signal.direction as keyof typeof signalPositions]
      const colors = {
        red: '#ef4444',
        yellow: '#fbbf24',
        green: '#22c55e',
      }
      
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, 8, 0, Math.PI * 2)
      ctx.fillStyle = colors[signal.state as keyof typeof colors] || '#6b7280'
      ctx.fill()
      
      // Glow effect
      ctx.shadowColor = colors[signal.state as keyof typeof colors] || '#6b7280'
      ctx.shadowBlur = 10
      ctx.fill()
      ctx.shadowBlur = 0
    })
  }

  const drawVehicle = (ctx: CanvasRenderingContext2D, vehicle: Vehicle) => {
    ctx.save()
    ctx.translate(vehicle.x, vehicle.y)
    
    const rotations = {
      north: 0,
      south: Math.PI,
      east: -Math.PI / 2,
      west: Math.PI / 2,
    }
    
    ctx.rotate(rotations[vehicle.direction])
    
    // Car body
    const gradient = ctx.createLinearGradient(-7, -10, -7, 10)
    gradient.addColorStop(0, vehicle.waiting ? '#ef4444' : '#60a5fa')
    gradient.addColorStop(1, vehicle.waiting ? '#b91c1c' : '#2563eb')
    
    ctx.beginPath()
    ctx.roundRect(-7, -10, 14, 20, 3)
    ctx.fillStyle = gradient
    ctx.fill()
    
    // Windshield
    ctx.fillStyle = '#1e3a5f'
    ctx.fillRect(-5, -7, 10, 6)
    
    // Headlights
    ctx.fillStyle = '#fcd34d'
    ctx.fillRect(-6, 7, 4, 2)
    ctx.fillRect(2, 7, 4, 2)
    
    ctx.restore()
  }

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={250}
        height={250}
        className="w-full rounded-lg"
      />
      
      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-3 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-muted-foreground">Go</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <span className="text-muted-foreground">Caution</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-muted-foreground">Stop</span>
        </div>
      </div>
      
      {/* Signal Timer */}
      <div className="grid grid-cols-4 gap-2 mt-3">
        {signals.map((signal) => (
          <div
            key={signal.direction}
            className="flex flex-col items-center p-2 rounded-lg bg-muted/50"
          >
            <div
              className={cn(
                "w-4 h-4 rounded-full mb-1",
                getSignalColor(signal.state)
              )}
            />
            <span className="text-xs font-medium capitalize">{signal.direction[0]}</span>
            <span className="text-xs font-mono text-muted-foreground">
              {signal.remaining_time}s
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
