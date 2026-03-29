export default function Footer() {
  return (
    <footer className="border-t border-slate-800/60 py-8 mt-auto">
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
            G
          </div>
          <span className="text-sm text-slate-500">
            GitMax &mdash; GenAI Genesis Hackathon 2026
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm text-slate-500">
          <a
            href="https://github.com/rohanh03/github-conflict-ai"
            target="_blank"
            rel="noreferrer"
            className="hover:text-slate-300 transition-colors"
          >
            Source Code
          </a>
          <span className="text-slate-700">|</span>
          <span>Built with FastAPI + React</span>
        </div>
      </div>
    </footer>
  )
}
