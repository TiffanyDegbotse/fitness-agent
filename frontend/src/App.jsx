import { useState } from 'react'
import Dashboard from './pages/Dashboard.jsx'
import Chat from './pages/Chat.jsx'
import Setup from './pages/Setup.jsx'

export default function App() {
  const [page, setPage] = useState('setup')          // setup | dashboard | chat
  const [stepData, setStepData] = useState([])
  const [userProfile, setUserProfile] = useState(null)
  const [goal, setGoal] = useState(null)

  const sharedProps = { stepData, setStepData, userProfile, setUserProfile, goal, setGoal }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface)' }}>
      {/* Top Nav */}
      <nav style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 28px', height: 60,
        borderBottom: '1px solid var(--border)',
        background: 'rgba(15,17,23,0.95)',
        position: 'sticky', top: 0, zIndex: 50,
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 22 }}>🏃</span>
          <span style={{ fontFamily: 'Syne', fontWeight: 800, fontSize: 18, letterSpacing: '-0.02em' }}>
            FitAgent
          </span>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          {['setup', 'dashboard', 'chat'].map(p => (
            <button
              key={p}
              onClick={() => setPage(p)}
              style={{
                padding: '6px 16px',
                borderRadius: 7,
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'Syne',
                fontWeight: 600,
                fontSize: 13,
                transition: 'all 0.15s',
                background: page === p ? 'var(--brand)' : 'transparent',
                color: page === p ? '#000' : 'var(--text-soft)',
              }}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="pulse-dot" />
          <span style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>
            {stepData.length > 0 ? `${stepData.length} days loaded` : 'no data'}
          </span>
        </div>
      </nav>

      {/* Pages */}
      {page === 'setup'     && <Setup     {...sharedProps} onDone={() => setPage('dashboard')} />}
      {page === 'dashboard' && <Dashboard {...sharedProps} onChat={() => setPage('chat')} />}
      {page === 'chat'      && <Chat      {...sharedProps} />}
    </div>
  )
}
