import { useEffect, useState } from 'react'
import './App.css'

const TOKEN_KEY = 'nyaysakha_token'
const MAX_BYTES = 8 * 1024 * 1024

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || '')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [authError, setAuthError] = useState('')
  const [signingIn, setSigningIn] = useState(false)
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [uploads, setUploads] = useState([])

  useEffect(() => {
    if (!token) {
      return
    }

    let ignore = false

    loadUploads(token)
      .then((items) => {
        if (!ignore) {
          setUploads(items)
        }
      })
      .catch(() => {
        if (!ignore) {
          setUploads([])
        }
      })

    return () => {
      ignore = true
    }
  }, [token])

  async function signIn(event) {
    event.preventDefault()
    setSigningIn(true)
    setAuthError('')

    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await readJson(response)

      if (!response.ok) {
        throw new Error(messageFrom(data))
      }

      sessionStorage.setItem(TOKEN_KEY, data.token)
      setToken(data.token)
      setPassword('')
    } catch (err) {
      setAuthError(err.message || 'Sign in failed')
    } finally {
      setSigningIn(false)
    }
  }

  function signOut() {
    sessionStorage.removeItem(TOKEN_KEY)
    setToken('')
    setFile(null)
    setResult(null)
    setUploads([])
    setError('')
  }

  function chooseFile(selected) {
    setFile(selected)
    setError(selected ? validateFile(selected) : '')
    setResult(null)
  }

  async function submitUpload(event) {
    event.preventDefault()
    const problem = validateFile(file)

    if (problem) {
      setError(problem)
      return
    }

    setUploading(true)
    setError('')

    const body = new FormData()
    body.append('file', file)

    try {
      const response = await fetch('/analysis/analyze', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body,
      })
      const data = await readJson(response)

      if (!response.ok) {
        throw new Error(messageFrom(data))
      }

      setResult(data)
      setFile(null)
      setUploads(await loadUploads(token))
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function removeUpload(id) {
    const response = await fetch(`/uploads/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!response.ok) {
      const data = await readJson(response)
      setError(messageFrom(data))
      return
    }

    setUploads((current) => current.filter((item) => item.id !== id))

    if (result?.upload?.id === id) {
      setResult(null)
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <p className="mark">Nyaay Sakha</p>
          <h1>Upload a case file</h1>
        </div>
        {token ? (
          <button type="button" className="ghost" onClick={signOut}>
            Sign out
          </button>
        ) : null}
      </header>

      {token ? (
        <main className="layout">
          <section className="panel">
            <form onSubmit={submitUpload}>
              <label
                className={dragOver ? 'dropzone active' : 'dropzone'}
                onDragOver={(event) => {
                  event.preventDefault()
                  setDragOver(true)
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(event) => {
                  event.preventDefault()
                  setDragOver(false)
                  chooseFile(event.dataTransfer.files?.[0] || null)
                }}
              >
                <input
                  type="file"
                  accept=".pdf,.txt,.text,application/pdf,text/plain"
                  onChange={(event) => chooseFile(event.target.files?.[0] || null)}
                />
                <span className="drop-title">
                  {file ? file.name : 'Drop a PDF or text file here'}
                </span>
                <span className="drop-copy">
                  {file
                    ? formatBytes(file.size)
                    : 'or choose a file from your computer. Maximum size is 8 MB.'}
                </span>
              </label>

              {error ? <p className="error">{error}</p> : null}

              <button type="submit" className="primary" disabled={uploading}>
                {uploading ? 'Uploading…' : 'Upload case'}
              </button>
            </form>

            {result ? <AnalysisResult result={result} /> : null}
          </section>

          <aside className="panel">
            <h2>Your uploads</h2>
            {uploads.length === 0 ? (
              <p className="muted">Uploaded case files will appear here.</p>
            ) : (
              <ul className="uploads">
                {uploads.map((item) => (
                  <li key={item.id}>
                    <div>
                      <strong>{item.filename}</strong>
                      <span>
                        {formatBytes(item.size_bytes)} · {formatWhen(item.created_at)}
                      </span>
                    </div>
                    <button type="button" onClick={() => removeUpload(item.id)}>
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </aside>
        </main>
      ) : (
        <main className="layout single">
          <section className="panel">
            <h2>Sign in to upload</h2>
            <p className="muted">
              Case files are stored with your account. Sign in with the email and
              password you registered.
            </p>
            <form className="signin" onSubmit={signIn}>
              <label>
                Email
                <input
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </label>
              {authError ? <p className="error">{authError}</p> : null}
              <button type="submit" className="primary" disabled={signingIn}>
                {signingIn ? 'Signing in…' : 'Sign in'}
              </button>
            </form>
          </section>
        </main>
      )}
    </div>
  )
}

function AnalysisResult({ result }) {
  return (
    <div className="results">
      <h2>Document received</h2>
      <p className="excerpt">{result.excerpt}</p>
      <p className="muted">{result.characters.toLocaleString()} characters read.</p>
      <div className="cards">
        <article>
          <h3>Summary</h3>
          <p>{result.summary.summary || 'LexRank summary is not connected yet.'}</p>
        </article>
        <article>
          <h3>Similar cases</h3>
          {result.similar_cases.cases.length === 0 ? (
            <p>Precedent matching is not connected yet.</p>
          ) : (
            <ol>
              {result.similar_cases.cases.map((item) => (
                <li key={`${item.rank}-${item.case_id}`}>{item.title}</li>
              ))}
            </ol>
          )}
        </article>
        <article>
          <h3>Predicted outcome</h3>
          <p>{result.prediction.outcome || 'Outcome prediction is not connected yet.'}</p>
        </article>
      </div>
      <p className="disclaimer">{result.disclaimer}</p>
    </div>
  )
}

function validateFile(selected) {
  if (!selected) {
    return 'Choose a PDF or text file'
  }

  if (!/\.(pdf|txt|text)$/i.test(selected.name)) {
    return 'Upload a PDF or text file'
  }

  if (selected.size === 0) {
    return 'The uploaded file is empty'
  }

  if (selected.size > MAX_BYTES) {
    return 'File is larger than 8 MB'
  }

  return ''
}

async function loadUploads(token) {
  const response = await fetch('/uploads', {
    headers: { Authorization: `Bearer ${token}` },
  })
  const data = await readJson(response)

  if (!response.ok) {
    throw new Error(messageFrom(data))
  }

  return data
}

async function readJson(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

function messageFrom(data) {
  if (!data) {
    return 'Something went wrong'
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg || String(item)).join(' ')
  }

  return data.message || 'Something went wrong'
}

function formatBytes(size) {
  if (size < 1024) {
    return `${size} B`
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }

  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function formatWhen(value) {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return date.toLocaleString()
}

export default App
