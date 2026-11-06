export function Banner({ tone = 'info', children }) {
  if (!children) return null
  return <div className={`banner ${tone}`}>{children}</div>
}

export function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint ? <small>{hint}</small> : null}
    </label>
  )
}

export function MetaList({ items = [] }) {
  return (
    <p className="meta inline-list">
      {items.map((item, index) => (
        <span key={index}>{item}</span>
      ))}
    </p>
  )
}

export function Outcome({ value }) {
  if (!value) return <span className="pill muted">Pending</span>
  const tone =
    value === 'Accepted'
      ? 'accepted'
      : value === 'Rejected'
      ? 'rejected'
      : value === 'Disposed'
      ? 'disposed'
      : 'muted'
  return <span className={`pill ${tone}`}>{value}</span>
}
