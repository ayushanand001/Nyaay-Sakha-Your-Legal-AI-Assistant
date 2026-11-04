import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../useAuth'

const links = [
  { to: '/analyze', label: 'Review' },
  { to: '/uploads', label: 'Documents' },
  { to: '/library', label: 'Precedents' },
]

export default function Shell() {
  const { logout } = useAuth()

  return (
    <div className="workspace">
      <aside className="side">
        <NavLink to="/" className="mark">
          <span>NS</span>
          <strong>Nyaay Sakha</strong>
        </NavLink>
        <nav>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => (isActive ? 'side-link active' : 'side-link')}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <button type="button" className="text-button" onClick={logout}>
          Sign out
        </button>
      </aside>
      <main className="workspace-main">
        <Outlet />
      </main>
    </div>
  )
}
