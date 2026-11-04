import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api'
import { useAuth } from '../useAuth'
import { Banner, Outcome } from '../components/ui'
import { formatWhen } from '../format'

export default function LibraryCase() {
  const { caseId } = useParams()
  const navigate = useNavigate()
  const { request, userId } = useAuth()
  const [item, setItem] = useState(null)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  useEffect(() => {
    let active = true

    request(`/library/cases/${caseId}`)
      .then((data) => {
        if (active) setItem(data)
      })
      .catch((err) => {
        if (!active) return
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) return
        setError(err.message)
      })

    return () => {
      active = false
    }
  }, [caseId, request])

  async function remove() {
    if (!window.confirm('Remove this precedent from the library?')) return
    setPending(true)
    setError('')

    try {
      await request(`/library/cases/${caseId}`, { method: 'DELETE' })
      navigate('/library', { replace: true })
    } catch (err) {
      setError(err.message)
      setPending(false)
    }
  }

  return (
    <div className="page narrow">
      <Link className="back" to="/library">Back to precedents</Link>
      <Banner>{error}</Banner>
      {!item && !error ? <p className="quiet">Loading precedent…</p> : null}
      {item ? (
        <article className="paper stack">
          <p className="eyebrow">Precedent</p>
          <div className="title-row">
            <h1>{item.title}</h1>
            <Outcome value={item.outcome} />
          </div>
          <p className="meta">
            {[item.citation, item.court, item.decided_year, formatWhen(item.created_at)]
              .filter(Boolean)
              .join(' · ')}
          </p>
          <div className="judgment">{item.content}</div>
          {item.created_by === userId ? (
            <button
              type="button"
              className="text-button danger"
              onClick={remove}
              disabled={pending}
            >
              {pending ? 'Removing…' : 'Remove from library'}
            </button>
          ) : (
            <p className="quiet">Only the person who added this precedent can remove it.</p>
          )}
        </article>
      ) : null}
    </div>
  )
}
