import { useState } from 'react';
import Navbar from '../components/Navbar';
import { generateTests, type TestCase } from '../services/analysis';
import { ApiError } from '../services/api';

const CATEGORY_COLOR: Record<string, string> = {
  unit:        'bg-[#EDF4FF] text-[#0F62FE]',
  integration: 'bg-[#F4F4F4] text-[#525252]',
  security:    'bg-[#FDF6DD] text-[#8A6400]',
  edge_case:   'bg-[#FFF1F1] text-[#DA1E28]',
};

export default function Testing() {
  const [diff, setDiff] = useState('');
  const [repo, setRepo] = useState('');
  const [language, setLanguage] = useState('');
  const [framework, setFramework] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    tests: TestCase[];
    summary: string;
    disclaimer: string;
    ai_enhanced: boolean;
  } | null>(null);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const handleSubmit = async () => {
    if (!diff.trim() || !repo.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await generateTests({
        diff,
        repository: repo,
        language: language || undefined,
        framework: framework || undefined,
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
            <p className="text-label mb-1">AI-Assisted Test Generation</p>
            <h1 className="text-xl font-semibold text-[#161616]">Test Checklist</h1>
            <p className="text-xs text-[#525252] mt-1">
              Generate unit, integration, and security test cases from a diff.
              Tests are suggestions only — always review before using.
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
          <div className="bg-white border border-[#D0D0D0] p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Repository *</label>
                <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="owner/repo"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
              <div>
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Language (optional)</label>
                <input value={language} onChange={(e) => setLanguage(e.target.value)} placeholder="python, typescript…"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
              <div className="md:col-span-2">
                <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Framework (optional)</label>
                <input value={framework} onChange={(e) => setFramework(e.target.value)} placeholder="pytest, jest, go test…"
                  className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
              </div>
            </div>
            <div className="mb-4">
              <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Unified Diff *</label>
              <textarea value={diff} onChange={(e) => setDiff(e.target.value)} rows={10}
                placeholder="Paste your git diff here…"
                className="w-full border border-[#D0D0D0] px-3 py-2 text-xs font-mono focus:outline-none focus:border-[#0F62FE] resize-y bg-[#F4F4F4]" />
            </div>
            <div className="flex items-center justify-between">
              {error && <p className="text-xs text-[#DA1E28] font-mono">{error}</p>}
              <div className="ml-auto">
                <button onClick={handleSubmit} disabled={loading || !diff.trim() || !repo.trim()}
                  className="px-5 py-2 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors disabled:opacity-60 flex items-center gap-2">
                  {loading && <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>}
                  {loading ? 'Generating…' : 'Generate Tests'}
                </button>
              </div>
            </div>
          </div>

          {result && (
            <div className="space-y-4">
              {/* Disclaimer */}
              <div className="border border-[#F1C21B] bg-[#FDF6DD] px-4 py-3 flex gap-3">
                <span className="text-[#8A6400] font-mono text-xs shrink-0">⚠</span>
                <p className="text-xs text-[#8A6400]">{result.disclaimer}</p>
              </div>

              <div className="flex items-center justify-between">
                <p className="text-label">{result.tests.length} test case{result.tests.length !== 1 ? 's' : ''} generated</p>
                {result.ai_enhanced && <span className="text-[10px] font-mono bg-[#EDF4FF] text-[#0F62FE] px-2 py-0.5">AI ENHANCED</span>}
              </div>
              {result.summary && (
                <div className="bg-white border border-[#D0D0D0] p-4">
                  <p className="text-xs text-[#525252]">{result.summary}</p>
                </div>
              )}
              {result.tests.map((t, i) => (
                <div key={i} className={`bg-white border transition-colors ${expandedIdx === i ? 'border-[#0F62FE]' : 'border-[#D0D0D0]'}`}>
                  <button className="w-full text-left px-5 py-4 flex items-center justify-between bg-transparent border-none hover:bg-[#F4F4F4] transition-colors cursor-pointer"
                    onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}>
                    <div className="flex items-center gap-3 min-w-0">
                      <span className={`text-[10px] font-mono px-2 py-0.5 shrink-0 ${CATEGORY_COLOR[t.category] ?? 'bg-[#F4F4F4] text-[#525252]'}`}>
                        {t.category.toUpperCase()}
                      </span>
                      <span className="text-sm font-semibold text-[#161616] truncate">{t.name}</span>
                    </div>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"
                      className={`shrink-0 text-[#525252] transition-transform ml-3 ${expandedIdx === i ? 'rotate-180' : ''}`}>
                      <path d="M4 6L8 10L12 6" stroke="currentColor" strokeWidth="1.5" />
                    </svg>
                  </button>
                  {expandedIdx === i && (
                    <div className="px-5 pb-5 border-t border-[#E0E0E0] space-y-3 pt-4">
                      <p className="text-xs text-[#525252]">{t.description}</p>
                      <pre className="bg-[#F4F4F4] border border-[#D0D0D0] p-3 text-xs font-mono overflow-x-auto text-[#161616]">
                        {t.code}
                      </pre>
                      <p className="text-[10px] font-mono text-[#8D8D8D]">Rationale: {t.rationale}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
