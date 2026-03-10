import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useThemeStore } from '@/store/themeStore'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import Intersections from '@/pages/Intersections'
import Analytics from '@/pages/Analytics'
import Cameras from '@/pages/Cameras'
import Emergency from '@/pages/Emergency'
import Settings from '@/pages/Settings'

function App() {
  const { theme } = useThemeStore()

  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme)
  }, [theme])

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/intersections" element={<Intersections />} />
          <Route path="/cameras" element={<Cameras />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/emergency" element={<Emergency />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
