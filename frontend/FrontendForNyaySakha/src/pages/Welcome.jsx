import { Link } from 'react-router-dom'
import { useAuth } from '../useAuth'

const features = [
  {
    title: 'Case summary',
    copy: 'Upload a judgment or brief and receive a short extractive summary of the facts and issues.',
  },
  {
    title: 'Similar precedents',
    copy: 'Compare the uploaded case with the stored library and see the five closest past decisions.',
  },
  {
    title: 'Outcome indication',
    copy: 'See whether a new case leans Accepted or Rejected, as a planning aid before the hearing.',
  },
]

export default function Welcome() {
  const { token } = useAuth()

  return (
    <div className="public">
      <header className="topbar">
        <Link to="/" className="mark">
          <span>NS</span>
          <strong>Nyaay Sakha</strong>
        </Link>
        <div className="top-actions">
          {token ? (
            <Link className="button" to="/analyze">Open workspace</Link>
          ) : (
            <>
              <Link className="text-link" to="/login">Sign in</Link>
              <Link className="button" to="/register">Create account</Link>
            </>
          )}
        </div>
      </header>

      <section className="hero">
        <p className="eyebrow">Legal companion</p>
        <h1>Read a case once. Keep the argument moving.</h1>
        <p className="lede">
          Nyaay Sakha condenses a case file, locates related precedents, and
          gives an early indication of how a similar matter was decided.
          Lawyers and judges remain the decision makers.
        </p>
        <div className="hero-actions">
          <Link className="button" to={token ? '/analyze' : '/register'}>
            {token ? 'Review a case' : 'Start with an account'}
          </Link>
          <Link className="button ghost" to="/login">Sign in</Link>
        </div>
      </section>

      <section className="feature-grid">
        {features.map((feature) => (
          <article key={feature.title} className="paper">
            <h2>{feature.title}</h2>
            <p>{feature.copy}</p>
          </article>
        ))}
      </section>
    </div>
  )
}
