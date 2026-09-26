import Navbar from '../components/Navbar';

const layers = [
  {
    id: 'source',
    label: 'Source Layer',
    color: '#0F62FE',
    nodes: [
      { title: 'Git Repository', sub: 'GitHub / GitLab / Bitbucket', detail: 'Commits, branches, pull requests' },
      { title: 'GitHub Webhooks', sub: 'Push events, PR events', detail: 'Real-time diff delivery' },
    ],
  },
  {
    id: 'parsing',
    label: 'Parsing Layer',
    color: '#393939',
    nodes: [
      { title: 'Diff Parser', sub: 'Unified diff format', detail: 'Extract changed lines and hunks' },
      { title: 'AST Builder', sub: 'Tree-sitter', detail: 'Build syntax tree from changed files' },
    ],
  },
  {
    id: 'analysis',
    label: 'Analysis Layer',
    color: '#393939',
    nodes: [
      { title: 'Syntax Analyzer', sub: 'Language-aware parsing', detail: 'JS, TS, Python, Go, Java' },
      { title: 'Security Scanner', sub: 'Semgrep rules', detail: 'Known vulnerability patterns' },
      { title: 'Complexity Analyzer', sub: 'Cyclomatic complexity', detail: 'Cognitive load metrics' },
      { title: 'Code Quality', sub: 'Lint + style rules', detail: 'Anti-pattern detection' },
    ],
  },
  {
    id: 'ai',
    label: 'Intelligence Layer',
    color: '#0F62FE',
    nodes: [
      { title: 'AI Service', sub: 'IBM watsonx.ai', detail: 'LLM-assisted recommendations' },
      { title: 'Rules Engine', sub: 'Deterministic checks', detail: 'Pattern + heuristic analysis' },
      { title: 'Prompt Templates', sub: 'Domain-specific prompts', detail: 'Debug, optimize, explain' },
    ],
  },
  {
    id: 'output',
    label: 'Output Layer',
    color: '#198038',
    nodes: [
      { title: 'Findings API', sub: 'REST / FastAPI', detail: 'Structured JSON findings' },
      { title: 'CodeLens UI', sub: 'React + TypeScript', detail: 'Developer-facing interface' },
      { title: 'Jira Integration', sub: 'Atlassian REST API', detail: 'Ticket creation from findings' },
    ],
  },
];

const dataFlows = [
  { from: 'Git Repository', to: 'Diff Parser', label: 'raw diff' },
  { from: 'Diff Parser', to: 'AST Builder', label: 'change objects' },
  { from: 'AST Builder', to: 'Syntax Analyzer', label: 'syntax tree' },
  { from: 'Syntax Analyzer', to: 'AI Service', label: 'analyzed structure' },
  { from: 'AI Service', to: 'Findings API', label: 'insights + recommendations' },
  { from: 'Findings API', to: 'CodeLens UI', label: 'structured findings' },
];

export default function Architecture() {
  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        {/* Header */}
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-8">
          <div className="max-w-6xl mx-auto">
            <p className="text-label mb-2">System Architecture</p>
            <h1 className="text-2xl font-semibold text-[#161616] mb-2">
              Built around the developer workflow.
            </h1>
            <p className="text-sm text-[#525252] max-w-xl">
              CodeLens uses a layered architecture where deterministic static analysis is always run first,
              followed by AI-assisted interpretation. The AI layer augments the analysis — it does not replace it.
            </p>
          </div>
        </div>

        <div className="max-w-6xl mx-auto px-6 py-10">
          {/* Layer diagram */}
          <div className="mb-12">
            <h2 className="text-sm font-semibold text-[#161616] mb-6 uppercase tracking-wide">System Layers</h2>
            <div className="space-y-3">
              {layers.map((layer) => (
                <div key={layer.id} className="border border-[#D0D0D0] bg-white overflow-hidden">
                  <div
                    className="px-4 py-2 flex items-center gap-3"
                    style={{ borderLeft: `3px solid ${layer.color}` }}
                  >
                    <span className="text-xs font-semibold text-[#161616]">{layer.label}</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-x divide-[#E0E0E0] border-t border-[#E0E0E0]">
                    {layer.nodes.map((node) => (
                      <div key={node.title} className="px-4 py-3">
                        <p className="text-sm font-semibold text-[#161616] mb-0.5">{node.title}</p>
                        <p className="text-xs text-[#0F62FE] font-mono mb-1">{node.sub}</p>
                        <p className="text-xs text-[#525252]">{node.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Data flow */}
          <div className="mb-12">
            <h2 className="text-sm font-semibold text-[#161616] mb-6 uppercase tracking-wide">Data Flow</h2>
            <div className="border border-[#D0D0D0] bg-white p-6">
              <div className="flex flex-col lg:flex-row items-start lg:items-center gap-0 overflow-x-auto">
                {dataFlows.map((flow, i) => (
                  <div key={i} className="flex flex-col lg:flex-row items-center">
                    <div className="border border-[#D0D0D0] px-3 py-2 text-center min-w-[130px]">
                      <p className="text-xs font-semibold text-[#161616]">{flow.from}</p>
                    </div>
                    <div className="flex flex-col lg:flex-row items-center">
                      <div className="w-px h-4 lg:h-px lg:w-6 bg-[#D0D0D0]" />
                      <div className="px-2 py-0.5 bg-[#F4F4F4] border border-[#D0D0D0] my-1 lg:my-0">
                        <span className="font-mono text-[9px] text-[#525252] whitespace-nowrap">{flow.label}</span>
                      </div>
                      <div className="w-px h-4 lg:h-px lg:w-6 bg-[#D0D0D0]" />
                      <svg width="8" height="8" viewBox="0 0 8 8" fill="none" className="text-[#D0D0D0] rotate-90 lg:rotate-0 shrink-0">
                        <path d="M1 4L7 4M5 2L7 4L5 6" stroke="#525252" strokeWidth="1.2"/>
                      </svg>
                    </div>
                    {i === dataFlows.length - 1 && (
                      <div className="border border-[#0F62FE] bg-[#EDF4FF] px-3 py-2 text-center min-w-[130px]">
                        <p className="text-xs font-semibold text-[#0F62FE]">{flow.to}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Design principles */}
          <div>
            <h2 className="text-sm font-semibold text-[#161616] mb-6 uppercase tracking-wide">
              Design Principles
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                {
                  num: '01',
                  title: 'Deterministic First',
                  desc: 'Static analysis runs before AI. Results are reproducible and auditable regardless of LLM availability.',
                },
                {
                  num: '02',
                  title: 'AI Augments, Not Replaces',
                  desc: 'The AI layer interprets and explains findings from deterministic analysis. It does not generate findings independently.',
                },
                {
                  num: '03',
                  title: 'Developer Approval Required',
                  desc: 'No external system (Jira, GitHub, PRs) is modified without explicit developer review and confirmation.',
                },
              ].map((p) => (
                <div key={p.num} className="border border-[#D0D0D0] bg-white p-5">
                  <div className="font-mono text-2xl font-light text-[#D0D0D0] mb-3">{p.num}</div>
                  <h3 className="text-sm font-semibold text-[#161616] mb-2">{p.title}</h3>
                  <p className="text-xs text-[#525252] leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
