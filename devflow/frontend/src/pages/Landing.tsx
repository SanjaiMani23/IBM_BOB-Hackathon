import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';

// ─── Hero ───────────────────────────────────────────────────────────────────

function Hero() {
  const navigate = useNavigate();
  return (
    <section className="pt-12 hero-grid-bg border-b border-[#303030]">
      <div className="max-w-7xl mx-auto px-6 py-16 lg:py-24 grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
        {/* Left */}
        <div>
          <p className="text-label mb-4" style={{ color: '#6F6F6F' }}>Developer Intelligence Platform</p>
          <h1 className="text-3xl lg:text-4xl xl:text-5xl font-semibold leading-tight tracking-tight mb-6" style={{ color: '#F4F4F4' }}>
            Turn Code Changes Into<br />
            <span className="text-[#0F62FE]">Actionable Insights.</span>
          </h1>
          <p className="text-base leading-relaxed mb-8 max-w-md" style={{ color: '#8D8D8D' }}>
            Analyze Git diffs, identify potential bugs, understand structural changes,
            detect optimization opportunities and generate clear developer recommendations.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => navigate('/analyzer')}
              className="px-5 py-2.5 bg-[#0F62FE] text-white text-sm font-medium hover:bg-[#0353E9] transition-colors"
            >
              Analyze a Diff
            </button>
            <button
              onClick={() => {
                document.getElementById('workflow')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="px-5 py-2.5 text-sm font-medium transition-colors"
              style={{ border: '1px solid #393939', color: '#C6C6C6', background: 'transparent' }}
            >
              View Workflow
            </button>
          </div>
        </div>

        {/* Right — product demo video */}
        <div className="border border-[#D0D0D0] bg-white overflow-hidden w-full" style={{ aspectRatio: '16/9' }}>
          <video
            src="/videos/Create_a_premium_second_D_c.mp4"
            autoPlay
            muted
            loop
            playsInline
            className="w-full h-full object-cover block"
          />
        </div>
      </div>
    </section>
  );
}

// ─── Workflow ────────────────────────────────────────────────────────────────

const workflowSteps = [
  { num: '01', title: 'Git Diff', desc: 'Parse the raw diff from a commit, PR or branch comparison.' },
  { num: '02', title: 'Parse', desc: 'Tokenize changed lines into AST nodes and structured change objects.' },
  { num: '03', title: 'Analyze', desc: 'Run static analysis, complexity scoring and security pattern matching.' },
  { num: '04', title: 'Detect', desc: 'Identify potential bugs, regressions, anti-patterns and risks.' },
  { num: '05', title: 'Optimize', desc: 'Surface performance and structural improvement opportunities.' },
  { num: '06', title: 'Report', desc: 'Generate prioritized findings with actionable developer recommendations.' },
];

function Workflow() {
  return (
    <section id="workflow" className="bg-[#F4F4F4] border-b border-[#D0D0D0] py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-10">
          <p className="text-label mb-2">Core Workflow</p>
          <h2 className="text-2xl lg:text-3xl font-semibold text-[#161616] tracking-tight">
            From code change to developer insight.
          </h2>
        </div>
        {/* Timeline */}
        <div className="relative">
          {/* Connecting line */}
          <div className="hidden lg:block absolute top-7 left-0 right-0 h-px bg-[#D0D0D0]" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6 lg:gap-0">
            {workflowSteps.map((step, i) => (
              <div key={step.num} className="relative lg:px-4">
                {/* Active dot */}
                <div className={`hidden lg:flex absolute top-[22px] left-1/2 -translate-x-1/2 w-4 h-4 border-2 items-center justify-center ${
                  i === 0 ? 'border-[#0F62FE] bg-[#0F62FE]' : 'border-[#D0D0D0] bg-white'
                }`}>
                  {i === 0 && <span className="w-1.5 h-1.5 bg-white" />}
                </div>
                <div className="lg:pt-12">
                  <span className="font-mono text-2xl font-light text-[#D0D0D0] leading-none">{step.num}</span>
                  <h3 className={`text-sm font-semibold mt-2 mb-1.5 ${i === 0 ? 'text-[#0F62FE]' : 'text-[#161616]'}`}>
                    {step.title}
                  </h3>
                  <p className="text-xs text-[#525252] leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Features ────────────────────────────────────────────────────────────────

const features = [
  {
    marker: '01',
    title: 'Debugging',
    desc: 'Identify potential bugs and suspicious changes introduced by a commit. Surface null references, missing error handling and logic regressions.',
  },
  {
    marker: '02',
    title: 'Code Optimization',
    desc: 'Detect inefficient patterns such as repeated database calls inside loops, redundant computations and unnecessary allocations.',
  },
  {
    marker: '03',
    title: 'Structural Analysis',
    desc: 'Understand how the changed code affects the existing project structure. Track coupling, cohesion and module boundaries across the diff.',
  },
  {
    marker: '04',
    title: 'Change Impact',
    desc: 'Highlight affected files, functions, modules and downstream dependencies so developers understand the blast radius before merging.',
  },
  {
    marker: '05',
    title: 'Developer Recommendations',
    desc: 'Convert analysis results into clear, prioritized, actionable recommendations that developers can act on immediately.',
  },
];

function Features() {
  return (
    <section id="features" className="bg-white border-b border-[#D0D0D0] py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-10">
          <p className="text-label mb-2">Core Capabilities</p>
          <h2 className="text-2xl lg:text-3xl font-semibold text-[#161616] tracking-tight">
            Everything needed to understand a code change.
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f) => (
            <div
              key={f.marker}
              className="border border-[#D0D0D0] bg-white p-5 hover:border-[#0F62FE] transition-colors group"
            >
              <div className="flex items-start gap-3 mb-3">
                <span className="font-mono text-xs text-[#0F62FE] font-medium mt-0.5">{f.marker}</span>
                <h3 className="text-sm font-semibold text-[#161616] group-hover:text-[#0F62FE] transition-colors">
                  {f.title}
                </h3>
              </div>
              <p className="text-xs text-[#525252] leading-relaxed pl-6">{f.desc}</p>
            </div>
          ))}
          {/* CTA card */}
          <div className="border border-[#0F62FE] bg-[#EDF4FF] p-5 flex flex-col justify-between">
            <div>
              <p className="text-[10px] font-mono text-[#0F62FE] uppercase tracking-wide mb-2">Get Started</p>
              <p className="text-sm text-[#161616] font-medium leading-snug">
                Analyze your first Git diff in under 60 seconds.
              </p>
            </div>
            <a href="/analyzer" className="mt-4 text-xs font-medium text-[#0F62FE] hover:underline">
              Open Analyzer →
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Analyzer Preview ────────────────────────────────────────────────────────

function AnalyzerPreview() {
  return (
    <section id="product" className="bg-[#F4F4F4] border-b border-[#D0D0D0] py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-10">
          <p className="text-label mb-2">Interface Preview</p>
          <h2 className="text-2xl lg:text-3xl font-semibold text-[#161616] tracking-tight">
            See the analysis before you read the entire diff.
          </h2>
        </div>

        {/* Dashboard frame */}
        <div className="border border-[#D0D0D0] bg-white overflow-hidden">
          {/* Toolbar */}
          <div className="flex items-center gap-0 border-b border-[#D0D0D0] bg-[#F4F4F4]">
            <div className="px-4 py-2 border-r border-[#D0D0D0]">
              <span className="font-mono text-xs text-[#525252]">acme-corp/checkout-service</span>
            </div>
            <div className="px-4 py-2 border-r border-[#D0D0D0]">
              <span className="font-mono text-xs text-[#525252]">feature/payment-refactor</span>
            </div>
            <div className="px-4 py-2 border-r border-[#D0D0D0]">
              <span className="font-mono text-xs text-[#525252]">a7f3c2e</span>
            </div>
            <div className="ml-auto px-4 py-2">
              <span className="font-mono text-xs text-[#198038]">Analysis complete — 1.42s</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr_260px] divide-y lg:divide-y-0 lg:divide-x divide-[#D0D0D0]" style={{ minHeight: 340 }}>
            {/* Left — file tree */}
            <div className="bg-[#F4F4F4]">
              <div className="px-3 py-2 border-b border-[#D0D0D0]">
                <span className="text-label">Changed Files</span>
                <span className="ml-1.5 font-mono text-xs text-[#0F62FE]">7</span>
              </div>
              <div className="font-mono text-xs text-[#525252] p-3 space-y-1 leading-relaxed">
                <div className="text-[#161616]">src/</div>
                <div className="pl-3">├── services/</div>
                <div className="pl-6 flex items-center gap-1.5">
                  <span className="text-[#0F62FE] font-medium">│</span>
                  <span className="text-[#161616] bg-[#EDF4FF] px-1">payment.js</span>
                  <span className="text-[#198038] text-[10px]">+14</span>
                  <span className="text-[#DA1E28] text-[10px]">-6</span>
                </div>
                <div className="pl-3">├── controllers/</div>
                <div className="pl-6">│&nbsp;&nbsp;&nbsp;└── order.js</div>
                <div className="pl-3">└── utils/</div>
                <div className="pl-6">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── validation.js</div>
              </div>
            </div>

            {/* Center — diff viewer */}
            <div className="bg-[#161616] min-h-[200px]">
              <div className="flex items-center justify-between px-4 py-2 border-b border-[#393939] bg-[#1C1C1C]">
                <span className="font-mono text-xs text-[#A8A8A8]">src/services/payment.js</span>
                <span className="text-[10px] font-mono text-[#198038]">+14 / -6</span>
              </div>
              <div className="font-mono text-xs p-0 overflow-x-auto">
                <table className="w-full border-collapse">
                  <tbody>
                    {[
                      { type: 'header', n: null, c: '@@ -42,14 +42,18 @@ async function processPayment(order)' },
                      { type: 'ctx', n: 42, c: '  const session = await db.startTransaction();' },
                      { type: 'ctx', n: 43, c: '  try {' },
                      { type: 'del', n: 44, c: '    const result = calculateTotal();' },
                      { type: 'add', n: 44, c: '    const result = calculateTotal(items);' },
                      { type: 'ctx', n: 45, c: '    if (!result) {' },
                      { type: 'del', n: 46, c: '      return null;' },
                      { type: 'add', n: 46, c: '      throw new PaymentError("Calculation failed");' },
                      { type: 'add', n: 47, c: '    }' },
                      { type: 'add', n: 48, c: '    const charge = await stripe.charge({' },
                      { type: 'add', n: 49, c: '      amount: result.total,' },
                    ].map((row, i) => (
                      <tr
                        key={i}
                        className={
                          row.type === 'header' ? 'bg-[#252525]' :
                          row.type === 'add' ? 'bg-[#022D0D]' :
                          row.type === 'del' ? 'bg-[#2D0709]' : ''
                        }
                      >
                        <td className="w-8 text-right px-2 py-0.5 text-[#525252] select-none border-r border-[#2A2A2A]">
                          {row.n}
                        </td>
                        <td className={`px-3 py-0.5 whitespace-pre ${
                          row.type === 'add' ? 'text-[#42BE65]' :
                          row.type === 'del' ? 'text-[#FF8389]' :
                          row.type === 'header' ? 'text-[#6F6F6F]' :
                          'text-[#C6C6C6]'
                        }`}>
                          <span className="select-none opacity-50 mr-2">
                            {row.type === 'add' ? '+' : row.type === 'del' ? '-' : ' '}
                          </span>
                          {row.c}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right — analysis */}
            <div className="bg-white">
              <div className="px-3 py-2 border-b border-[#D0D0D0]">
                <span className="text-label">Analysis Summary</span>
              </div>
              <div className="p-3">
                <div className="mb-3">
                  <span className="font-mono text-xs text-[#DA1E28] font-semibold">3 Issues Detected</span>
                </div>
                <div className="space-y-2 mb-4">
                  {[
                    { n: '01', sev: 'HIGH', title: 'Potential null reference', color: '#DA1E28' },
                    { n: '02', sev: 'MEDIUM', title: 'Duplicate computation', color: '#8A6400' },
                    { n: '03', sev: 'LOW', title: 'Unnecessary abstraction', color: '#525252' },
                  ].map((issue) => (
                    <div key={issue.n} className="flex items-start gap-2.5 p-2 border border-[#E0E0E0] bg-[#F4F4F4]">
                      <span className="font-mono text-[10px] text-[#525252] mt-0.5">{issue.n}</span>
                      <div>
                        <span
                          className="font-mono text-[10px] font-semibold"
                          style={{ color: issue.color }}
                        >
                          {issue.sev}
                        </span>
                        <p className="text-[11px] text-[#161616] mt-0.5 leading-snug">{issue.title}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="border-t border-[#D0D0D0] pt-3">
                  <p className="text-[10px] font-mono text-[#0F62FE] uppercase tracking-wide mb-1.5">
                    Optimization Opportunity
                  </p>
                  <p className="text-xs text-[#525252] leading-relaxed mb-3">
                    Reduce repeated database lookup inside the loop.
                  </p>
                  <a
                    href="/results"
                    className="inline-block px-3 py-1.5 text-xs font-medium text-[#0F62FE] border border-[#0F62FE] hover:bg-[#EDF4FF] transition-colors no-underline"
                  >
                    View Recommendation
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Metrics ─────────────────────────────────────────────────────────────────

const metrics = [
  { label: 'Files Analyzed', value: '24' },
  { label: 'Issues Detected', value: '08' },
  { label: 'Optimizations', value: '12' },
  { label: 'High Priority', value: '03' },
  { label: 'Avg Analysis Time', value: '1.4s' },
];

function Metrics() {
  return (
    <section className="bg-[#161616] border-b border-[#393939] py-8">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-0 divide-x divide-[#393939]">
          {metrics.map((m) => (
            <div key={m.label} className="px-6 first:pl-0 last:pr-0 py-2">
              <div className="font-mono text-2xl font-light text-white mb-1">{m.value}</div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-[#525252]">{m.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Architecture ─────────────────────────────────────────────────────────────

const archNodes = [
  { id: 'git', label: 'Git Repository', sub: 'Source of truth', top: false },
  { id: 'diff', label: 'Diff Parser', sub: 'Extract change objects', top: false },
  { id: 'engine', label: 'Analysis Engine', sub: 'AST + Static Analysis', top: false },
  { id: 'ai', label: 'AI / Rules Engine', sub: 'LLM-assisted insights', top: false },
  { id: 'ui', label: 'CodeLens UI', sub: 'Developer interface', top: false },
];

function Architecture() {
  return (
    <section id="architecture-section" className="bg-white border-b border-[#D0D0D0] py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-10">
          <p className="text-label mb-2">System Design</p>
          <h2 className="text-2xl lg:text-3xl font-semibold text-[#161616] tracking-tight">
            Built around the developer workflow.
          </h2>
        </div>
        <div className="flex flex-col lg:flex-row items-center lg:items-stretch gap-0 max-w-4xl">
          {archNodes.map((node, i) => (
            <div key={node.id} className="flex flex-col lg:flex-row items-center">
              <div className={`border ${i === 4 ? 'border-[#0F62FE] bg-[#EDF4FF]' : 'border-[#D0D0D0] bg-white'} px-6 py-4 w-52 text-center`}>
                <div className="font-mono text-[10px] text-[#0F62FE] uppercase tracking-wide mb-1">
                  {String(i + 1).padStart(2, '0')}
                </div>
                <div className={`text-sm font-semibold ${i === 4 ? 'text-[#0F62FE]' : 'text-[#161616]'} mb-0.5`}>
                  {node.label}
                </div>
                <div className="text-xs text-[#525252]">{node.sub}</div>
              </div>
              {i < archNodes.length - 1 && (
                <div className="flex flex-col lg:flex-row items-center">
                  {/* vertical on mobile, horizontal on desktop */}
                  <div className="w-px h-6 lg:h-px lg:w-8 bg-[#D0D0D0]" />
                  <div className="w-1.5 h-1.5 bg-[#D0D0D0] rotate-45 lg:rotate-45" />
                  <div className="w-px h-2 lg:h-px lg:w-4 bg-[#D0D0D0]" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Technology ───────────────────────────────────────────────────────────────

const techStack = [
  { layer: 'Frontend', tech: 'React + TypeScript', detail: 'Vite build system' },
  { layer: 'Backend', tech: 'Python / FastAPI', detail: 'REST + WebSocket' },
  { layer: 'Code Analysis', tech: 'AST + Static Analysis', detail: 'Tree-sitter / Semgrep' },
  { layer: 'Repository', tech: 'Git / GitHub API', detail: 'Webhooks + REST' },
  { layer: 'AI Layer', tech: 'LLM-assisted Analysis', detail: 'IBM watsonx.ai' },
];

function Technology() {
  return (
    <section className="bg-[#F4F4F4] border-b border-[#D0D0D0] py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-8">
          <p className="text-label mb-2">Planned Architecture</p>
          <h2 className="text-2xl lg:text-3xl font-semibold text-[#161616] tracking-tight">
            Technology ecosystem.
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-0 divide-y md:divide-y-0 md:divide-x divide-[#D0D0D0] border border-[#D0D0D0] bg-white">
          {techStack.map((t) => (
            <div key={t.layer} className="px-5 py-4">
              <p className="text-[10px] font-mono uppercase tracking-widest text-[#525252] mb-2">{t.layer}</p>
              <p className="text-sm font-semibold text-[#161616] mb-1">{t.tech}</p>
              <p className="text-xs text-[#525252]">{t.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── CTA ──────────────────────────────────────────────────────────────────────

function CTA() {
  const navigate = useNavigate();
  return (
    <section className="bg-[#161616] py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="max-w-2xl">
          <p className="text-label text-[#525252] mb-4">Ready to start</p>
          <h2 className="text-2xl lg:text-3xl font-semibold text-white leading-tight mb-4">
            Understand every change<br />
            before it reaches production.
          </h2>
          <p className="text-sm text-[#8D8D8D] mb-8">
            Analyze your next Git diff with CodeLens.
          </p>
          <button
            onClick={() => navigate('/analyzer')}
            className="px-6 py-3 bg-[#0F62FE] text-white text-sm font-medium hover:bg-[#0353E9] transition-colors"
          >
            Open Analyzer
          </button>
        </div>
      </div>
    </section>
  );
}

// ─── Footer ───────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="bg-[#161616] border-t border-[#393939] py-8">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-8">
          <div>
            <div className="text-white font-semibold text-sm mb-1">CodeLens</div>
            <div className="text-[10px] font-mono text-[#525252] uppercase tracking-widest">
              Developer Intelligence Platform
            </div>
          </div>
          <nav className="flex flex-wrap gap-6">
            {['Product', 'Workflow', 'Architecture', 'GitHub'].map((item) => (
              <a
                key={item}
                href={item === 'Architecture' ? '/architecture' : `/#${item.toLowerCase()}`}
                className="text-xs text-[#8D8D8D] hover:text-white transition-colors no-underline"
              >
                {item}
              </a>
            ))}
          </nav>
        </div>
        <div className="border-t border-[#393939] pt-6">
          <p className="text-xs font-mono text-[#525252]">
            Built for developers. Designed for clarity.
          </p>
        </div>
      </div>
    </footer>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Landing() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <Hero />
        <Workflow />
        <Features />
        <AnalyzerPreview />
        <Metrics />
        <Architecture />
        <Technology />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
