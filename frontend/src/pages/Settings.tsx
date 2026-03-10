import { useState } from 'react'
import {
  Settings as SettingsIcon,
  Sun,
  Moon,
  Bell,
  Shield,
  Database,
  Wifi,
  Save,
  RefreshCw,
  Server,
  Clock,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useThemeStore } from '@/store/themeStore'
import { useTrafficStore } from '@/store/trafficStore'
import { cn } from '@/lib/utils'

export default function Settings() {
  const { isDark, toggleTheme } = useThemeStore()
  const isConnected = useTrafficStore((state) => state.isConnected)
  
  const [settings, setSettings] = useState({
    // Notifications
    enableNotifications: true,
    emergencyAlerts: true,
    congestionAlerts: true,
    systemAlerts: false,
    
    // Signal Control
    autoOptimize: true,
    emergencyOverride: true,
    minGreenTime: 10,
    maxGreenTime: 60,
    yellowTime: 3,
    
    // System
    dataRetention: 30,
    refreshInterval: 5,
    debugMode: false,
  })

  const updateSetting = (key: string, value: any) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = () => {
    // In production, this would save to backend
    console.log('Settings saved:', settings)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Configure system preferences and controls
          </p>
        </div>
        <Button onClick={handleSave} className="gap-2">
          <Save className="w-4 h-4" />
          Save Changes
        </Button>
      </div>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
              <div className="flex items-center gap-3">
                <Wifi className={cn(
                  "w-5 h-5",
                  isConnected ? "text-green-500" : "text-red-500"
                )} />
                <span className="font-medium">WebSocket</span>
              </div>
              <Badge variant={isConnected ? "success" : "danger"}>
                {isConnected ? "Connected" : "Disconnected"}
              </Badge>
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
              <div className="flex items-center gap-3">
                <Database className="w-5 h-5 text-blue-500" />
                <span className="font-medium">Database</span>
              </div>
              <Badge variant="success">Online</Badge>
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
              <div className="flex items-center gap-3">
                <Zap className="w-5 h-5 text-yellow-500" />
                <span className="font-medium">AI Model</span>
              </div>
              <Badge variant="success">Active</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="appearance">
        <TabsList>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="signals">Signal Control</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        {/* Appearance */}
        <TabsContent value="appearance" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
              <CardDescription>
                Choose your preferred color scheme
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {isDark ? (
                    <Moon className="w-5 h-5 text-blue-500" />
                  ) : (
                    <Sun className="w-5 h-5 text-yellow-500" />
                  )}
                  <div>
                    <p className="font-medium">Dark Mode</p>
                    <p className="text-sm text-muted-foreground">
                      {isDark ? "Dark theme is enabled" : "Light theme is enabled"}
                    </p>
                  </div>
                </div>
                <Switch checked={isDark} onCheckedChange={toggleTheme} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Configure which alerts you want to receive
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-2">
                <div>
                  <p className="font-medium">Enable Notifications</p>
                  <p className="text-sm text-muted-foreground">
                    Receive desktop notifications
                  </p>
                </div>
                <Switch
                  checked={settings.enableNotifications}
                  onCheckedChange={(v) => updateSetting('enableNotifications', v)}
                />
              </div>
              <div className="flex items-center justify-between py-2 border-t">
                <div>
                  <p className="font-medium">Emergency Alerts</p>
                  <p className="text-sm text-muted-foreground">
                    Get notified for emergency vehicle events
                  </p>
                </div>
                <Switch
                  checked={settings.emergencyAlerts}
                  onCheckedChange={(v) => updateSetting('emergencyAlerts', v)}
                />
              </div>
              <div className="flex items-center justify-between py-2 border-t">
                <div>
                  <p className="font-medium">Congestion Alerts</p>
                  <p className="text-sm text-muted-foreground">
                    Get notified when traffic reaches critical levels
                  </p>
                </div>
                <Switch
                  checked={settings.congestionAlerts}
                  onCheckedChange={(v) => updateSetting('congestionAlerts', v)}
                />
              </div>
              <div className="flex items-center justify-between py-2 border-t">
                <div>
                  <p className="font-medium">System Alerts</p>
                  <p className="text-sm text-muted-foreground">
                    Receive system maintenance notifications
                  </p>
                </div>
                <Switch
                  checked={settings.systemAlerts}
                  onCheckedChange={(v) => updateSetting('systemAlerts', v)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Signal Control */}
        <TabsContent value="signals" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Signal Timing Configuration
              </CardTitle>
              <CardDescription>
                Configure traffic signal timing parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-2">
                <div>
                  <p className="font-medium">Auto Optimization</p>
                  <p className="text-sm text-muted-foreground">
                    Automatically optimize signal timing based on traffic
                  </p>
                </div>
                <Switch
                  checked={settings.autoOptimize}
                  onCheckedChange={(v) => updateSetting('autoOptimize', v)}
                />
              </div>
              <div className="flex items-center justify-between py-2 border-t">
                <div>
                  <p className="font-medium">Emergency Override</p>
                  <p className="text-sm text-muted-foreground">
                    Allow emergency vehicles to override signals
                  </p>
                </div>
                <Switch
                  checked={settings.emergencyOverride}
                  onCheckedChange={(v) => updateSetting('emergencyOverride', v)}
                />
              </div>
              
              <div className="space-y-4 pt-4 border-t">
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Minimum Green Time (seconds): {settings.minGreenTime}s
                  </label>
                  <input
                    type="range"
                    min={5}
                    max={30}
                    value={settings.minGreenTime}
                    onChange={(e) => updateSetting('minGreenTime', parseInt(e.target.value))}
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Maximum Green Time (seconds): {settings.maxGreenTime}s
                  </label>
                  <input
                    type="range"
                    min={30}
                    max={120}
                    value={settings.maxGreenTime}
                    onChange={(e) => updateSetting('maxGreenTime', parseInt(e.target.value))}
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Yellow Light Duration (seconds): {settings.yellowTime}s
                  </label>
                  <input
                    type="range"
                    min={2}
                    max={5}
                    value={settings.yellowTime}
                    onChange={(e) => updateSetting('yellowTime', parseInt(e.target.value))}
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System */}
        <TabsContent value="system" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                System Configuration
              </CardTitle>
              <CardDescription>
                Advanced system settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Data Retention (days): {settings.dataRetention}
                </label>
                <input
                  type="range"
                  min={7}
                  max={90}
                  value={settings.dataRetention}
                  onChange={(e) => updateSetting('dataRetention', parseInt(e.target.value))}
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <p className="text-xs text-muted-foreground">
                  How long to keep historical traffic data
                </p>
              </div>
              
              <div className="space-y-2 pt-4 border-t">
                <label className="text-sm font-medium">
                  Dashboard Refresh Interval (seconds): {settings.refreshInterval}s
                </label>
                <input
                  type="range"
                  min={1}
                  max={30}
                  value={settings.refreshInterval}
                  onChange={(e) => updateSetting('refreshInterval', parseInt(e.target.value))}
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                />
              </div>
              
              <div className="flex items-center justify-between py-4 border-t">
                <div>
                  <p className="font-medium">Debug Mode</p>
                  <p className="text-sm text-muted-foreground">
                    Show detailed logging information
                  </p>
                </div>
                <Switch
                  checked={settings.debugMode}
                  onCheckedChange={(v) => updateSetting('debugMode', v)}
                />
              </div>
              
              <div className="pt-4 border-t">
                <Button variant="outline" className="w-full gap-2">
                  <RefreshCw className="w-4 h-4" />
                  Reset to Default Settings
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>About</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Version</span>
                <span className="font-medium">1.0.0</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Build Date</span>
                <span className="font-medium">{new Date().toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">License</span>
                <span className="font-medium">MIT</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
