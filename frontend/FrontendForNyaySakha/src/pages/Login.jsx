import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../useAuth'
import { Banner, Field } from '../components/ui'

export default function Login() {
  const { token, saveToken } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  if (token) return <Navigate to="/analyze" replace />

  async function onSubmit(event) {
    event.preventDefault()
    setError('')
    setPending(true)

    try {
      const data = await api('/auth/login', {
        method: 'POST',
        json: { email, password },
      })
      saveToken(data.token)
      navigate(location.state?.from || '/analyze', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <AuthFrame
      title="Sign in"
      lede="Use the account you verified for NyayaSetu."
    >
      <form className="stack" onSubmit={onSubmit}>
        <Banner kind="ok">
          {location.state?.verified ? 'Email verified. Sign in to continue.' : ''}
        </Banner>
        <Banner>{error}</Banner>
        <Field label="Email">
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </Field>
        <Field label="Password">
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </Field>
        <button className="button" type="submit" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p className="form-note">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </AuthFrame>
  )
}

export function AuthFrame({ title, lede, children }) {
  return (
    <div className="public auth-screen">
      <Link to="/" className="mark">
        <span>NS</span>
        <strong>NyayaSetu</strong>
      </Link>
      <section className="paper auth-card">
        <h1>{title}</h1>
        <p className="lede">{lede}</p>
        {children}
      </section>
    </div>
  )
}
