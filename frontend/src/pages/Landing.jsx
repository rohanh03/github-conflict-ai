import { Link } from 'react-router-dom'

const features = [
  {
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
      </svg>
    ),
    title: 'Conflict Detection',
    desc: 'Automatically detect textual and semantic merge conflicts between branches before they break your build.',
    gradient: 'from-blue-500 to-cyan-400',
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
    ),
    title: 'PR Summaries',
    desc: 'AI-generated pull request summaries with complexity ratings, change breakdowns, and reviewer notes.',
    gradient: 'from-purple-500 to-pink-400',
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
      </svg>
    ),
    title: 'Slack Alerts',
    desc: 'Real-time conflict notifications delivered to your Slack channels with severity badges and fix suggestions.',
    gradient: 'from-amber-500 to-orange-400',
  },
]

const steps = [
  { num: '01', title: 'Configure', desc: 'Connect your GitHub credentials and LLM endpoint through our guided setup wizard.' },
  { num: '02', title: 'Install Webhook', desc: 'Point your repository webhook at GitMax — one URL, automatic conflict detection.' },
  { num: '03', title: 'Relax', desc: 'Get automatic conflict reports, PR summaries, and alerts. Focus on coding, not conflicts.' },
]

export default function Landing() {
  return (
    <div className="hero-glow">
      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-800/60 border border-slate-700/50 text-sm text-slate-300 mb-8">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-slow" />
          GenAI Genesis Hackathon 2026
        </div>

        <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight mb-6">
          <span className="gradient-text">GitMax</span>
        </h1>

        <p className="text-xl md:text-2xl text-slate-400 max-w-2xl mx-auto mb-4 leading-relaxed">
          AI-Powered Conflict Detection for GitHub
        </p>
        <p className="text-base md:text-lg text-slate-500 max-w-xl mx-auto mb-12">
          Detect merge conflicts, get intelligent PR summaries, and catch semantic issues before they break your build.
        </p>

        <div className="flex items-center justify-center gap-4">
          <Link
            to="/setup"
            className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold text-base hover:shadow-lg hover:shadow-blue-500/25 transition-all hover:scale-105"
          >
            Get Started
          </Link>
          <Link
            to="/dashboard"
            className="px-8 py-3.5 rounded-xl border border-slate-700 text-slate-300 font-semibold text-base hover:bg-slate-800/50 hover:border-slate-600 transition-all"
          >
            View Dashboard
          </Link>
        </div>

        {/* Terminal mockup */}
        <div className="mt-20 max-w-2xl mx-auto">
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 overflow-hidden shadow-2xl">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800 bg-slate-900">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-green-500/80" />
              <span className="ml-3 text-xs text-slate-500 font-mono">conflict-report</span>
            </div>
            <div className="p-5 text-left font-mono text-sm leading-relaxed">
              <div className="text-slate-500">## Conflict Alert — feature-auth × feature-payments</div>
              <div className="mt-2">
                <span className="text-red-400">⚠ Merge Conflict</span>
                <span className="text-slate-500"> — </span>
                <span className="text-slate-300">app.py</span>
                <span className="text-slate-600"> (high severity)</span>
              </div>
              <div className="mt-1">
                <span className="text-amber-400">⚡ Semantic Conflict</span>
                <span className="text-slate-500"> — </span>
                <span className="text-slate-300">validate_token → verify_token rename</span>
              </div>
              <div className="mt-1">
                <span className="text-blue-400">💡 Fix:</span>
                <span className="text-slate-400"> Update payments to use verify_token()</span>
              </div>
              <div className="mt-3 text-slate-600">Scan duration: 245ms · 2 conflict(s) found</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-4">
          Everything you need
        </h2>
        <p className="text-slate-400 text-center mb-14 max-w-lg mx-auto">
          Proactive conflict detection powered by AI, integrated directly into your GitHub workflow.
        </p>

        <div className="grid md:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div
              key={i}
              className="group rounded-2xl border border-slate-800 bg-slate-900/50 p-7 hover:border-slate-700 transition-all card-glow"
            >
              <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${f.gradient} p-3 text-white mb-5 group-hover:scale-110 transition-transform`}>
                {f.icon}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-14">
          How it works
        </h2>

        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((s, i) => (
            <div key={i} className="text-center">
              <div className="text-5xl font-extrabold gradient-text mb-4">{s.num}</div>
              <h3 className="text-xl font-semibold text-white mb-2">{s.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed max-w-xs mx-auto">{s.desc}</p>
            </div>
          ))}
        </div>

        <div className="text-center mt-14">
          <Link
            to="/setup"
            className="inline-flex px-8 py-3.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold hover:shadow-lg hover:shadow-blue-500/25 transition-all hover:scale-105"
          >
            Start Setup →
          </Link>
        </div>
      </section>
    </div>
  )
}
