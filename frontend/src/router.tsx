// TODO: [MOCK_REGISTRY] Mock router config - Next.js uses file-based routing
import { createBrowserRouter } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Tenants from './components/Tenants'
import Settings from './components/Settings'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Dashboard />,
  },
  {
    path: '/dashboard',
    element: <Dashboard />,
  },
  {
    path: '/tenants',
    element: <Tenants />,
  },
  {
    path: '/settings',
    element: <Settings />,
  },
])