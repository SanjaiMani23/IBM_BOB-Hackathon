import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { apiFetch } from '../services/api';
import { ApiError } from '../services/api';

interface MetricItem {
  metric: string;
  value:  number;
  unit:   string;
}

interface FrictionReport {
  repository:  string;
  period_days: number;
  metrics:     MetricItem[];
  recorded_at: string;
}

const METRIC_LABELS: Record<string, string> = {
  avg_time_to_merge_hours:  'Avg Time to Merge',
  p90_time_to_merge_hours:  'P90 Merge Time',
  avg_review_cycles:        'Avg Review Cycles',
  total_prs_analysed:       'PRs Analysed',
  finding_recurrence_rate:  'Finding Recurrence Rate',
};

export default function FrictionAnalytics() {
  const [repo, setRepo] = useState('');
  const [periodDays, setPeriodDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<FrictionReport | null>(null);

  const handleFetch = async () => {
    if (!repo.trim()) return;
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const data = await apiFetch<FrictionReport>('/analytics/friction', {
        params: { repository: repo, period_days: periodDays },
      });
      setReport(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (m: MetricItem): string => {
    if (m.unit === 'ratio') return `${(m.value * 100).toFixed(1)}%`;
    if (m.unit === 'count') return String(Math.round(m.value));
    if (m.unit === 'hours') {
      if (m.value >= 24) return `${(m.value / 24).toFixed(1)}d`;
      return `${m.value.toFixed(1)}h`;
    }
    return `${m.value.toFixed(2)} ${m.unit}`;
  };

  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-6">
          <div className="max-w-4xl mx-auto">
            <p className="text-label mb-1">Developer Experience</p>
            <h1 className="text-xl font-semibold text-[#161616]">Friction Analytics</h1>
            <p className="text-xs text-[#525252] mt-1">
              Measure what slows your team down — merge times, review cycles, and recurring findings.
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
          <div className="bg-white border border-[#D0D0D0] p-5 flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-40">
              <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Repository *</label>
              <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="owner/repo"
                className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
            </div>
            <div>
              <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Period (days)</label>
              <input type="number" min={1} max={365} value={periodDays} onChange={(e) => setPeriodDays(Number(e.target.value))}
                className="border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE] w-24" />
            </div>
            <button onClick={handleFetch} disabled={loading || !repo.trim()}
              className="px-4 py-1.5 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors disabled:opacity-60">
              {loading ? 'Loading…' : 'Load Metrics'}
            </button>
            {error && <p className="text-xs text-[#DA1E28] font-mono w-full">{error}</p>}
          </div>

          {report && (
            <>
              <div className="flex items-center justify-between">
                <p className="text-label">{report.repository}</p>
                <span className="font-mono text-xs text-[#525252]">Last {report.period_days} days</span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {report.metrics.map((m) => (
                  <div key={m.metric} className="bg-white border border-[#D0D0D0] p-5">
                    <div className="font-mono text-2xl font-light text-[#0F62FE] mb-1">{formatValue(m)}</div>
                    <div className="text-[10px] font-mono uppercase tracking-widest text-[#525252]">
                      {METRIC_LABELS[m.metric] ?? m.metric.replace(/_/g, ' ')}
                    </div>
                  </div>
                ))}
              </div>

              <div className="bg-white border border-[#D0D0D0] p-4">
                <p className="text-[10px] font-mono text-[#8D8D8D]">
                  Metrics recorded up to {new Date(report.recorded_at).toLocaleString()}
                </p>
              </div>
            </>
          )}

          {!report && !loading && (
            <div className="bg-white border border-[#D0D0D0] p-10 text-center">
              <p className="text-xs text-[#525252]">Enter a repository and load metrics to see friction data.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
