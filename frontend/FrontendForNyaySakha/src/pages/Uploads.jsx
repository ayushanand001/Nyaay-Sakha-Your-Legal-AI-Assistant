import { useEffect, useState } from 'react'
import { ApiError, downloadFile } from '../api'
import { useAuth } from '../useAuth'
import { Banner } from '../components/ui'
import { formatBytes, formatWhen } from '../format'

export default function Uploads() {
  const { token, request } = useAuth()
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    request('/uploads')
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

  async function download(row) {
    setError('')
    setNotice('')
    try {
      await downloadFile(`/uploads/${row.id}/file`, token, row.filename)
    } catch (err) {
      setError(err.message)
    }
  }

  async function remove(row) {
    if (!window.confirm(`Remove ${row.filename}?`)) return
    setError('')
    setNotice('')
    try {
      await request(`/uploads/${row.id}`, { method: 'DELETE' })
      setRows((current) => current.filter((item) => item.id !== row.id))
      setNotice('Document removed.')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <p className="eyebrow">Your files</p>
        <h1>Uploaded documents</h1>
        <p className="lede">
          Every review stores the original PDF or text file with the account that uploaded it.
        </p>
      </header>
      <Banner>{error}</Banner>
      <Banner kind="ok">{notice}</Banner>
      {loading ? <p className="quiet">Loading documents…</p> : null}
      {!loading && rows.length === 0 ? (
        <div className="paper empty">
          <h2>No documents yet</h2>
          <p>Run a review and the uploaded case file will be listed here.</p>
        </div>
      ) : null}
      <div className="card-list">
        {rows.map((row) => (
          <article key={row.id} className="paper record">
            <div>
              <h2>{row.filename}</h2>
              <p className="meta">
                {formatBytes(row.size_bytes)} · {row.characters.toLocaleString()} characters · {formatWhen(row.created_at)}
              </p>
              <p>{row.excerpt}</p>
            </div>
            <div className="row-actions">
              <button type="button" className="button ghost" onClick={() => download(row)}>
                Download
              </button>
              <button type="button" className="text-button danger" onClick={() => remove(row)}>
                Remove
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
