import { useState } from 'react';
import Navbar from '../components/Navbar';
import SeverityBadge from '../components/SeverityBadge';
import { debugCode, type DebugIssue } from '../services/analysis';
import { ApiError } from '../services/api';

export default function Debugging() {
  const [diff, setDiff] = useState('');
  const [repo, setRepo] = useState('');
  const [language, setLanguage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ issues: DebugIssue[]; summary: string; ai_enhanced: boolean } | null>(null);

  const handleSubmit = async () => {
    if (!diff.trim() || !repo.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await debugCode({ diff, repository: repo, language: language || undefined });
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
            <p className="text-label mb-1">Static Analysis + watsonx.ai</p>
            <h1 className="text-xl font-semibold text-[#161616]">Code Debugging</h1>
            <p className="text-xs text-[#525252] mt-1">Paste a unified diff to identify bugs, logic errors, and security issues.</p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
          {/* Input form */}
          <div className="bg-white border border-[#D0D0D0] p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">
                  Repository *
                </label>
                <input
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  placeholder="owner/repo"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]"
                />
              </div>
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">
                  Language (optional)
                </label>
                <input
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  placeholder="python, javascript, go…"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]"
                />
              </div>
            </div>
            <div className="mb-4">
              <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">
                Unified Diff *
              </label>
              <textarea
                value={diff}
                onChange={(e) => setDiff(e.target.value)}
                rows={12}
                placeholder="Paste your git diff here…"
                className="w-full border border-[#D0D0D0] px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#0F62FE] resize-y bg-[#F4F4F4]"
              />
            </div>
            <div className="flex items-center justify-between">
              {error && <p className="text-xs text-[#DA1E28] font-mono">{error}</p>}
              <div className="ml-auto">
                <button
                  onClick={handleSubmit}
                  disabled={loading || !diff.trim() || !repo.trim()}
                  className="px-5 py-2 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors disabled:opacity-60 flex items-center gap-2"
                >
                  {loading && (
                    <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                  )}
                  {loading ? 'Analysing…' : 'Debug Code'}
                </button>
              </div>
            </div>
          </div>

          {/* Results */}
          {result && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-label">
                  {result.issues.length} issue{result.issues.length !== 1 ? 's' : ''} found
                </p>
                {result.ai_enhanced && (
                  <span className="text-[10px] font-mono bg-[#EDF4FF] text-[#0F62FE] px-2 py-0.5">
                    AI ENHANCED
                  </span>
                )}
              </div>
              {result.summary && (
                <div className="bg-white border border-[#D0D0D0] p-4">
                  <p className="text-xs text-[#525252]">{result.summary}</p>
                </div>
              )}
              {result.issues.map((issue, i) => (
                <div key={i} className="bg-white border border-[#D0D0D0] p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <SeverityBadge severity={issue.severity} />
                    {issue.line_number && (
                      <span className="font-mono text-xs text-[#525252]">Line {issue.line_number}</span>
                    )}
                    <span className="font-mono text-[10px] text-[#525252] bg-[#F4F4F4] px-2 py-0.5">
                      {issue.confidence}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-[#161616] mb-2">{issue.title}</p>
                  <p className="text-xs text-[#525252] leading-relaxed mb-3">{issue.explanation}</p>
                  <div className="border-l-2 border-[#0F62FE] pl-3">
                    <p className="text-[10px] font-mono text-[#0F62FE] uppercase tracking-wide mb-1">Recommendation</p>
                    <p className="text-xs text-[#161616] leading-relaxed">{issue.recommendation}</p>
                  </div>
                </div>
              ))}
              {result.issues.length === 0 && (
                <div className="bg-white border border-[#D0D0D0] p-8 text-center">
                  <p className="text-sm text-[#198038] font-semibold">No issues detected.</p>
                  <p className="text-xs text-[#525252] mt-1">The diff looks clean.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
