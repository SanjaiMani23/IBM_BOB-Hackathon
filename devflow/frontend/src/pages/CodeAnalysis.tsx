import { useState } from 'react';
import Navbar from '../components/Navbar';
import { generatePrDescription, type PrDescriptionResponse } from '../services/analysis';
import { ApiError } from '../services/api';

export default function CodeAnalysis() {
  const [diff, setDiff] = useState('');
  const [repo, setRepo] = useState('');
  const [prNumber, setPrNumber] = useState('');
  const [branch, setBranch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PrDescriptionResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async () => {
    if (!repo.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await generatePrDescription({
        diff: diff || undefined,
        repository: repo,
        pr_number: prNumber ? Number(prNumber) : undefined,
        branch: branch || undefined,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Unexpected error');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result) return;
    const md = [
      `## ${result.title}`,
      '',
      result.summary,
      '',
      `### Motivation`,
      result.motivation,
      '',
      `### Changes`,
      ...result.changes.map((c) => `- ${c}`),
      '',
      `### Testing`,
      result.testing_notes,
      result.breaking_changes ? `\n### Breaking Changes\n${result.breaking_changes}` : '',
      '',
      `### Reviewer Checklist`,
      ...result.reviewer_checklist.map((c) => `- [ ] ${c}`),
    ].join('\n');
    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-6">
          <div className="max-w-4xl mx-auto">
            <p className="text-label mb-1">AI-Generated PR Description</p>
            <h1 className="text-xl font-semibold text-[#161616]">PR Description Generator</h1>
            <p className="text-xs text-[#525252] mt-1">
              Provide a diff or a PR number to generate a structured pull request description.
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
          <div className="bg-white border border-[#D0D0D0] p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Repository *</label>
                <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="owner/repo"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">PR Number (optional)</label>
                <input value={prNumber} onChange={(e) => setPrNumber(e.target.value)} placeholder="42"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Branch (optional)</label>
                <input value={branch} onChange={(e) => setBranch(e.target.value)} placeholder="feature/my-branch"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
            </div>
            <div className="mb-4">
              <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">
                Diff (optional if PR number provided)
              </label>
              <textarea value={diff} onChange={(e) => setDiff(e.target.value)} rows={8}
                placeholder="Paste your git diff here, or supply a PR number above…"
                className="w-full border border-[#D0D0D0] px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#0F62FE] resize-y bg-[#F4F4F4]" />
            </div>
            <div className="flex items-center justify-between">
              {error && <p className="text-xs text-[#DA1E28] font-mono">{error}</p>}
              <div className="ml-auto">
                <button onClick={handleSubmit} disabled={loading || !repo.trim()}
                  className="px-5 py-2 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors disabled:opacity-60 flex items-center gap-2">
                  {loading && <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>}
                  {loading ? 'Generating…' : 'Generate Description'}
                </button>
              </div>
            </div>
          </div>

          {result && (
            <div className="bg-white border border-[#D0D0D0]">
              <div className="px-6 py-4 border-b border-[#D0D0D0] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <p className="text-sm font-semibold text-[#161616]">PR Description</p>
                  {result.ai_enhanced && (
                    <span className="text-[10px] font-mono bg-[#EDF4FF] text-[#0F62FE] px-2 py-0.5">AI ENHANCED</span>
                  )}
                </div>
                <button onClick={handleCopy}
                  className="px-3 py-1 border border-[#D0D0D0] text-xs text-[#161616] hover:border-[#161616] transition-colors bg-white">
                  {copied ? 'Copied!' : 'Copy Markdown'}
                </button>
              </div>
              <div className="p-6 space-y-5">
                <div>
                  <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-1">Title</p>
                  <p className="text-base font-semibold text-[#161616]">{result.title}</p>
                </div>
                <div>
                  <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-1">Summary</p>
                  <p className="text-sm text-[#161616] leading-relaxed">{result.summary}</p>
                </div>
                <div>
                  <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-1">Motivation</p>
                  <p className="text-sm text-[#161616] leading-relaxed">{result.motivation}</p>
                </div>
                {result.changes.length > 0 && (
                  <div>
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-2">Changes</p>
                    <ul className="space-y-1">
                      {result.changes.map((c, i) => (
                        <li key={i} className="text-sm text-[#161616] flex gap-2">
                          <span className="text-[#0F62FE] shrink-0">•</span>{c}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div>
                  <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-1">Testing Notes</p>
                  <p className="text-sm text-[#161616] leading-relaxed">{result.testing_notes}</p>
                </div>
                {result.breaking_changes && (
                  <div className="border border-[#DA1E28] bg-[#FFF1F1] p-4">
                    <p className="text-[10px] font-mono text-[#DA1E28] uppercase tracking-wide mb-1">Breaking Changes</p>
                    <p className="text-sm text-[#DA1E28]">{result.breaking_changes}</p>
                  </div>
                )}
                {result.reviewer_checklist.length > 0 && (
                  <div>
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-2">Reviewer Checklist</p>
                    <ul className="space-y-1">
                      {result.reviewer_checklist.map((c, i) => (
                        <li key={i} className="text-sm text-[#161616] flex gap-2">
                          <span className="text-[#8D8D8D] shrink-0">☐</span>{c}
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
