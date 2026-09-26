import { useState } from 'react';
import type { Finding } from '../data/mockAnalysis';
import SeverityBadge from './SeverityBadge';

interface Props {
  findings: Finding[];
}

export default function FindingsPanel({ findings }: Props) {
  const [expanded, setExpanded] = useState<string | null>(findings[0]?.id ?? null);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="px-3 py-2 border-b border-[#D0D0D0] shrink-0">
        <span className="text-label">Analysis Findings</span>
        <span className="ml-2 font-mono text-xs text-[#DA1E28]">{findings.length}</span>
      </div>
      <div className="flex-1 overflow-y-auto divide-y divide-[#E0E0E0]">
        {findings.map((f) => {
          const isOpen = expanded === f.id;
          return (
            <div key={f.id} className="bg-white">
              <button
                className="w-full text-left px-3 py-2.5 flex items-start gap-2 hover:bg-[#F4F4F4] transition-colors cursor-pointer border-none bg-transparent"
                onClick={() => setExpanded(isOpen ? null : f.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <SeverityBadge severity={f.severity} size="sm" />
                    <span className="font-mono text-[10px] text-[#525252]">{f.file.split('/').pop()}:{f.line}</span>
                  </div>
                  <p className="text-xs font-medium text-[#161616] leading-snug">{f.title}</p>
                </div>
                <svg
                  width="14" height="14" viewBox="0 0 14 14" fill="none"
                  className={`shrink-0 mt-0.5 text-[#525252] transition-transform ${isOpen ? 'rotate-180' : ''}`}
                >
                  <path d="M3 5L7 9L11 5" stroke="currentColor" strokeWidth="1.5" />
                </svg>
              </button>
              {isOpen && (
                <div className="px-3 pb-3 border-t border-[#E0E0E0] bg-[#F4F4F4]">
                  <p className="text-xs text-[#525252] leading-relaxed mt-2 mb-3">{f.explanation}</p>
                  <div className="border-l-2 border-[#0F62FE] pl-2">
                    <p className="text-[10px] font-mono text-[#0F62FE] uppercase tracking-wide mb-1">Recommendation</p>
                    <p className="text-xs text-[#161616] leading-relaxed">{f.recommendation}</p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
