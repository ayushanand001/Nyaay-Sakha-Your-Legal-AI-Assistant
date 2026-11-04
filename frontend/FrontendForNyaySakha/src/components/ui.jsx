export function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint ? <small>{hint}</small> : null}
    </label>
  )
}

export function Banner({ kind = 'error', children }) {
  if (!children) return null
  return (
    <p className={`banner ${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      {children}
    </p>
  )
}

export function Outcome({ value }) {
  if (!value) return <span className="pill muted">Pending</span>
  const tone = value === 'Accepted' ? 'accepted' : 'rejected'
  return <span className={`pill ${tone}`}>{value}</span>
}
