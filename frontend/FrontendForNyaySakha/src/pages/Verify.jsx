import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../useAuth'
import { Banner, Field } from '../components/ui'
import { AuthFrame } from './Login'

export default function Verify() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const registrationId = location.state?.registrationId
    || sessionStorage.getItem('nyaysakha_registration')
  const email = location.state?.email
    || sessionStorage.getItem('nyaysakha_registration_email')
  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [pending, setPending] = useState(false)

  if (token) return <Navigate to="/analyze" replace />

  if (!registrationId) {
    return (
      <AuthFrame title="Verify email" lede="Start registration to receive a code.">
        <Link className="button" to="/register">Create an account</Link>
      </AuthFrame>
    )
  }

  async function onSubmit(event) {
    event.preventDefault()
    setError('')
    setNotice('')
    setPending(true)

    try {
      await api('/auth/verify-registration', {
        method: 'POST',
        json: { registration_id: registrationId, otp: otp.trim() },
      })
      sessionStorage.removeItem('nyaysakha_registration')
      sessionStorage.removeItem('nyaysakha_registration_email')
      navigate('/login', { replace: true, state: { verified: true } })
    } catch (err) {
      setError(err.message)
    } finally {
      setPending(false)
    }
  }

  async function resend() {
    setError('')
    setNotice('')
    setPending(true)

    try {
      await api('/auth/resend-otp', {
        method: 'POST',
        json: { registration_id: registrationId },
      })
      setNotice('A new code is on its way. The previous code is no longer valid.')
    } catch (err) {
      setError(err.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <AuthFrame
      title="Enter the code"
      lede={email ? `Sent to ${email}.` : 'Enter the six-digit code from your email.'}
    >
      <form className="stack" onSubmit={onSubmit}>
        <Banner>{error}</Banner>
        <Banner kind="ok">{notice}</Banner>
        <Field label="Verification code" hint="Valid for 10 minutes.">
          <input
            inputMode="numeric"
            autoComplete="one-time-code"
            value={otp}
            onChange={(event) => setOtp(event.target.value)}
            minLength={6}
            maxLength={6}
            pattern="[0-9]{6}"
            required
          />
        </Field>
        <button className="button" type="submit" disabled={pending}>
          {pending ? 'Checking…' : 'Verify and continue'}
        </button>
      </form>
      <p className="form-note">
        <button type="button" className="text-button" onClick={resend} disabled={pending}>
          Resend code
        </button>
      </p>
    </AuthFrame>
  )
}
