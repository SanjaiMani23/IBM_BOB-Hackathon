import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { getMe, type UserResponse } from '../services/api';
import { ApiError } from '../services/api';

interface StatCard {
  label: string;
  value: string | number;
  sub:   string;
  color: string;
}

export default function Dashboard() {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          window.location.href = '/';
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const stats: StatCard[] = [
    { label: 'Analyses Run', value: '—', sub: 'last 30 days', color: 'text-[#0F62FE]' },
    { label: 'Findings Detected', value: '—', sub: 'total open', color: 'text-[#DA1E28]' },
    { label: 'Avg Merge Time', value: '—', sub: 'hours', color: 'text-[#161616]' },
    { label: 'Jira Tickets', value: '—', sub: 'created this month', color: 'text-[#198038]' },
  ];

  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-6">
          <div className="max-w-5xl mx-auto">
            <p className="text-label mb-1">DevFlow CodeLens</p>
            <h1 className="text-xl font-semibold text-[#161616]">Dashboard</h1>
            {user && (
              <p className="font-mono text-xs text-[#525252] mt-1">
                Welcome back, {user.full_name ?? user.email}
              </p>
            )}
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-6 py-8">
          {loading ? (
            <div className="flex items-center justify-center py-24">
              <div className="font-mono text-xs text-[#525252] animate-pulse">Loading…</div>
            </div>
          ) : (
            <>
              {/* Stat cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-0 border border-[#D0D0D0] bg-white mb-8">
                {stats.map((s, i) => (
                  <div
                    key={s.label}
                    className={`px-6 py-5 ${i < 3 ? 'border-b md:border-b-0 md:border-r border-[#D0D0D0]' : ''}`}
                  >
                    <div className={`font-mono text-3xl font-light mb-1 ${s.color}`}>{s.value}</div>
                    <div className="text-[10px] font-mono uppercase tracking-widest text-[#525252]">{s.label}</div>
                    <div className="text-[10px] text-[#8D8D8D] mt-0.5">{s.sub}</div>
                  </div>
                ))}
              </div>

              {/* Quick actions */}
              <div className="mb-6">
                <p className="text-label mb-3">Quick Actions</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    { href: '/analyzer', label: 'Run Analysis', desc: 'Analyse a branch or PR diff' },
                    { href: '/debugging', label: 'Debug Code', desc: 'Submit a diff for debugging' },
                    { href: '/return-summary', label: 'Return Summary', desc: 'Catch up on what changed' },
                  ].map((a) => (
                    <a
                      key={a.href}
                      href={a.href}
                      className="border border-[#D0D0D0] bg-white p-4 hover:border-[#0F62FE] transition-colors block"
                    >
                      <p className="text-sm font-semibold text-[#161616] mb-1">{a.label}</p>
                      <p className="text-xs text-[#525252]">{a.desc}</p>
                    </a>
                  ))}
                </div>
              </div>

              <div className="border border-[#D0D0D0] bg-white p-6 text-center">
                <p className="text-xs text-[#525252]">
                  Connect your GitHub repository and run your first analysis to populate this dashboard.
                </p>
                <a
                  href="/settings"
                  className="inline-block mt-3 px-4 py-1.5 bg-[#0F62FE] text-white text-xs hover:bg-[#0353E9] transition-colors"
                >
                  Configure Settings
                </a>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
