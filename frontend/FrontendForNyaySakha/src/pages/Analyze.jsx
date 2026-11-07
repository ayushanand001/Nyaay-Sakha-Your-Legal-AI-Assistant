import { useEffect, useState } from 'react'
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

const resultTabs = [
  { id: 'summary', label: 'Summary' },
  { id: 'precedents', label: 'Precedents' },
  { id: 'outcome', label: 'Outcome' },
]

const loadingStages = [
  'Reading the case file',
  'Writing the summary',
  'Matching precedents',
  'Estimating the outcome',
]

const tabForMode = {
  analyze: 'summary',
  summarize: 'summary',
  similar: 'precedents',
  predict: 'outcome',
}

export default function Analyze() {
  const { request } = useAuth()
  const [mode, setMode] = useState('analyze')
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const [result, setResult] = useState(null)
  const [panel, setPanel] = useState('summary')
  const [stage, setStage] = useState(0)
  const [dragging, setDragging] = useState(false)
  const [selectedPrecedent, setSelectedPrecedent] = useState(null)

  useEffect(() => {
    if (!pending) return undefined
    const timer = setInterval(() => {
      setStage((current) => Math.min(current + 1, loadingStages.length - 1))
    }, 1100)
    return () => clearInterval(timer)
  }, [pending])

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
    setStage(0)
    setPending(true)
    setError('')

    try {
      const data = await request(selected.path, { method: 'POST', formData })
      setPanel(tabForMode[mode])
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
                  onChange={(event) => setMode(event.target.value)}
                />
                <span>{item.label}</span>
              </label>
            ))}
          </fieldset>

          <label
            className={dragging ? 'drop-target active' : 'drop-target'}
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
              accept=".pdf,.txt,.text"
              onChange={(event) => chooseFile(event.target.files?.[0])}
            />
            {file ? (
              <span className="file-chip">
                <strong>{file.name}</strong>
                <small>{formatBytes(file.size)}</small>
              </span>
            ) : (
              <span>
                <strong>Drop a PDF or text file here</strong>, or browse your machine.
              </span>
            )}
          </label>

          <Banner tone="error">{error}</Banner>

          <button type="submit" disabled={pending || !file}>
            {pending ? 'Review in progress' : 'Run review'}
          </button>
        </form>

        <section className="review-stage">
          {pending ? <ReviewLoading stage={stage} filename={file?.name} /> : null}
          {!pending && result ? (
            <ResultView
              mode={result.mode}
              panel={panel}
              onPanel={setPanel}
              data={result.data}
              onOpenJudgment={setSelectedPrecedent}
            />
          ) : null}
          {!pending && !result ? (
            <div className="paper quiet">
              <p className="eyebrow">Awaiting document</p>
              <h2>Select an option and upload</h2>
              <p>
                A full review opens three tabs: the summary, the closest precedents,
                and the likely outcome.
              </p>
            </div>
          ) : null}
        </section>
      </div>

      {selectedPrecedent ? (
        <JudgmentModal
          precedent={selectedPrecedent}
          onClose={() => setSelectedPrecedent(null)}
        />
      ) : null}
    </div>
  )
}

function ReviewLoading({ stage, filename }) {
  const progress = ((stage + 1) / loadingStages.length) * 100

  return (
    <div className="paper loading-card" role="status" aria-live="polite">
      <p className="eyebrow">Review in progress</p>
      <h2>{filename || 'Reading the document'}</h2>
      <div className="loading-track" aria-hidden="true">
        <span style={{ width: `${progress}%` }} />
      </div>
      <ol className="loading-steps">
        {loadingStages.map((label, index) => {
          const state = index < stage ? 'done' : index === stage ? 'active' : 'wait'
          return (
            <li key={label} className={`loading-step ${state}`}>
              <span />
              {label}
            </li>
          )
        })}
      </ol>
    </div>
  )
}

function ResultView({ mode, panel, onPanel, data, onOpenJudgment }) {
  const available = {
    summary: mode === 'analyze' || mode === 'summarize',
    precedents: mode === 'analyze' || mode === 'similar',
    outcome: mode === 'analyze' || mode === 'predict',
  }

  return (
    <div className="stack result-reveal">
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

      <div className="result-tabs" role="tablist">
        {resultTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={panel === tab.id}
            className={panel === tab.id ? 'result-tab active' : 'result-tab'}
            onClick={() => onPanel(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div key={panel} className="panel-enter">
        {panel === 'summary' ? (
          available.summary
            ? <SummaryBlock summary={data.summary} />
            : <MissingPanel label="summary" />
        ) : null}
        {panel === 'precedents' ? (
          available.precedents
            ? <SimilarBlock similar={data.similar_cases} onOpenJudgment={onOpenJudgment} />
            : <MissingPanel label="precedents" />
        ) : null}
        {panel === 'outcome' ? (
          available.outcome
            ? <PredictionBlock prediction={data.prediction} />
            : <MissingPanel label="the outcome" />
        ) : null}
      </div>

      <p className="disclaimer">{data.disclaimer}</p>
    </div>
  )
}

function MissingPanel({ label }) {
  return (
    <article className="paper quiet">
      <h2>This review did not include {label}</h2>
      <p>Run a full review to fill the summary, precedents, and outcome tabs from one upload.</p>
    </article>
  )
}

function SummaryBlock({ summary }) {
  const [tab, setTab] = useState('narrative')

  const reductionTag =
    typeof summary?.reduction_pct === 'number' && summary.reduction_pct > 0
      ? ` · ${summary.reduction_pct}% condensed (${summary.word_count || 0} words)`
      : ''

  return (
    <article className="paper">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginBottom: '0.35rem',
        }}
      >
        <p className="eyebrow" style={{ margin: 0 }}>
          Legal Domain LexRank{reductionTag}
        </p>
        {summary?.key_points?.length ? (
          <div style={{ display: 'flex', gap: '0.35rem' }}>
            <button
              type="button"
              className="btn-secondary btn-sm"
              style={{
                fontWeight: tab === 'narrative' ? 600 : 400,
                background: tab === 'narrative' ? '#dfd6c8' : '#eee7dc',
                borderColor: tab === 'narrative' ? '#b5a995' : 'transparent',
              }}
              onClick={() => setTab('narrative')}
            >
              Narrative Summary
            </button>
            <button
              type="button"
              className="btn-secondary btn-sm"
              style={{
                fontWeight: tab === 'takeaways' ? 600 : 400,
                background: tab === 'takeaways' ? '#dfd6c8' : '#eee7dc',
                borderColor: tab === 'takeaways' ? '#b5a995' : 'transparent',
              }}
              onClick={() => setTab('takeaways')}
            >
              Structured Highlights
            </button>
          </div>
        ) : null}
      </div>

      <h2>Executive Case Summary</h2>

      {tab === 'narrative' ? (
        summary?.summary ? (
          <p style={{ lineHeight: 1.7, fontSize: '0.98rem' }}>{summary.summary}</p>
        ) : (
          <p className="quiet">The summary will appear here once the document is analyzed.</p>
        )
      ) : (
        <ul className="sentence-list" style={{ marginTop: '0.5rem' }}>
          {(summary?.key_points || []).map((point, idx) => (
            <li key={idx} style={{ padding: '0.35rem 0', lineHeight: 1.5 }}>
              {point}
            </li>
          ))}
        </ul>
      )}

      {tab === 'narrative' && summary?.sentences?.length ? (
        <details style={{ marginTop: '0.8rem', fontSize: '0.85rem' }}>
          <summary style={{ cursor: 'pointer', color: 'var(--muted, #666)' }}>
            View individual sentences ({summary.sentences.length})
          </summary>
          <ul className="sentence-list" style={{ marginTop: '0.4rem' }}>
            {summary.sentences.map((sentence) => (
              <li key={sentence}>{sentence}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </article>
  )
}

function SimilarBlock({ similar, onOpenJudgment }) {
  const cases = similar?.cases || []
  const eyebrowText = similar?.total_corpus_cases
    ? `Precedent Recommender · ${similar.total_corpus_cases.toLocaleString()} cases indexed`
    : 'TF-IDF Cosine Similarity'

  return (
    <article className="paper">
      <p className="eyebrow">{eyebrowText}</p>
      <h2>Five closest precedents</h2>
      {cases.length ? (
        <ol className="case-list">
          {cases.map((item) => (
            <li
              key={`${item.rank}-${item.case_id || item.title}`}
              style={{ alignItems: 'flex-start' }}
            >
              <div style={{ flex: 1, minWidth: 0, paddingRight: '0.75rem' }}>
                <strong>{item.title || 'Untitled precedent'}</strong>
                <p className="meta" style={{ margin: '0.2rem 0' }}>
                  {[item.court, item.citation, item.decided_year, item.judge]
                    .filter(Boolean)
                    .join(' · ')}
                  {typeof item.similarity === 'number'
                    ? ` · ${(item.similarity * 100).toFixed(1)}% match`
                    : ''}
                </p>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginTop: '0.4rem',
                    flexWrap: 'wrap',
                  }}
                >
                  <button
                    type="button"
                    className="btn-secondary btn-sm"
                    style={{
                      cursor: 'pointer',
                      fontWeight: 600,
                      color: 'var(--primary, #0056b3)',
                    }}
                    onClick={() => onOpenJudgment(item)}
                  >
                    📖 View Full Judgment
                  </button>

                  {item.snippet ? (
                    <details style={{ fontSize: '0.84rem', color: '#555', display: 'inline' }}>
                      <summary
                        style={{
                          cursor: 'pointer',
                          color: 'var(--muted, #666)',
                          fontWeight: 500,
                        }}
                      >
                        Factual snippet
                      </summary>
                      <p
                        style={{
                          margin: '0.3rem 0 0',
                          padding: '0.45rem 0.65rem',
                          background: '#f5f2eb',
                          borderRadius: '4px',
                          fontStyle: 'italic',
                          lineHeight: 1.45,
                        }}
                      >
                        {item.snippet}
                      </p>
                    </details>
                  ) : null}
                </div>
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-end',
                  gap: '0.3rem',
                  flexShrink: 0,
                }}
              >
                <Outcome value={item.outcome} />
                {item.detailed_label && item.detailed_label !== item.outcome ? (
                  <span className="pill muted" style={{ fontSize: '0.75rem' }}>
                    {item.detailed_label}
                  </span>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="quiet">
          {similar?.implemented
            ? 'No precedents match this document yet.'
            : 'Similar precedents will appear here once the model is connected.'}
        </p>
      )}
    </article>
  )
}

function PredictionBlock({ prediction }) {
  const methodLabel =
    prediction?.method === 'lightgbm'
      ? 'LightGBM Classifier'
      : prediction?.method === 'svm'
      ? 'Support Vector Machine'
      : prediction?.method
      ? `${prediction.method} Model`
      : 'Outcome Model'

  return (
    <article className="paper">
      <p className="eyebrow">{methodLabel}</p>
      <h2>Likely outcome</h2>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          flexWrap: 'wrap',
          marginBottom: '0.6rem',
        }}
      >
        <Outcome value={prediction?.outcome} />
        {prediction?.detailed_label ? (
          <span className="pill muted" title="Fine-grained legal prediction">
            {prediction.detailed_label}
          </span>
        ) : null}
      </div>
      {typeof prediction?.confidence === 'number' ? (
        <p className="meta">Confidence {(prediction.confidence * 100).toFixed(1)}%</p>
      ) : null}
      {prediction?.probabilities && Object.keys(prediction.probabilities).length > 0 ? (
        <div
          style={{
            marginTop: '0.85rem',
            paddingTop: '0.75rem',
            borderTop: '1px solid #e8e2d8',
          }}
        >
          <p
            style={{
              margin: '0 0 0.4rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              color: 'var(--muted, #666)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            Class Probabilities
          </p>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '0.4rem',
            }}
          >
            {Object.entries(prediction.probabilities).map(([cls, prob]) => {
              const isSelected =
                cls.toLowerCase() === (prediction?.detailed_label || '').toLowerCase()
              return (
                <div
                  key={cls}
                  style={{
                    background: isSelected ? '#e5f0e8' : '#f5f2eb',
                    border: isSelected ? '1px solid #b2d8bc' : '1px solid transparent',
                    padding: '0.35rem 0.55rem',
                    borderRadius: '6px',
                    fontSize: '0.82rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span style={{ fontWeight: isSelected ? 600 : 400 }}>{cls}</span>
                  <strong>{(prob * 100).toFixed(1)}%</strong>
                </div>
              )
            })}
          </div>
        </div>
      ) : null}
      {prediction?.detail ? <p className="quiet">{prediction.detail}</p> : null}
      {!prediction?.implemented && !prediction?.detail ? (
        <p className="quiet">
          The outcome indication will appear here once the model is connected.
        </p>
      ) : null}
    </article>
  )
}

function JudgmentModal({ precedent, onClose }) {
  const [copied, setCopied] = useState(false)

  if (!precedent) return null

  function handleCopy() {
    const textToCopy = precedent.full_text || precedent.snippet || ''
    navigator.clipboard.writeText(textToCopy).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    })
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="eyebrow" style={{ color: 'var(--primary, #0056b3)' }}>
              Full Judgment Reader · High Court Precedent
            </span>
            <h2>{precedent.title}</h2>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                flexWrap: 'wrap',
                marginTop: '0.4rem',
              }}
            >
              <Outcome value={precedent.outcome} />
              {precedent.detailed_label ? (
                <span className="pill muted">{precedent.detailed_label}</span>
              ) : null}
              {precedent.court ? (
                <span className="pill muted">{precedent.court}</span>
              ) : null}
              {precedent.decided_year ? (
                <span className="pill muted">Decided: {precedent.decided_year}</span>
              ) : null}
            </div>
            {precedent.judge ? (
              <p className="meta" style={{ marginTop: '0.35rem', marginBottom: 0 }}>
                Coram: <strong>{precedent.judge}</strong>
                {precedent.case_id ? ` · Record: ${precedent.case_id}` : ''}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close judgment reader"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="judgment-viewer">
            {precedent.full_text || precedent.snippet || 'The full text of this judgment is not available.'}
          </div>
        </div>

        <div className="modal-footer">
          <p className="meta" style={{ margin: 0 }}>
            {precedent.full_text ? `${precedent.full_text.length.toLocaleString()} characters` : ''}
          </p>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="button" className="btn-secondary" onClick={handleCopy}>
              {copied ? '✓ Copied to Clipboard!' : '📋 Copy Judgment Text'}
            </button>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
