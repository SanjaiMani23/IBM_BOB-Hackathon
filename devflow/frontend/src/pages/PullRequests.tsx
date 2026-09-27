import { useState } from 'react';
import Navbar from '../components/Navbar';
import { listPullRequests, getPullRequestDiff, type GithubPullRequest } from '../services/github';
import { ApiError } from '../services/api';

export default function PullRequests() {
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');
  const [state, setState] = useState<'open' | 'closed' | 'all'>('open');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prs, setPrs] = useState<GithubPullRequest[]>([]);
  const [selectedPr, setSelectedPr] = useState<GithubPullRequest | null>(null);
  const [diff, setDiff] = useState<string | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);

  const handleFetch = async () => {
    if (!owner.trim() || !repo.trim()) return;
    setLoading(true);
    setError(null);
    setPrs([]);
    setSelectedPr(null);
    setDiff(null);
    try {
      const list = await listPullRequests(owner, repo, state);
      setPrs(list);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to fetch pull requests');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPr = async (pr: GithubPullRequest) => {
    setSelectedPr(pr);
    setDiff(null);
    setDiffLoading(true);
    try {
      const d = await getPullRequestDiff(owner, repo, pr.number);
      setDiff(d);
    } catch {
      setDiff(null);
    } finally {
      setDiffLoading(false);
    }
  };

  const STATE_COLOR: Record<string, string> = {
    open:   'text-[#198038] bg-[#DEFBE6]',
    closed: 'text-[#525252] bg-[#F4F4F4]',
    merged: 'text-[#8A3FFC] bg-[#F6F2FF]',
  };

  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-6">
          <div className="max-w-5xl mx-auto">
            <p className="text-label mb-1">GitHub Integration</p>
            <h1 className="text-xl font-semibold text-[#161616]">Pull Requests</h1>
            <p className="text-xs text-[#525252] mt-1">Browse and inspect pull requests from any connected repository.</p>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
          {/* Search bar */}
          <div className="bg-white border border-[#D0D0D0] p-5 flex flex-wrap items-end gap-4">
            <div>
              <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Owner *</label>
              <input value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="acme-corp"
                className="border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE] w-36" />
            </div>
            <div>
              <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Repo *</label>
              <input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="checkout-service"
                className="border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE] w-44" />
            </div>
            <div>
              <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">State</label>
              <select value={state} onChange={(e) => setState(e.target.value as 'open' | 'closed' | 'all')}
                className="border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE] bg-white w-24">
                <option value="open">Open</option>
                <option value="closed">Closed</option>
                <option value="all">All</option>
              </select>
            </div>
            <button onClick={handleFetch} disabled={loading || !owner.trim() || !repo.trim()}
              className="px-4 py-1.5 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors disabled:opacity-60">
              {loading ? 'Loading…' : 'Fetch PRs'}
            </button>
            {error && <p className="text-xs text-[#DA1E28] font-mono w-full">{error}</p>}
          </div>

          {/* PR list + diff preview */}
          {prs.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-[320px_1fr] gap-4">
              <div className="space-y-2">
                {prs.map((pr) => (
                  <button key={pr.number} onClick={() => handleSelectPr(pr)}
                    className={`w-full text-left bg-white border p-4 transition-colors cursor-pointer ${selectedPr?.number === pr.number ? 'border-[#0F62FE]' : 'border-[#D0D0D0] hover:border-[#8D8D8D]'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-[#8D8D8D]">#{pr.number}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 ${STATE_COLOR[pr.state] ?? STATE_COLOR.closed}`}>
                        {pr.state.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-[#161616] leading-snug">{pr.title}</p>
                    <p className="font-mono text-[10px] text-[#525252] mt-1">
                      {pr.head_branch} → {pr.base_branch}
                    </p>
                    <p className="font-mono text-[10px] text-[#8D8D8D]">{new Date(pr.created_at).toLocaleDateString()}</p>
                  </button>
                ))}
              </div>
              <div className="bg-white border border-[#D0D0D0] overflow-hidden">
                {selectedPr ? (
                  <>
                    <div className="px-4 py-3 border-b border-[#D0D0D0] flex items-center justify-between">
                      <span className="font-mono text-xs text-[#161616]">PR #{selectedPr.number} — diff</span>
                      <a href={`/analyzer?repo=${owner}/${repo}&pr=${selectedPr.number}`}
                        className="text-xs text-[#0F62FE] hover:underline">Analyse this PR →</a>
                    </div>
                    {diffLoading ? (
                      <div className="flex items-center justify-center py-16">
                        <p className="font-mono text-xs text-[#525252] animate-pulse">Loading diff…</p>
                      </div>
                    ) : diff ? (
                      <pre className="p-4 text-xs font-mono overflow-auto text-[#161616] max-h-[60vh] bg-[#F4F4F4]">{diff}</pre>
                    ) : (
                      <div className="flex items-center justify-center py-16">
                        <p className="font-mono text-xs text-[#525252]">Diff unavailable</p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="flex items-center justify-center py-16">
                    <p className="font-mono text-xs text-[#525252]">Select a pull request to preview its diff.</p>
                  </div>
                )}
              </div>
            </div>
          )}
          {!loading && prs.length === 0 && (
            <div className="bg-white border border-[#D0D0D0] p-10 text-center">
              <p className="text-xs text-[#525252]">Enter a repository owner and name, then click Fetch PRs.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
