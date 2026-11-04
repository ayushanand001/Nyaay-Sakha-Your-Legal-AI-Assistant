import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api'
import { useAuth } from '../useAuth'
import { Banner, Field, Outcome } from '../components/ui'
import { formatWhen } from '../format'

const emptyForm = {
  title: '',
  citation: '',
  court: '',
  decided_year: '',
  outcome: 'Accepted',
  content: '',
}

export default function Library() {
  const { request } = useAuth()
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    let active = true

    request('/library/cases')
      .then((data) => {
        if (active) setRows(data)
      })
      .catch((err) => {
        if (!active) return
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) return
        setError(err.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [request])

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function onSubmit(event) {
    event.preventDefault()
    setError('')
    setNotice('')
    setPending(true)

    const year = form.decided_year.trim()

    try {
      const created = await request('/library/cases', {
        method: 'POST',
        json: {
          title: form.title.trim(),
          content: form.content.trim(),
          outcome: form.outcome,
          citation: form.citation.trim() || null,
          court: form.court.trim() || null,
          decided_year: year ? Number(year) : null,
        },
      })
      setRows((current) => [{ ...created, content: null }, ...current])
      setForm(emptyForm)
      setNotice('Precedent saved to the library.')
    } catch (err) {
      setError(err.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <p className="eyebrow">Stored judgments</p>
        <h1>Precedent library</h1>
        <p className="lede">
          Past cases kept for similarity search. Each entry needs the judgment
          text and a decided outcome of Accepted or Rejected.
        </p>
      </header>

      <div className="split">
        <form className="paper stack" onSubmit={onSubmit}>
          <h2>Add a precedent</h2>
          <Banner>{error}</Banner>
          <Banner kind="ok">{notice}</Banner>
          <Field label="Title">
            <input
              value={form.title}
              onChange={(event) => update('title', event.target.value)}
              maxLength={300}
              required
            />
          </Field>
          <Field label="Citation">
            <input
              value={form.citation}
              onChange={(event) => update('citation', event.target.value)}
              maxLength={300}
            />
          </Field>
          <div className="pair">
            <Field label="Court">
              <input
                value={form.court}
                onChange={(event) => update('court', event.target.value)}
                maxLength={200}
              />
            </Field>
            <Field label="Year">
              <input
                type="number"
                min="1800"
                max="2100"
                value={form.decided_year}
                onChange={(event) => update('decided_year', event.target.value)}
              />
            </Field>
          </div>
          <Field label="Outcome">
            <select
              value={form.outcome}
              onChange={(event) => update('outcome', event.target.value)}
            >
              <option value="Accepted">Accepted</option>
              <option value="Rejected">Rejected</option>
            </select>
          </Field>
          <Field label="Judgment text">
            <textarea
              value={form.content}
              onChange={(event) => update('content', event.target.value)}
              rows={8}
              required
            />
          </Field>
          <button className="button" type="submit" disabled={pending}>
            {pending ? 'Saving…' : 'Save precedent'}
          </button>
        </form>

        <section className="stack">
          {loading ? <p className="quiet">Loading precedents…</p> : null}
          {!loading && rows.length === 0 ? (
            <div className="paper empty">
              <h2>The library is empty</h2>
              <p>Add a decided case to give later reviews something to compare against.</p>
            </div>
          ) : null}
          {rows.map((row) => (
            <article key={row.id} className="paper record">
              <div>
                <h2>
                  <Link to={`/library/${row.id}`}>{row.title}</Link>
                </h2>
                <p className="meta">
                  {[row.citation, row.court, row.decided_year, formatWhen(row.created_at)]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </div>
              <Outcome value={row.outcome} />
            </article>
          ))}
        </section>
      </div>
    </div>
  )
}
