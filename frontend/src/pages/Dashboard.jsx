import { useState, useEffect } from 'react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts'

const SAMPLE_DATA = Array.from({ length: 30 }, (_, i) => {
  const d = new Date(2024, 0, i + 1)
  return {
    date: d.toISOString().slice(0, 10),
    steps: Math.floor(6000 + Math.random() * 6000),
  }
})

const fmt = n => n?.toLocaleString() ?? '—'

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="card" style={{ padding: '20px 22px' }}>
      <p style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'Syne', marginBottom: 6 }}>{label}</p>
      <p style={{ fontSize: 28, fontWeight: 800, fontFamily: 'Syne', color: accent || 'var(--text-primary)', marginBottom: 2 }}>
        {value}
      </p>
      {sub && <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{sub}</p>}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--card)', border: '1px solid var(--border)',
      borderRadius: 8, padding: '10px 14px', fontSize: 13,
    }}>
      <p style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
      <p style={{ color: 'var(--brand)', fontWeight: 600 }}>{fmt(payload[0].value)} steps</p>
    </div>
  )
}

export default function Dashboard({ stepData, userProfile, goal, setStepData, onChat }) {
  const data = stepData.length > 0 ? stepData : SAMPLE_DATA
  const isDemo = stepData.length === 0

  const steps = data.map(d => d.steps)
  const avg = Math.round(steps.reduce((a, b) => a + b, 0) / steps.length)
  const best = Math.max(...steps)
  const goalTarget = goal?.daily_target || 10000

  // Calorie estimate (rough: 0.04 cal/step for 70kg)
  const weight = userProfile?.weight_kg || 70
  const calPerStep = 0.04 * (weight / 70)
  const avgCal = Math.round(avg * calPerStep)

  // Chart data: last 14 days
  const chartData = data.slice(-14).map(d => ({
    date: d.date.slice(5),  // MM-DD
    steps: d.steps,
    goal: goalTarget,
  }))

  // Weekly breakdown
  const weeklyMap = {}
  data.forEach(d => {
    const dt = new Date(d.date)
    const week = `W${Math.ceil(dt.getDate() / 7)} ${dt.toLocaleString('default', { month: 'short' })}`
    if (!weeklyMap[week]) weeklyMap[week] = []
    weeklyMap[week].push(d.steps)
  })
  const weeklyData = Object.entries(weeklyMap).slice(-6).map(([week, vals]) => ({
    week,
    avg: Math.round(vals.reduce((a, b) => a + b, 0) / vals.length),
  }))

  const daysAboveGoal = steps.filter(s => s >= goalTarget).length
  const streak = (() => {
    let s = 0
    for (let i = steps.length - 1; i >= 0; i--) {
      if (steps[i] >= goalTarget) s++; else break
    }
    return s
  })()

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '36px 24px' }}>
      {isDemo && (
        <div style={{
          background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)',
          borderRadius: 10, padding: '10px 16px', marginBottom: 24, fontSize: 13,
          color: 'var(--brand)',
        }}>
          📊 Showing demo data — go to Setup to import your own step history
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne', fontSize: 26, fontWeight: 800, margin: 0 }}>
            {userProfile ? `Hey, ${userProfile.name} 👋` : 'Your Dashboard'}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 4 }}>
            Last {data.length} days · goal: {fmt(goalTarget)} steps/day
          </p>
        </div>
        <button className="btn-primary" onClick={onChat}>
          Ask FitAgent →
        </button>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 24 }}>
        <StatCard label="AVG DAILY STEPS" value={fmt(avg)} sub={`${Math.round(avg/goalTarget*100)}% of goal`} accent="var(--brand)" />
        <StatCard label="AVG CALORIES BURNED" value={fmt(avgCal)} sub="active kcal estimate" />
        <StatCard label="CURRENT STREAK" value={`${streak}d`} sub="days above goal" />
        <StatCard label="DAYS ABOVE GOAL" value={daysAboveGoal} sub={`of ${data.length} days`} />
      </div>

      {/* Area Chart */}
      <div className="card" style={{ padding: '24px', marginBottom: 20 }}>
        <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, marginBottom: 20, color: 'var(--text-soft)' }}>
          DAILY STEPS — LAST 14 DAYS
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="stepGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={goalTarget} stroke="rgba(34,197,94,0.4)" strokeDasharray="4 4" label={{ value: 'Goal', fill: 'var(--brand)', fontSize: 11 }} />
            <Area type="monotone" dataKey="steps" stroke="#22c55e" strokeWidth={2} fill="url(#stepGrad)" dot={false} activeDot={{ r: 4, fill: '#22c55e' }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart */}
      <div className="card" style={{ padding: '24px' }}>
        <h3 style={{ fontFamily: 'Syne', fontSize: 14, fontWeight: 700, marginBottom: 20, color: 'var(--text-soft)' }}>
          WEEKLY AVERAGE STEPS
        </h3>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={weeklyData} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="week" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={goalTarget} stroke="rgba(34,197,94,0.4)" strokeDasharray="4 4" />
            <Bar dataKey="avg" fill="#22c55e" radius={[4, 4, 0, 0]} opacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
