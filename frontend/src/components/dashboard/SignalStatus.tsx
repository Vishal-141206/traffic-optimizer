import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { signalsApi } from '@/services/api'
import { useTrafficStore } from '@/store/trafficStore'
import { cn, getSignalColor } from '@/lib/utils'
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-react'

interface SignalStatusProps {
  intersectionId: number
}

interface SignalState {
  direction: string
  state: string
  remaining_time: number
}

const directionIcons = {
  north: ArrowUp,
  south: ArrowDown,
  east: ArrowRight,
  west: ArrowLeft,
}

const directionLabels = {
  north: 'N',
  south: 'S',
  east: 'E',
  west: 'W',
}

export default function SignalStatus({ intersectionId }: SignalStatusProps) {
  const [signals, setSignals] = useState<SignalState[]>([])
  const [loading, setLoading] = useState(true)
  const signalStates = useTrafficStore((state) => state.signalStates)

  useEffect(() => {
    fetchSignals()
    const interval = setInterval(fetchSignals, 5000)
    return () => clearInterval(interval)
  }, [intersectionId])

  // Update from real-time WebSocket data
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

  const fetchSignals = async () => {
    const { data, error } = await signalsApi.getSignalState(intersectionId)
    if (data && Array.isArray(data)) {
      setSignals(
        data.map((s: any) => ({
          direction: s.direction,
          state: s.state,
          remaining_time: s.remaining_time || 0,
        }))
      )
    } else if (data) {
      // Mock data if single signal returned
      setSignals([
        { direction: 'north', state: 'green', remaining_time: 25 },
        { direction: 'south', state: 'green', remaining_time: 25 },
        { direction: 'east', state: 'red', remaining_time: 25 },
        { direction: 'west', state: 'red', remaining_time: 25 },
      ])
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  // Default signals if none loaded
  const displaySignals = signals.length > 0 
    ? signals 
    : [
        { direction: 'north', state: 'green', remaining_time: 25 },
        { direction: 'south', state: 'green', remaining_time: 25 },
        { direction: 'east', state: 'red', remaining_time: 25 },
        { direction: 'west', state: 'red', remaining_time: 25 },
      ]

  return (
    <div className="space-y-4">
      {/* Visual Signal Display */}
      <div className="relative aspect-square bg-muted/50 rounded-xl p-4">
        {/* Center dot representing intersection */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-foreground/20 rounded-full" />
        
        {/* Signal lights */}
        {displaySignals.map((signal) => {
          const Icon = directionIcons[signal.direction as keyof typeof directionIcons]
          const positions = {
            north: 'top-2 left-1/2 -translate-x-1/2',
            south: 'bottom-2 left-1/2 -translate-x-1/2',
            east: 'right-2 top-1/2 -translate-y-1/2',
            west: 'left-2 top-1/2 -translate-y-1/2',
          }
          
          return (
            <motion.div
              key={signal.direction}
              className={cn(
                "absolute flex flex-col items-center gap-1",
                positions[signal.direction as keyof typeof positions]
              )}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center shadow-lg",
                  getSignalColor(signal.state),
                  signal.state === 'yellow' && 'animate-pulse'
                )}
              >
                {Icon && <Icon className="w-5 h-5 text-white" />}
              </div>
              <span className="text-xs font-mono font-bold">
                {signal.remaining_time}s
              </span>
            </motion.div>
          )
        })}
      </div>

      {/* Signal List */}
      <div className="grid grid-cols-2 gap-2">
        {displaySignals.map((signal) => (
          <div
            key={signal.direction}
            className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
          >
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "w-3 h-3 rounded-full",
                  getSignalColor(signal.state)
                )}
              />
              <span className="text-sm font-medium capitalize">
                {signal.direction}
              </span>
            </div>
            <span className="text-xs font-mono text-muted-foreground">
              {signal.remaining_time}s
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
