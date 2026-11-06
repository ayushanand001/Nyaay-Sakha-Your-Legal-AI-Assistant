import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../useAuth'
import { Banner, Outcome } from '../components/ui'
import { formatBytes } from '../format'

const modes = [
  { id: 'analyze', label: 'Full review', path: '/analysis/analyze' },
  { id: 'summarize', label: 'Summary', path: '/analysis/summarize' },
  { id: 'similar', label: 'Precedents', path: '/analysis/similar-cases' },
  { id: 'predict', label: 'Outcome', path: '/analysis/predict' },
]

export default function Analyze() {
  const { request } = useAuth()
  const [mode, setMode] = useState('analyze')
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const [result, setResult] = useState(null)
  const [dragging, setDragging] = useState(false)

  function chooseFile(next) {
    setResult(null)
    if (!next) {
      setFile(null)
      return
    }

    const extension = next.name.includes('.')
      ? next.name.slice(next.name.lastIndexOf('.')).toLowerCase()
      : ''

    if (!['.pdf', '.txt', '.text'].includes(extension)) {
      setFile(null)
      setError('Upload a PDF or text file.')
      return
    }

    if (next.size === 0) {
      setFile(null)
      setError('The uploaded file is empty.')
      return
    }

    if (next.size > 8 * 1024 * 1024) {
      setFile(null)
      setError('File is larger than 8 MB.')
      return
    }

    setError('')
    setFile(next)
  }

  async function onSubmit(event) {
    event.preventDefault()
    if (!file) {
      setError('Choose a case document first.')
      return
    }

    const selected = modes.find((item) => item.id === mode)
    const formData = new FormData()
    formData.append('file', file)
    setPending(true)
    setError('')

    try {
      const data = await request(selected.path, { method: 'POST', formData })
      setResult({ mode, data })
    } catch (err) {
      setResult(null)
      setError(err.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <p className="eyebrow">Case review</p>
        <h1>Upload a case document</h1>
        <p className="lede">
          PDF and text files up to 8 MB. One upload is stored with your documents
          and returned with the review you select.
        </p>
      </header>

      <div className="split">
        <form className="paper stack" onSubmit={onSubmit}>
          <fieldset className="mode-set">
            <legend>What should come back</legend>
            {modes.map((item) => (
              <label key={item.id} className={mode === item.id ? 'mode on' : 'mode'}>
                <input
                  type="radio"
                  name="mode"
                  value={item.id}
                  checked={mode === item.id}
                  onChange={() => setMode(item.id)}
                />
                {item.label}
              </label>
            ))}
          </fieldset>

          <label
            className={dragging ? 'drop dragging' : 'drop'}
            onDragOver={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault()
              setDragging(false)
              chooseFile(event.dataTransfer.files?.[0])
            }}
          >
            <input
              type="file"
              accept=".pdf,.txt,.text,application/pdf,text/plain"
              onChange={(event) => chooseFile(event.target.files?.[0])}
            />
            <strong>{file ? file.name : 'Drop a case file here'}</strong>
            <span>
              {file
                ? formatBytes(file.size)
                : 'or choose a PDF, .txt, or .text file'}
            </span>
          </label>

          <Banner>{error}</Banner>
          <button className="button" type="submit" disabled={pending || !file}>
            {pending ? 'Reading the file…' : 'Run review'}
          </button>
        </form>

        <section className="results">
          {result ? <Review result={result} /> : (
            <div className="paper empty">
              <h2>The review appears here</h2>
              <p>
                A full review returns the summary, five similar precedents, and
                an Accepted or Rejected indication together.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function Review({ result }) {
  const { mode, data } = result
  const showSummary = mode === 'analyze' || mode === 'summarize'
  const showSimilar = mode === 'analyze' || mode === 'similar'
  const showPrediction = mode === 'analyze' || mode === 'predict'

  return (
    <div className="stack">
      <article className="paper">
        <p className="eyebrow">Document</p>
        <h2>{data.filename}</h2>
        <p className="meta">
          {data.characters.toLocaleString()} characters
          {data.upload ? ` · saved as ${data.upload.id.slice(0, 8)}` : ''}
        </p>
        <blockquote>{data.excerpt}</blockquote>
        {data.upload ? <Link to="/uploads">Open documents</Link> : null}
      </article>

      {showSummary ? <SummaryBlock summary={data.summary} /> : null}
      {showSimilar ? <SimilarBlock similar={data.similar_cases} /> : null}
      {showPrediction ? <PredictionBlock prediction={data.prediction} /> : null}

      <p className="disclaimer">{data.disclaimer}</p>
    </div>
  )
}

function SummaryBlock({ summary }) {
  return (
    <article className="paper">
      <p className="eyebrow">LexRank summary</p>
      <h2>Summary</h2>
      {summary?.summary ? <p>{summary.summary}</p> : (
        <p className="quiet">The summary will appear here once the model is connected.</p>
      )}
      {summary?.sentences?.length ? (
        <ul className="sentence-list">
          {summary.sentences.map((sentence) => (
            <li key={sentence}>{sentence}</li>
          ))}
        </ul>
      ) : null}
    </article>
  )
}

function SimilarBlock({ similar }) {
  const cases = similar?.cases || []

  return (
    <article className="paper">
      <p className="eyebrow">TF-IDF cosine similarity</p>
      <h2>Five closest precedents</h2>
      {cases.length ? (
        <ol className="case-list">
          {cases.map((item) => (
            <li key={`${item.rank}-${item.case_id || item.title}`}>
              <div>
                <strong>{item.title || 'Untitled precedent'}</strong>
                <p className="meta">
                  {[item.citation, item.court, item.decided_year].filter(Boolean).join(' · ')}
                  {typeof item.similarity === 'number'
                    ? ` · ${(item.similarity * 100).toFixed(1)}% similar`
                    : ''}
                </p>
              </div>
              <Outcome value={item.outcome} />
            </li>
          ))}
        </ol>
      ) : (
        <p className="quiet">
          {similar?.implemented
            ? 'No precedents on this account match this document yet. Add decided cases under Precedents.'
            : 'Similar precedents will appear here once the model is connected. Add decided cases under Precedents so the library has something to search.'}
        </p>
      )}
    </article>
  )
}

function PredictionBlock({ prediction }) {
  return (
    <article className="paper">
      <p className="eyebrow">Support vector machine</p>
      <h2>Likely outcome</h2>
      <Outcome value={prediction?.outcome} />
      {typeof prediction?.confidence === 'number' ? (
        <p className="meta">Confidence {(prediction.confidence * 100).toFixed(1)}%</p>
      ) : null}
      {prediction?.detail ? <p className="quiet">{prediction.detail}</p> : null}
      {!prediction?.implemented && !prediction?.detail ? (
        <p className="quiet">The outcome indication will appear here once the model is connected.</p>
      ) : null}
    </article>
  )
}
