import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

function StatusDot({ ok }) {
  return (
    <span className={`inline-block w-2.5 h-2.5 rounded-full ${ok ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
  )
}

function HealthCard({ health }) {
  if (!health) return null

  const formatUptime = (s) => {
    if (s < 60) return `${s}s`
    if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`
    return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg font-semibold text-white">Server Health</h3>
        <div className="flex items-center gap-2">
          <StatusDot ok={health.status === 'ok'} />
          <span className={`text-sm font-medium ${health.status === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
            {health.status === 'ok' ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl bg-slate-800/50 p-4">
          <p className="text-xs text-slate-500 mb-1">Uptime</p>
          <p className="text-lg font-semibold text-white">{formatUptime(health.uptime_seconds || 0)}</p>
        </div>
        <div className="rounded-xl bg-slate-800/50 p-4">
          <p className="text-xs text-slate-500 mb-1">Integrations</p>
          <div className="flex items-center gap-3 mt-1">
            <div className="flex items-center gap-1.5" title="GitHub">
              <StatusDot ok={health.github_configured} />
              <span className="text-xs text-slate-400">GH</span>
            </div>
            <div className="flex items-center gap-1.5" title="LLM">
              <StatusDot ok={health.llm_configured} />
              <span className="text-xs text-slate-400">LLM</span>
            </div>
            <div className="flex items-center gap-1.5" title="Slack">
              <StatusDot ok={health.slack_configured} />
              <span className="text-xs text-slate-400">Slack</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ConfigCard({ config }) {
  if (!config) return null

  const badges = {
    pat: { label: 'Personal Token', color: 'bg-green-500/20 text-green-400' },
    app: { label: 'GitHub App', color: 'bg-purple-500/20 text-purple-400' },
    none: { label: 'Not Configured', color: 'bg-red-500/20 text-red-400' },
  }

  const badge = badges[config.auth_mode] || badges.none

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg font-semibold text-white">Configuration</h3>
        <Link to="/setup" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
          Reconfigure →
        </Link>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Auth Mode</span>
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${badge.color}`}>{badge.label}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">LLM Model</span>
          <span className="text-sm text-slate-300 font-mono">{config.llm_model || '—'}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Slack</span>
          <span className={`text-sm ${config.slack_configured ? 'text-green-400' : 'text-slate-500'}`}>
            {config.slack_configured ? 'Connected' : 'Disabled'}
          </span>
        </div>
      </div>
    </div>
  )
}

function StatsCards({ stats }) {
  const cards = [
    { label: 'Events Processed', value: stats?.total_events ?? 0, gradient: 'from-blue-500 to-cyan-400' },
    { label: 'PRs Analyzed', value: stats?.prs_analyzed ?? 0, gradient: 'from-purple-500 to-pink-400' },
    { label: 'Conflicts Found', value: stats?.conflicts_detected ?? 0, gradient: 'from-amber-500 to-orange-400' },
  ]

  return (
    <div className="grid grid-cols-3 gap-4">
      {cards.map((c, i) => (
        <div key={i} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 text-center">
          <p className={`text-4xl font-bold bg-gradient-to-r ${c.gradient} bg-clip-text text-transparent`}>
            {c.value}
          </p>
          <p className="text-sm text-slate-400 mt-1">{c.label}</p>
        </div>
      ))}
    </div>
  )
}

function ActivityFeed({ events }) {
  const typeColors = {
    push: 'bg-blue-500/20 text-blue-400',
    pull_request: 'bg-purple-500/20 text-purple-400',
    issue_comment: 'bg-amber-500/20 text-amber-400',
  }

  const formatTime = (iso) => {
    const d = new Date(iso)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
      <h3 className="text-lg font-semibold text-white mb-5">Activity Feed</h3>

      {events && events.length > 0 ? (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {events.map((e, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-800/30 hover:bg-slate-800/50 transition-colors">
              <span className={`text-xs px-2 py-1 rounded-full font-medium whitespace-nowrap mt-0.5 ${typeColors[e.event_type] || 'bg-slate-700 text-slate-400'}`}>
                {e.event_type}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-white font-medium truncate">{e.repo || 'unknown'}</span>
                  {e.pr_number && (
                    <span className="text-xs text-slate-500">#{e.pr_number}</span>
                  )}
                </div>
                {e.conflicts_found > 0 && (
                  <span className="text-xs text-amber-400">{e.conflicts_found} conflict(s)</span>
                )}
              </div>
              <span className="text-xs text-slate-500 whitespace-nowrap">{formatTime(e.timestamp)}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-4xl mb-3">📡</div>
          <p className="text-slate-400">No activity yet</p>
          <p className="text-slate-500 text-sm mt-1">Configure a GitHub webhook to get started.</p>
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [config, setConfig] = useState(null)
  const [activity, setActivity] = useState({ events: [], stats: {} })
  const [error, setError] = useState(null)

  const fetchAll = async () => {
    try {
      const [h, c, a] = await Promise.all([api.health(), api.config(), api.activity()])
      setHealth(h)
      setConfig(c)
      setActivity(a)
      setError(null)
    } catch (e) {
      setError('Cannot reach backend. Is the server running on port 8000?')
    }
  }

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Monitor your GitMax instance</p>
        </div>
        <button
          onClick={fetchAll}
          className="px-4 py-2 rounded-lg border border-slate-700 text-sm text-slate-300 hover:bg-slate-800 transition-all"
        >
          ↻ Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 px-5 py-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          ⚠️ {error}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        <HealthCard health={health} />
        <ConfigCard config={config} />
      </div>

      <div className="mb-6">
        <StatsCards stats={activity.stats} />
      </div>

      <ActivityFeed events={activity.events} />
    </div>
  )
}
