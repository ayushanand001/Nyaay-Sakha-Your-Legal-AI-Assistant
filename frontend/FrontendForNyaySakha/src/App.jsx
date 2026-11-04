import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './useAuth'
import Shell from './components/Shell'
import Analyze from './pages/Analyze'
import Library from './pages/Library'
import LibraryCase from './pages/LibraryCase'
import Login from './pages/Login'
import Register from './pages/Register'
import Uploads from './pages/Uploads'
import Verify from './pages/Verify'
import Welcome from './pages/Welcome'

function RequireAuth({ children }) {
  const { token } = useAuth()
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Welcome />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify" element={<Verify />} />
      <Route
        element={(
          <RequireAuth>
            <Shell />
          </RequireAuth>
        )}
      >
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/uploads" element={<Uploads />} />
        <Route path="/library" element={<Library />} />
        <Route path="/library/:caseId" element={<LibraryCase />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
