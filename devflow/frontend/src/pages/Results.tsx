import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import SeverityBadge from '../components/SeverityBadge';
import { mockFindings, mockSummary, type Severity } from '../data/mockAnalysis';

type Filter = 'all' | Severity;

const filterOptions: { id: Filter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'critical', label: 'Critical' },
  { id: 'high', label: 'High' },
  { id: 'medium', label: 'Medium' },
  { id: 'low', label: 'Low' },
];

const typeColors: Record<string, string> = {
  bug: 'text-[#DA1E28] bg-[#FFF1F1]',
  optimization: 'text-[#0F62FE] bg-[#EDF4FF]',
  security: 'text-[#8A6400] bg-[#FDF6DD]',
  structure: 'text-[#525252] bg-[#F4F4F4]',
};

export default function Results() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<Filter>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = filter === 'all'
    ? mockFindings
    : mockFindings.filter((f) => f.severity === filter);

  const counts = {
    critical: mockFindings.filter((f) => f.severity === 'critical').length,
    high: mockFindings.filter((f) => f.severity === 'high').length,
    medium: mockFindings.filter((f) => f.severity === 'medium').length,
    low: mockFindings.filter((f) => f.severity === 'low').length,
  };

  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        {/* Page header */}
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-6">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div>
                <p className="text-label mb-1">Analysis Report</p>
                <h1 className="text-xl font-semibold text-[#161616]">Results Dashboard</h1>
                <p className="font-mono text-xs text-[#525252] mt-1">
                  {mockSummary.repository} / {mockSummary.branch} / {mockSummary.commit}
                </p>
              </div>
              <button
                onClick={() => navigate('/analyzer')}
                className="px-4 py-2 border border-[#D0D0D0] text-xs text-[#161616] hover:border-[#161616] transition-colors bg-white"
              >
                Back to Analyzer
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-6 py-8">
          {/* Summary strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-0 border border-[#D0D0D0] bg-white mb-6">
            {[
              { label: 'Files Analyzed', value: mockSummary.filesAnalyzed, color: 'text-[#161616]' },
              { label: 'Issues Detected', value: mockSummary.issuesDetected, color: 'text-[#DA1E28]' },
              { label: 'Optimizations', value: mockSummary.optimizations, color: 'text-[#0F62FE]' },
              { label: 'High Priority', value: mockSummary.highPriority, color: 'text-[#DA1E28]' },
            ].map((s, i) => (
              <div
                key={s.label}
                className={`px-6 py-4 ${i < 3 ? 'border-b md:border-b-0 md:border-r border-[#D0D0D0]' : ''}`}
              >
                <div className={`font-mono text-3xl font-light mb-1 ${s.color}`}>
                  {String(s.value).padStart(2, '0')}
                </div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-[#525252]">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Severity breakdown */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            {[
              { sev: 'critical' as Severity, count: counts.critical },
              { sev: 'high' as Severity, count: counts.high },
              { sev: 'medium' as Severity, count: counts.medium },
              { sev: 'low' as Severity, count: counts.low },
            ].map(({ sev, count }) => (
              <button
                key={sev}
                onClick={() => setFilter(filter === sev ? 'all' : sev)}
                className={`border p-3 text-left transition-colors cursor-pointer bg-white ${
                  filter === sev
                    ? 'border-[#0F62FE]'
                    : 'border-[#D0D0D0] hover:border-[#8D8D8D]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <SeverityBadge severity={sev} size="sm" />
                  <span className="font-mono text-lg font-light text-[#161616]">{count}</span>
                </div>
              </button>
            ))}
          </div>

          {/* Filter bar */}
          <div className="flex items-center gap-0 border border-[#D0D0D0] bg-white mb-4 w-fit">
            {filterOptions.map((opt) => (
              <button
                key={opt.id}
                onClick={() => setFilter(opt.id)}
                className={`px-4 py-2 text-xs font-medium border-r last:border-r-0 border-[#D0D0D0] transition-colors cursor-pointer ${
                  filter === opt.id
                    ? 'bg-[#0F62FE] text-white'
                    : 'bg-white text-[#525252] hover:text-[#161616]'
                }`}
              >
                {opt.label}
                {opt.id !== 'all' && (
                  <span className={`ml-1.5 font-mono text-[10px] ${filter === opt.id ? 'text-blue-200' : 'text-[#8D8D8D]'}`}>
                    {counts[opt.id as Severity]}
                  </span>
                )}
              </button>
            ))}
            <span className="px-4 text-xs text-[#525252] border-l border-[#D0D0D0] py-2">
              {filtered.length} result{filtered.length !== 1 ? 's' : ''}
            </span>
          </div>

          {/* Findings list */}
          <div className="space-y-2">
            {filtered.map((f) => {
              const isOpen = expandedId === f.id;
              return (
                <div
                  key={f.id}
                  className={`border bg-white transition-colors ${
                    isOpen ? 'border-[#0F62FE]' : 'border-[#D0D0D0]'
                  }`}
                >
                  <button
                    className="w-full text-left px-5 py-4 flex items-start gap-4 hover:bg-[#F4F4F4] transition-colors cursor-pointer bg-transparent border-none"
                    onClick={() => setExpandedId(isOpen ? null : f.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1.5 flex-wrap">
                        <SeverityBadge severity={f.severity} />
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 ${typeColors[f.type]}`}>
                          {f.type.toUpperCase()}
                        </span>
                        <span className="font-mono text-xs text-[#525252]">
                          {f.file} : {f.line}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-[#161616]">{f.title}</p>
                    </div>
                    <svg
                      width="16" height="16" viewBox="0 0 16 16" fill="none"
                      className={`shrink-0 text-[#525252] transition-transform mt-0.5 ${isOpen ? 'rotate-180' : ''}`}
                    >
                      <path d="M4 6L8 10L12 6" stroke="currentColor" strokeWidth="1.5" />
                    </svg>
                  </button>

                  {isOpen && (
                    <div className="px-5 pb-5 border-t border-[#E0E0E0]">
                      <div className="grid md:grid-cols-2 gap-6 pt-4">
                        <div>
                          <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-2">
                            Explanation
                          </p>
                          <p className="text-sm text-[#161616] leading-relaxed">{f.explanation}</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-mono text-[#0F62FE] uppercase tracking-wide mb-2">
                            Recommendation
                          </p>
                          <div className="border-l-2 border-[#0F62FE] pl-3">
                            <p className="text-sm text-[#161616] leading-relaxed">{f.recommendation}</p>
                          </div>
                          <div className="mt-4 flex items-center gap-2 font-mono text-xs text-[#525252]">
                            <span>File:</span>
                            <span className="text-[#161616] bg-[#F4F4F4] px-2 py-0.5">{f.file}</span>
                            <span>Line {f.line}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {filtered.length === 0 && (
            <div className="text-center py-16 border border-[#D0D0D0] bg-white">
              <p className="text-sm text-[#525252]">No findings for the selected severity filter.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
