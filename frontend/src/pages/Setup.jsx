import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

const STEPS = ['Auth Mode', 'Credentials', 'LLM Config', 'Slack', 'Test']

function StepIndicator({ current }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-12">
      {STEPS.map((label, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${
              i < current
                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                : i === current
                ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
                : 'bg-slate-800 text-slate-500 border border-slate-700'
            }`}
          >
            {i < current ? '✓' : i + 1}
          </div>
          <span className={`text-xs hidden md:block ${i === current ? 'text-white' : 'text-slate-500'}`}>
            {label}
          </span>
          {i < STEPS.length - 1 && (
            <div className={`w-8 h-px ${i < current ? 'bg-green-500/30' : 'bg-slate-700'}`} />
          )}
        </div>
      ))}
    </div>
  )
}

// mar15 fixed: use conditional classes instead of disabled attr for gradient button
function AuthModeStep({ authMode, setAuthMode, onNext }) {
  const handleSelect = (id) => {
    setAuthMode(id)
  }

  const handleContinue = () => {
    if (authMode) {
      onNext()
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">Choose Authentication</h2>
      <p className="text-slate-400 mb-8">How should GitMax connect to GitHub?</p>

      <div className="grid md:grid-cols-2 gap-4 max-w-2xl mx-auto">
        {[
          {
            id: 'pat',
            title: 'Personal Access Token',
            desc: 'Simple setup — great for quick testing and personal repos.',
            tag: 'Recommended',
          },
          {
            id: 'app',
            title: 'GitHub App',
            desc: 'Fine-grained permissions — ideal for organizations and production.',
            tag: 'Advanced',
          },
        ].map((opt) => (
          <button
            key={opt.id}
            type="button"
            onClick={() => handleSelect(opt.id)}
            className={`text-left rounded-xl border p-6 transition-all cursor-pointer ${
              authMode === opt.id
                ? 'border-blue-500 bg-blue-500/10 ring-2 ring-blue-500/30'
                : 'border-slate-700 bg-slate-900/50 hover:border-slate-600'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-white">{opt.title}</h3>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                opt.id === 'pat' ? 'bg-green-500/20 text-green-400' : 'bg-purple-500/20 text-purple-400'
              }`}>
                {opt.tag}
              </span>
            </div>
            <p className="text-sm text-slate-400">{opt.desc}</p>
          </button>
        ))}
      </div>

      <div className="mt-8 flex justify-center">
        <button
          type="button"
          onClick={handleContinue}
          disabled={!authMode}
          className={`px-8 py-3 rounded-xl font-semibold transition-all ${
            authMode
              ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:shadow-lg hover:shadow-blue-500/25 cursor-pointer'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-40'
          }`}
        >
          Continue →
        </button>
      </div>
    </div>
  )
}

function CredentialsStep({ authMode, creds, setCreds, onNext, onBack }) {
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState(null)

  // mar15 added try/catch so button doesn't get stuck on network failure
  const save = async () => {
    setSaving(true)
    setResult(null)
    try {
      const res = await api.saveAuth({ mode: authMode, ...creds })
      setResult(res)
      if (res.success) setTimeout(onNext, 600)
    } catch (e) {
      setResult({ success: false, message: `Connection failed: ${e.message}` })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-bold text-white mb-2">
        {authMode === 'pat' ? 'Personal Access Token' : 'GitHub App Credentials'}
      </h2>
      <p className="text-slate-400 mb-8">
        {authMode === 'pat'
          ? 'Generate a token at GitHub → Settings → Developer settings → Personal access tokens.'
          : 'Enter your GitHub App credentials from the app settings page.'}
      </p>

      <div className="space-y-4">
        {authMode === 'pat' ? (
          <>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Repository Full Name</label>
              <input
                type="text"
                placeholder="owner/private-repo"
                value={creds.repo_full_name || ''}
                onChange={(e) => setCreds({ ...creds, repo_full_name: e.target.value })}
                className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all font-mono text-sm"
              />
              <p className="mt-2 text-xs text-slate-500">
                Save the exact repo you will attach the webhook to so GitMax can match incoming events to the right PAT.
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">GitHub Token</label>
              <input
                type="password"
                placeholder="ghp_xxxxxxxxxxxx"
                value={creds.github_token || ''}
                onChange={(e) => setCreds({ ...creds, github_token: e.target.value })}
                className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
              />
            </div>
          </>
        ) : (
          <>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">App ID</label>
              <input
                type="text"
                placeholder="123456"
                value={creds.github_app_id || ''}
                onChange={(e) => setCreds({ ...creds, github_app_id: e.target.value })}
                className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Private Key Path</label>
              <input
                type="text"
                placeholder="./github-app-private-key.pem"
                value={creds.github_private_key_path || ''}
                onChange={(e) => setCreds({ ...creds, github_private_key_path: e.target.value })}
                className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
              />
            </div>
          </>
        )}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">Webhook Secret (optional)</label>
          <input
            type="password"
            placeholder="your-webhook-secret"
            value={creds.github_webhook_secret || ''}
            onChange={(e) => setCreds({ ...creds, github_webhook_secret: e.target.value })}
            className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
          />
        </div>
      </div>

      {result && (
        <div className={`mt-4 px-4 py-3 rounded-xl text-sm ${result.success ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
          {result.message}
        </div>
      )}

      <div className="mt-8 flex justify-between">
        <button onClick={onBack} className="px-6 py-3 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 transition-all">
          ← Back
        </button>
        <button
          onClick={save}
          disabled={saving}
          className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold disabled:opacity-60 hover:shadow-lg hover:shadow-blue-500/25 transition-all"
        >
          {saving ? 'Saving...' : 'Save & Continue →'}
        </button>
      </div>
    </div>
  )
}

function LLMStep({ llm, setLLM, onNext, onBack }) {
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState(null)

  // mar15 added try/catch so button doesn't get stuck on network failure
  const save = async () => {
    setSaving(true)
    setResult(null)
    try {
      const res = await api.saveLLM(llm)
      setResult(res)
      if (res.success) setTimeout(onNext, 600)
    } catch (e) {
      setResult({ success: false, message: `Connection failed: ${e.message}` })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-bold text-white mb-2">LLM Configuration</h2>
      <p className="text-slate-400 mb-2">Configure your AI model endpoint for semantic analysis and PR summaries.</p>
      <div className="px-4 py-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm mb-8">
        💡 Defaults are pre-configured for the hackathon GPT-OSS server. Leave as-is to get started quickly.
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">API Base URL</label>
          <input
            type="text"
            value={llm.llm_api_base || ''}
            onChange={(e) => setLLM({ ...llm, llm_api_base: e.target.value })}
            className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all font-mono text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">API Key</label>
          <input
            type="password"
            value={llm.llm_api_key || ''}
            onChange={(e) => setLLM({ ...llm, llm_api_key: e.target.value })}
            className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">Model</label>
          <input
            type="text"
            value={llm.llm_model || ''}
            onChange={(e) => setLLM({ ...llm, llm_model: e.target.value })}
            className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all font-mono text-sm"
          />
        </div>
      </div>

      {result && (
        <div className={`mt-4 px-4 py-3 rounded-xl text-sm ${result.success ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
          {result.message}
        </div>
      )}

      <div className="mt-8 flex justify-between">
        <button onClick={onBack} className="px-6 py-3 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 transition-all">
          ← Back
        </button>
        <button
          onClick={save}
          disabled={saving}
          className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold disabled:opacity-60 hover:shadow-lg hover:shadow-blue-500/25 transition-all"
        >
          {saving ? 'Saving...' : 'Save & Continue →'}
        </button>
      </div>
    </div>
  )
}

function SlackStep({ slack, setSlack, onNext, onBack }) {
  const [saving, setSaving] = useState(false)

  // mar15 added try/catch so button doesn't get stuck on network failure
  const save = async () => {
    setSaving(true)
    try {
      await api.saveSlack({ slack_webhook_url: slack })
      onNext()
    } catch (e) {
      // still advance — slack is optional
      onNext()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-bold text-white mb-2">Slack Integration</h2>
      <p className="text-slate-400 mb-8">Optionally send conflict alerts to a Slack channel. You can skip this step.</p>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1.5">Slack Webhook URL</label>
        <input
          type="text"
          placeholder="https://hooks.slack.com/services/..."
          value={slack}
          onChange={(e) => setSlack(e.target.value)}
          className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all font-mono text-sm"
        />
      </div>

      <div className="mt-8 flex justify-between">
        <button onClick={onBack} className="px-6 py-3 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 transition-all">
          ← Back
        </button>
        <div className="flex gap-3">
          <button
            onClick={onNext}
            className="px-6 py-3 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 transition-all"
          >
            Skip
          </button>
          <button
            onClick={save}
            disabled={saving || !slack}
            className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-blue-500/25 transition-all"
          >
            {saving ? 'Saving...' : 'Save & Continue →'}
          </button>
        </div>
      </div>
    </div>
  )
}

function TestStep({ onBack, creds }) {
  const [tests, setTests] = useState({
    github: { status: 'idle', message: '' },
    llm: { status: 'idle', message: '' },
    slack: { status: 'idle', message: '' },
  })
  const [done, setDone] = useState(false)

  const runTest = async (key, fn) => {
    setTests((t) => ({ ...t, [key]: { status: 'loading', message: 'Testing...' } }))
    try {
      const res = await fn()
      setTests((t) => ({
        ...t,
        [key]: { status: res.success ? 'pass' : 'fail', message: res.message },
      }))
    } catch (e) {
      setTests((t) => ({ ...t, [key]: { status: 'fail', message: e.message } }))
    }
  }

  const statusIcon = (s) => {
    if (s === 'loading') return <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
    if (s === 'pass') return <span className="text-green-400 text-lg">✓</span>
    if (s === 'fail') return <span className="text-red-400 text-lg">✗</span>
    return <span className="text-slate-500 text-lg">○</span>
  }

  const statusColor = (s) => {
    if (s === 'pass') return 'border-green-500/30 bg-green-500/5'
    if (s === 'fail') return 'border-red-500/30 bg-red-500/5'
    if (s === 'loading') return 'border-blue-500/30 bg-blue-500/5'
    return 'border-slate-700 bg-slate-900/50'
  }

  const testCards = [
    { key: 'github', label: 'GitHub Connection', fn: () => api.testGithub({ repo_full_name: creds.repo_full_name || '' }) },
    { key: 'llm', label: 'LLM Endpoint', fn: api.testLLM },
    { key: 'slack', label: 'Slack Webhook', fn: api.testSlack },
  ]

  return (
    <div className="max-w-lg mx-auto">
      {!done ? (
        <>
          <h2 className="text-2xl font-bold text-white mb-2">Test Connections</h2>
          <p className="text-slate-400 mb-8">Verify your integrations are working. At least GitHub should pass.</p>

          <div className="space-y-4">
            {testCards.map((t) => (
              <div key={t.key} className={`rounded-xl border p-5 transition-all ${statusColor(tests[t.key].status)}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {statusIcon(tests[t.key].status)}
                    <span className="font-medium text-white">{t.label}</span>
                  </div>
                  <button
                    onClick={() => runTest(t.key, t.fn)}
                    disabled={tests[t.key].status === 'loading'}
                    className="px-4 py-1.5 rounded-lg text-sm bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 disabled:opacity-40 transition-all"
                  >
                    {tests[t.key].status === 'loading' ? 'Testing...' : 'Test'}
                  </button>
                </div>
                {tests[t.key].message && (
                  <p className={`mt-2 text-sm ${tests[t.key].status === 'pass' ? 'text-green-400' : tests[t.key].status === 'fail' ? 'text-red-400' : 'text-slate-400'}`}>
                    {tests[t.key].message}
                  </p>
                )}
              </div>
            ))}
          </div>

          <div className="mt-8 flex justify-between">
            <button onClick={onBack} className="px-6 py-3 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 transition-all">
              ← Back
            </button>
            <button
              onClick={() => setDone(true)}
              className="px-8 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold hover:shadow-lg hover:shadow-blue-500/25 transition-all"
            >
              Complete Setup →
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-8">
          <div className="w-20 h-20 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl text-green-400">✓</span>
          </div>
          <h2 className="text-3xl font-bold text-white mb-3">You're all set!</h2>
          <p className="text-slate-400 mb-8">GitMax is configured and ready to detect conflicts.</p>

          {/* mar15 use actual server origin for webhook URL */}
          <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-5 max-w-lg mx-auto mb-6">
            <p className="text-sm text-slate-400 mb-2">Add this as a webhook in your GitHub repo:</p>
            <p className="text-xs text-slate-500 mb-3">
              Go to <span className="text-slate-300">Settings → Webhooks → Add webhook</span> and paste this Payload URL:
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 bg-slate-800 px-4 py-2.5 rounded-lg text-blue-400 text-sm font-mono text-left overflow-x-auto">
                {window.location.origin.replace(':5173', ':8000')}/webhooks/github
              </code>
              <button
                onClick={() => navigator.clipboard.writeText(
                  window.location.origin.replace(':5173', ':8000') + '/webhooks/github'
                )}
                className="px-3 py-2.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-colors shrink-0"
                title="Copy"
              >
                📋
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-slate-700/50 bg-slate-900/30 p-4 max-w-lg mx-auto mb-8 text-left">
            <p className="text-xs font-medium text-slate-300 mb-2">Webhook settings:</p>
            <ul className="text-xs text-slate-400 space-y-1">
              <li>• <span className="text-slate-300">Content type:</span> application/json</li>
              <li>• <span className="text-slate-300">Events:</span> Pull requests, Pushes, Issue comments</li>
              <li>• <span className="text-slate-300">Secret:</span> the webhook secret you entered in step 2</li>
            </ul>
          </div>

          <Link
            to="/dashboard"
            className="inline-flex px-8 py-3.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold hover:shadow-lg hover:shadow-blue-500/25 transition-all hover:scale-105"
          >
            Go to Dashboard →
          </Link>
        </div>
      )}
    </div>
  )
}

export default function Setup() {
  const [step, setStep] = useState(0)
  const [authMode, setAuthMode] = useState('')
  const [creds, setCreds] = useState({})
  const [llm, setLLM] = useState({
    llm_api_base: 'https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1',
    llm_api_key: 'test',
    llm_model: 'openai/gpt-oss-120b',
  })
  const [slack, setSlack] = useState('')

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1))
  const back = () => setStep((s) => Math.max(s - 1, 0))

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <div className="text-center mb-4">
        <h1 className="text-4xl font-bold text-white mb-2">Setup Wizard</h1>
        <p className="text-slate-400">Configure GitMax in a few easy steps</p>
      </div>

      <StepIndicator current={step} />

      {step === 0 && <AuthModeStep authMode={authMode} setAuthMode={setAuthMode} onNext={next} />}
      {step === 1 && <CredentialsStep authMode={authMode} creds={creds} setCreds={setCreds} onNext={next} onBack={back} />}
      {step === 2 && <LLMStep llm={llm} setLLM={setLLM} onNext={next} onBack={back} />}
      {step === 3 && <SlackStep slack={slack} setSlack={setSlack} onNext={next} onBack={back} />}
      {step === 4 && <TestStep onBack={back} creds={creds} />}
    </div>
  )
}
