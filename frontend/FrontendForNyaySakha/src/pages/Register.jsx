import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../useAuth'
import { Banner, Field } from '../components/ui'
import { AuthFrame } from './Login'

export default function Register() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
  })
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  if (token) return <Navigate to="/analyze" replace />

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function onSubmit(event) {
    event.preventDefault()
    setError('')
    setPending(true)

    try {
      const data = await api('/auth/register', {
        method: 'POST',
        json: {
          name: form.name.trim(),
          email: form.email.trim(),
          phone: form.phone.trim(),
          password: form.password,
        },
      })
      sessionStorage.setItem('nyaysakha_registration', data.registration_id)
      sessionStorage.setItem('nyaysakha_registration_email', form.email.trim())
      navigate('/verify', {
        state: {
          registrationId: data.registration_id,
          email: form.email.trim(),
        },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <AuthFrame
      title="Create an account"
      lede="A verification code will be sent to your email. It stays valid for 10 minutes."
    >
      <form className="stack" onSubmit={onSubmit}>
        <Banner>{error}</Banner>
        <Field label="Full name">
          <input
            value={form.name}
            onChange={(event) => update('name', event.target.value)}
            autoComplete="name"
            required
          />
        </Field>
        <Field label="Email">
          <input
            type="email"
            value={form.email}
            onChange={(event) => update('email', event.target.value)}
            autoComplete="email"
            required
          />
        </Field>
        <Field label="Phone">
          <input
            type="tel"
            value={form.phone}
            onChange={(event) => update('phone', event.target.value)}
            autoComplete="tel"
            required
          />
        </Field>
        <Field label="Password">
          <input
            type="password"
            value={form.password}
            onChange={(event) => update('password', event.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </Field>
        <button className="button" type="submit" disabled={pending}>
          {pending ? 'Sending code…' : 'Send verification code'}
        </button>
      </form>
      <p className="form-note">
        Already registered? <Link to="/login">Sign in</Link>
      </p>
    </AuthFrame>
  )
}
