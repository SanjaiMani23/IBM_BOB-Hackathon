import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import FileExplorer from '../components/FileExplorer';
import DiffViewer from '../components/DiffViewer';
import FindingsPanel from '../components/FindingsPanel';
import SeverityBadge from '../components/SeverityBadge';
import {
  mockChangedFiles,
  mockDiffLines,
  mockFindings,
  mockSummary,
} from '../data/mockAnalysis';

type Tab = 'diff' | 'analysis' | 'optimization';

export default function Analyzer() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(mockChangedFiles[0].path);
  const [repo, setRepo] = useState('acme-corp/checkout-service');
  const [branch, setBranch] = useState('feature/payment-refactor');
  const [commit, setCommit] = useState('a7f3c2e');
  const [analyzed, setAnalyzed] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('diff');
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalyze = () => {
    setAnalyzing(true);
    setTimeout(() => {
      setAnalyzed(true);
      setAnalyzing(false);
    }, 1400);
  };

  const fileFindigs = mockFindings.filter((f) => f.file === selectedFile);
  const allFindings = mockFindings;

  return (
    <div className="min-h-screen bg-[#F4F4F4] flex flex-col">
      <Navbar />

      {/* Header bar */}
      <div className="pt-12 bg-white border-b border-[#D0D0D0] shrink-0">
        <div className="max-w-full px-6 py-3 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-base font-semibold text-[#161616]">CodeLens Analyzer</h1>
            <p className="text-xs text-[#525252] font-mono">Interactive code analysis workspace</p>
          </div>
          {analyzed && (
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="text-[#525252]">
                Analyzed <span className="text-[#198038] font-semibold">{mockSummary.filesAnalyzed} files</span>
              </span>
              <span className="text-[#DA1E28] font-semibold">{mockSummary.issuesDetected} issues</span>
              <span className="text-[#525252]">{mockSummary.analysisTime}</span>
              <button
                onClick={() => navigate('/results')}
                className="px-3 py-1 bg-[#0F62FE] text-white hover:bg-[#0353E9] transition-colors"
              >
                View Full Report
              </button>
            </div>
          )}
        </div>

        {/* Repository controls */}
        <div className="px-6 py-3 border-t border-[#D0D0D0] flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide">Repository</label>
            <input
              type="text"
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              className="border border-[#D0D0D0] bg-white px-2 py-1 text-xs font-mono text-[#161616] w-52 focus:outline-none focus:border-[#0F62FE]"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide">Branch</label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              className="border border-[#D0D0D0] bg-white px-2 py-1 text-xs font-mono text-[#161616] w-44 focus:outline-none focus:border-[#0F62FE]"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide">Commit</label>
            <input
              type="text"
              value={commit}
              onChange={(e) => setCommit(e.target.value)}
              className="border border-[#D0D0D0] bg-white px-2 py-1 text-xs font-mono text-[#161616] w-28 focus:outline-none focus:border-[#0F62FE]"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="px-4 py-1.5 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors disabled:opacity-60 flex items-center gap-2"
          >
            {analyzing && (
              <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
            )}
            {analyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </div>

      {/* Main workspace */}
      <div
        className="flex-1 grid grid-cols-1 lg:grid-cols-[220px_1fr_280px] overflow-hidden"
        style={{ height: 'calc(100vh - 160px)' }}
      >
        {/* Left — file explorer */}
        <div className="border-r border-[#D0D0D0] bg-[#F4F4F4] overflow-hidden flex flex-col">
          <FileExplorer
            files={mockChangedFiles}
            selected={selectedFile}
            onSelect={setSelectedFile}
          />
        </div>

        {/* Center — diff / analysis tabs */}
        <div className="flex flex-col overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b border-[#D0D0D0] bg-white shrink-0">
            {[
              { id: 'diff' as Tab, label: 'Diff View' },
              { id: 'analysis' as Tab, label: 'Analysis' },
              { id: 'optimization' as Tab, label: 'Optimization' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors cursor-pointer border-none ${
                  activeTab === tab.id
                    ? 'border-b-[#0F62FE] text-[#0F62FE] bg-white'
                    : 'border-b-transparent text-[#525252] hover:text-[#161616] bg-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'diff' && (
              <DiffViewer lines={mockDiffLines} filename={selectedFile} />
            )}

            {activeTab === 'analysis' && (
              <div className="h-full overflow-y-auto bg-white p-5">
                <div className="mb-4">
                  <p className="text-label mb-1">File Analysis</p>
                  <p className="font-mono text-xs text-[#525252]">{selectedFile}</p>
                </div>
                {fileFindigs.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="w-8 h-8 border border-[#198038] flex items-center justify-center mx-auto mb-3">
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M3 8L6.5 11.5L13 5" stroke="#198038" strokeWidth="1.5"/>
                      </svg>
                    </div>
                    <p className="text-sm text-[#525252]">No issues detected in this file.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {fileFindigs.map((f) => (
                      <div key={f.id} className="border border-[#D0D0D0] p-4 bg-[#F4F4F4]">
                        <div className="flex items-center gap-2 mb-2">
                          <SeverityBadge severity={f.severity} />
                          <span className="font-mono text-xs text-[#525252]">Line {f.line}</span>
                        </div>
                        <p className="text-sm font-semibold text-[#161616] mb-2">{f.title}</p>
                        <p className="text-xs text-[#525252] leading-relaxed mb-3">{f.explanation}</p>
                        <div className="border-l-2 border-[#0F62FE] pl-3">
                          <p className="text-[10px] font-mono text-[#0F62FE] uppercase tracking-wide mb-1">
                            Recommendation
                          </p>
                          <p className="text-xs text-[#161616] leading-relaxed">{f.recommendation}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'optimization' && (
              <div className="h-full overflow-y-auto bg-white p-5">
                <div className="mb-4">
                  <p className="text-label mb-1">Optimization Suggestions</p>
                  <p className="text-xs text-[#525252]">Performance and structural improvements identified in the diff.</p>
                </div>
                <div className="space-y-3">
                  {allFindings.filter(f => f.type === 'optimization').map((f) => (
                    <div key={f.id} className="border border-[#D0D0D0] p-4 bg-[#F4F4F4]">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-[10px] font-mono bg-[#EDF4FF] text-[#0F62FE] px-2 py-0.5">
                          OPTIMIZATION
                        </span>
                        <span className="font-mono text-xs text-[#525252]">{f.file.split('/').pop()}:{f.line}</span>
                      </div>
                      <p className="text-sm font-semibold text-[#161616] mb-2">{f.title}</p>
                      <p className="text-xs text-[#525252] leading-relaxed mb-3">{f.explanation}</p>
                      <div className="border-l-2 border-[#0F62FE] pl-3">
                        <p className="text-[10px] font-mono text-[#0F62FE] uppercase tracking-wide mb-1">
                          Recommended Fix
                        </p>
                        <p className="text-xs text-[#161616] leading-relaxed">{f.recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right — findings panel */}
        <div className="border-l border-[#D0D0D0] overflow-hidden flex flex-col">
          <FindingsPanel findings={allFindings} />
        </div>
      </div>
    </div>
  );
}
