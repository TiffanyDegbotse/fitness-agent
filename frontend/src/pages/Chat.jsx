import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

const SUGGESTED = [
  'How am I doing this week?',
  'How many calories did I burn today?',
  "What's my current streak?",
  'Give me tips to hit my goal',
  'Analyze my trends',
  'Set a goal of 12,000 steps',
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className="fade-in" style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16,
    }}>
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: 'var(--brand)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', marginRight: 10, flexShrink: 0,
          fontSize: 15, alignSelf: 'flex-end',
        }}>🏃</div>
      )}
      <div style={{
        maxWidth: '72%',
        padding: '12px 16px',
        borderRadius: isUser ? '16px 16px 4px 16px' : '4px 16px 16px 16px',
        background: isUser ? 'var(--brand)' : 'var(--card)',
        border: isUser ? 'none' : '1px solid var(--border)',
        color: isUser ? '#000' : 'var(--text-primary)',
        fontSize: 14, lineHeight: 1.6,
      }}>
        {isUser
          ? <span style={{ fontFamily: 'DM Sans' }}>{msg.content}</span>
          : <ReactMarkdown
              components={{
                p: ({ children }) => <p style={{ margin: '0 0 8px' }}>{children}</p>,
                ul: ({ children }) => <ul style={{ margin: '4px 0', paddingLeft: 18 }}>{children}</ul>,
                li: ({ children }) => <li style={{ marginBottom: 3 }}>{children}</li>,
                strong: ({ children }) => <strong style={{ color: 'var(--brand)' }}>{children}</strong>,
              }}
            >{msg.content}</ReactMarkdown>
        }
      </div>
    </div>
  )
}

export default function Chat({ stepData, userProfile, goal }) {
  const [messages, setMessages] = useState([])     // display messages
  const [apiMessages, setApiMessages] = useState([]) // full API message history
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Greeting on first load
  useEffect(() => {
    const name = userProfile?.name ? `, ${userProfile.name}` : ''
    const dataNote = stepData.length > 0
      ? `I can see ${stepData.length} days of your step data. `
      : 'I don\'t have your step data yet — you can upload it in Setup. '
    setMessages([{
      role: 'assistant',
      content: `Hey${name}! 👋 I'm FitAgent, your AI fitness coach. ${dataNote}What would you like to know about your fitness?`,
    }])
  }, [])

  const send = async (text) => {
    const userText = text || input.trim()
    if (!userText || loading) return
    setInput('')

    const newDisplay = [...messages, { role: 'user', content: userText }]
    setMessages(newDisplay)
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          messages: apiMessages,
          user_profile: userProfile,
          step_data: stepData.length > 0 ? stepData : null,
          goal,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Request failed')

      setMessages([...newDisplay, { role: 'assistant', content: data.response }])
      setApiMessages(data.messages)
    } catch (e) {
      setMessages([...newDisplay, { role: 'assistant', content: `❌ Error: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div style={{
      maxWidth: 760, margin: '0 auto',
      display: 'flex', flexDirection: 'column',
      height: 'calc(100vh - 60px)',
      padding: '0 24px',
    }}>
      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '28px 0 16px' }}>
        {messages.map((m, i) => <Message key={i} msg={m} />)}
        {loading && (
          <div className="fade-in" style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%', background: 'var(--brand)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15,
            }}>🏃</div>
            <div className="card" style={{ padding: '12px 16px', display: 'flex', gap: 6, alignItems: 'center' }}>
              {[0, 0.2, 0.4].map(d => (
                <div key={d} style={{
                  width: 7, height: 7, borderRadius: '50%', background: 'var(--brand)',
                  animation: 'pulse 1.2s ease-in-out infinite',
                  animationDelay: `${d}s`,
                }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          {SUGGESTED.map(s => (
            <button
              key={s}
              onClick={() => send(s)}
              style={{
                padding: '6px 14px', borderRadius: 20,
                border: '1px solid var(--border)',
                background: 'var(--card)', color: 'var(--text-soft)',
                fontSize: 12, cursor: 'pointer', fontFamily: 'DM Sans',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { e.target.style.borderColor = 'var(--brand)'; e.target.style.color = 'var(--brand)' }}
              onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--text-soft)' }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="card" style={{
        display: 'flex', alignItems: 'flex-end', gap: 10,
        padding: '12px 14px', marginBottom: 20,
      }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask me anything about your fitness…"
          rows={1}
          style={{
            flex: 1, background: 'none', border: 'none', outline: 'none',
            color: 'var(--text-primary)', fontFamily: 'DM Sans', fontSize: 14,
            resize: 'none', lineHeight: 1.5, maxHeight: 120, overflowY: 'auto',
          }}
        />
        <button
          className="btn-primary"
          onClick={() => send()}
          disabled={loading || !input.trim()}
          style={{ padding: '8px 18px', flexShrink: 0 }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
