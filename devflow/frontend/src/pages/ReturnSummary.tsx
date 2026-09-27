import { useState } from 'react';
import Navbar from '../components/Navbar';
import { generateReturnSummary, type ReturnSummaryResponse } from '../services/analysis';
import { ApiError } from '../services/api';

export default function ReturnSummary() {
  const [repo, setRepo] = useState('');
  const [branch, setBranch] = useState('');
  const [sinceDays, setSinceDays] = useState(7);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReturnSummaryResponse | null>(null);

  const handleSubmit = async () => {
    if (!repo.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await generateReturnSummary({
        repository: repo,
        branch: branch || undefined,
        since_days: sinceDays,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Unexpected error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-6">
          <div className="max-w-4xl mx-auto">
            <p className="text-label mb-1">AI-Assisted Context Recovery</p>
            <h1 className="text-xl font-semibold text-[#161616]">Return Summary</h1>
            <p className="text-xs text-[#525252] mt-1">
              Catch up on what changed while you were away — commits, open PRs, key findings, and next steps.
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
          <div className="bg-white border border-[#D0D0D0] p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="md:col-span-1">
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Repository *</label>
                <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="owner/repo"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Branch (optional)</label>
                <input value={branch} onChange={(e) => setBranch(e.target.value)} placeholder="main"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Look-back days</label>
                <input type="number" min={1} max={90} value={sinceDays} onChange={(e) => setSinceDays(Number(e.target.value))}
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              {error && <p className="text-xs text-[#DA1E28] font-mono">{error}</p>}
              <div className="ml-auto">
                <button onClick={handleSubmit} disabled={loading || !repo.trim()}
                  className="px-5 py-2 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors disabled:opacity-60 flex items-center gap-2">
                  {loading && <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>}
                  {loading ? 'Generating…' : 'Generate Summary'}
                </button>
              </div>
            </div>
          </div>

          {result && (
            <div className="space-y-5">
              {result.ai_enhanced && (
                <div className="flex justify-end">
                  <span className="text-[10px] font-mono bg-[#EDF4FF] text-[#0F62FE] px-2 py-0.5">AI ENHANCED</span>
                </div>
              )}

              {/* Briefing */}
              <div className="bg-white border border-[#D0D0D0] p-5">
                <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-2">Briefing</p>
                <p className="text-sm text-[#161616] leading-relaxed">{result.briefing}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Recent commits */}
                {result.recent_commits.length > 0 && (
                  <div className="bg-white border border-[#D0D0D0] p-5">
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-3">Recent Commits</p>
                    <ul className="space-y-1.5">
                      {result.recent_commits.map((c, i) => (
                        <li key={i} className="flex gap-2 text-xs">
                          <span className="text-[#0F62FE] font-mono shrink-0">›</span>
                          <span className="text-[#161616]">{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Open PRs */}
                {result.open_prs.length > 0 && (
                  <div className="bg-white border border-[#D0D0D0] p-5">
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-3">Open Pull Requests</p>
                    <ul className="space-y-1.5">
                      {result.open_prs.map((pr, i) => (
                        <li key={i} className="flex gap-2 text-xs">
                          <span className="text-[#198038] font-mono shrink-0">›</span>
                          <span className="text-[#161616]">{pr}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Key findings */}
                {result.key_findings.length > 0 && (
                  <div className="bg-white border border-[#D0D0D0] p-5">
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-3">Key Findings</p>
                    <ul className="space-y-1.5">
                      {result.key_findings.map((f, i) => (
                        <li key={i} className="flex gap-2 text-xs">
                          <span className="text-[#DA1E28] font-mono shrink-0">›</span>
                          <span className="text-[#161616]">{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommended actions */}
                {result.recommended_actions.length > 0 && (
                  <div className="bg-white border border-[#D0D0D0] p-5">
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-3">Recommended Actions</p>
                    <ul className="space-y-1.5">
                      {result.recommended_actions.map((a, i) => (
                        <li key={i} className="flex gap-2 text-xs">
                          <span className="text-[#8A6400] font-mono shrink-0">{i + 1}.</span>
                          <span className="text-[#161616]">{a}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
