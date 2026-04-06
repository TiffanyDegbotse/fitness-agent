import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

export default function Setup({ userProfile, setUserProfile, setStepData, goal, setGoal, onDone }) {
  const [form, setForm] = useState({
    name: userProfile?.name || '',
    age: userProfile?.age || '',
    weight_kg: userProfile?.weight_kg || '',
    height_cm: userProfile?.height_cm || '',
  })
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [goalForm, setGoalForm] = useState({ type: 'steps', target: 10000 })
  const [error, setError] = useState('')

  const onDrop = useCallback(async (files) => {
    const file = files[0]
    if (!file) return
    setUploading(true)
    setError('')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await fetch('https://fitness-agent-backend-org7.onrender.com/api/upload/apple-health', { method: 'POST', body: fd })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Upload failed'); return }
      setStepData(data.step_data)
      setUploadResult({ source: data.source, days: data.days_found })
    } catch (e) {
      setError('Upload failed — check backend is running')
    } finally {
      setUploading(false)
    }
  }, [setStepData])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'text/xml': ['.xml'], 'application/xml': ['.xml'] },
    maxFiles: 1,
  })

  const connectGoogleFit = async () => {
    const res = await fetch('/auth/google')
    const data = await res.json()
    window.location.href = data.auth_url
  }

  const saveProfile = () => {
    if (!form.name) { setError('Please enter your name'); return }
    setUserProfile({
      name: form.name,
      age: Number(form.age) || 30,
      weight_kg: Number(form.weight_kg) || 70,
      height_cm: Number(form.height_cm) || 170,
    })
    setGoal({ type: goalForm.type, daily_target: Number(goalForm.target) })
    onDone()
  }

  return (
    <div style={{ maxWidth: 620, margin: '0 auto', padding: '48px 24px' }}>
      <div className="fade-in">
        <h1 style={{ fontFamily: 'Syne', fontSize: 32, fontWeight: 800, marginBottom: 6 }}>
          Welcome to FitAgent 🏃
        </h1>
        <p style={{ color: 'var(--text-muted)', marginBottom: 40, fontSize: 15 }}>
          Your AI-powered fitness coach. Set up your profile and import your step data to get started.
        </p>

        {/* Profile */}
        <section className="card" style={{ padding: 24, marginBottom: 20 }}>
          <h2 style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--brand)' }}>
            01 — Your Profile
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            {[
              { label: 'Name', key: 'name', placeholder: 'Alex', type: 'text', full: true },
              { label: 'Age', key: 'age', placeholder: '28', type: 'number' },
              { label: 'Weight (kg)', key: 'weight_kg', placeholder: '70', type: 'number' },
              { label: 'Height (cm)', key: 'height_cm', placeholder: '170', type: 'number' },
            ].map(f => (
              <div key={f.key} style={{ gridColumn: f.full ? 'span 2' : 'span 1' }}>
                <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 6, fontFamily: 'Syne' }}>
                  {f.label}
                </label>
                <input
                  type={f.type}
                  placeholder={f.placeholder}
                  value={form[f.key]}
                  onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                  style={{
                    width: '100%', padding: '10px 12px',
                    background: 'var(--surface)', border: '1px solid var(--border)',
                    borderRadius: 8, color: 'var(--text-primary)', fontSize: 14,
                    outline: 'none', fontFamily: 'DM Sans',
                  }}
                />
              </div>
            ))}
          </div>
        </section>

        {/* Goal */}
        <section className="card" style={{ padding: 24, marginBottom: 20 }}>
          <h2 style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--brand)' }}>
            02 — Daily Goal
          </h2>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <select
              value={goalForm.type}
              onChange={e => setGoalForm(p => ({ ...p, type: e.target.value }))}
              style={{
                padding: '10px 12px', background: 'var(--surface)',
                border: '1px solid var(--border)', borderRadius: 8,
                color: 'var(--text-primary)', fontFamily: 'DM Sans', fontSize: 14,
              }}
            >
              <option value="steps">Steps</option>
              <option value="calories">Calories</option>
            </select>
            <input
              type="number"
              value={goalForm.target}
              onChange={e => setGoalForm(p => ({ ...p, target: e.target.value }))}
              style={{
                flex: 1, padding: '10px 12px',
                background: 'var(--surface)', border: '1px solid var(--border)',
                borderRadius: 8, color: 'var(--text-primary)', fontFamily: 'DM Sans', fontSize: 14,
              }}
            />
            <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>per day</span>
          </div>
        </section>

        {/* Data Import */}
        <section className="card" style={{ padding: 24, marginBottom: 20 }}>
          <h2 style={{ fontFamily: 'Syne', fontSize: 16, fontWeight: 700, marginBottom: 4, color: 'var(--brand)' }}>
            03 — Import Step Data
          </h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
            Choose one method below — or skip and add data later.
          </p>

          {/* Apple Health */}
          <div style={{ marginBottom: 16 }}>
            <p style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>
              📱 Apple Health (iPhone)
            </p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>
              Open Health app → tap your profile → Export All Health Data → share the CSV or XML file here
            </p>
            <div
              {...getRootProps()}
              style={{
                border: `2px dashed ${isDragActive ? 'var(--brand)' : 'var(--border)'}`,
                borderRadius: 10, padding: '24px 16px', textAlign: 'center',
                cursor: 'pointer', transition: 'border-color 0.15s',
                background: isDragActive ? 'rgba(34,197,94,0.05)' : 'transparent',
              }}
            >
              <input {...getInputProps()} />
              {uploading
                ? <p style={{ color: 'var(--brand)', fontSize: 13 }}>Parsing file…</p>
                : uploadResult
                  ? <p style={{ color: 'var(--brand)', fontSize: 13 }}>
                      ✓ {uploadResult.days} days imported from {uploadResult.source}
                    </p>
                  : <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                      Drop your export.csv or export.xml here, or click to browse
                    </p>
              }
            </div>
          </div>

          {/* Google Fit */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
            <p style={{ fontSize: 13, fontWeight: 500, marginBottom: 8 }}>
              🤖 Google Fit (Android / cross-platform)
            </p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>
              Connect your Google account to automatically pull the last 30 days of step data.
            </p>
            <button className="btn-ghost" onClick={connectGoogleFit} style={{ fontSize: 13 }}>
              Connect Google Fit →
            </button>
          </div>
        </section>

        {error && (
          <p style={{ color: '#f87171', fontSize: 13, marginBottom: 12 }}>{error}</p>
        )}

        <button className="btn-primary" onClick={saveProfile} style={{ width: '100%', padding: '14px', fontSize: 15 }}>
          Continue to Dashboard →
        </button>
        <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 10 }}>
          You can skip data import and use sample data on the dashboard
        </p>
      </div>
    </div>
  )
}
