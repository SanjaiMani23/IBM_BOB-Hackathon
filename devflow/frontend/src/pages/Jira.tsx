import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { listProjects, draftIssue, createIssue, type JiraProject, type JiraDraft } from '../services/jira';
import { ApiError } from '../services/api';

type Step = 'select' | 'draft' | 'confirm' | 'created';

export default function Jira() {
  const [projects, setProjects] = useState<JiraProject[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectsError, setProjectsError] = useState<string | null>(null);

  const [findingId, setFindingId] = useState('');
  const [repository, setRepository] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  const [issueType, setIssueType] = useState('Bug');

  const [step, setStep] = useState<Step>('select');
  const [draft, setDraft] = useState<JiraDraft | null>(null);
  const [draftLoading, setDraftLoading] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [createdUrl, setCreatedUrl] = useState<string | null>(null);

  useEffect(() => {
    listProjects()
      .then((r) => setProjects(r.projects))
      .catch((err) => setProjectsError(err instanceof ApiError ? err.detail : 'Could not load projects'))
      .finally(() => setProjectsLoading(false));
  }, []);

  const handleDraft = async () => {
    if (!findingId.trim() || !repository.trim()) return;
    setDraftLoading(true);
    setError(null);
    try {
      const d = await draftIssue(findingId, repository);
      setDraft(d);
      setStep('draft');
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not generate draft');
    } finally {
      setDraftLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!draft || !selectedProject) return;
    setCreateLoading(true);
    setError(null);
    try {
      const res = await createIssue({
        ...draft,
        project_key: selectedProject,
        issue_type: issueType,
        confirmed: true,
      });
      setCreatedKey(res.key);
      setCreatedUrl(res.url);
      setStep('created');
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Could not create issue');
    } finally {
      setCreateLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-6">
          <div className="max-w-3xl mx-auto">
            <p className="text-label mb-1">Jira Integration</p>
            <h1 className="text-xl font-semibold text-[#161616]">Create Ticket</h1>
            <p className="text-xs text-[#525252] mt-1">
              AI drafts a Jira ticket from a code finding. You review and confirm before anything is created.
            </p>
          </div>
        </div>

        <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
          {projectsError && (
            <div className="border border-[#DA1E28] bg-[#FFF1F1] px-4 py-3 text-xs text-[#DA1E28] font-mono">
              {projectsError}
            </div>
          )}

          {step === 'created' ? (
            <div className="bg-white border border-[#198038] p-8 text-center space-y-3">
              <div className="w-10 h-10 border border-[#198038] flex items-center justify-center mx-auto">
                <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M3 8L6.5 11.5L13 5" stroke="#198038" strokeWidth="1.5"/></svg>
              </div>
              <p className="text-lg font-semibold text-[#161616]">Jira issue created</p>
              <p className="font-mono text-sm text-[#0F62FE]">{createdKey}</p>
              {createdUrl && (
                <a href={createdUrl} target="_blank" rel="noopener noreferrer"
                  className="inline-block px-4 py-1.5 bg-[#0F62FE] text-white text-xs hover:bg-[#0353E9] transition-colors">
                  Open in Jira
                </a>
              )}
              <button onClick={() => { setStep('select'); setDraft(null); setFindingId(''); setRepository(''); }}
                className="block mx-auto mt-2 text-xs text-[#525252] underline hover:text-[#161616]">
                Create another
              </button>
            </div>
          ) : (
            <>
              {/* Step 1 — Input */}
              <div className="bg-white border border-[#D0D0D0] p-6">
                <p className="text-sm font-semibold text-[#161616] mb-4">Step 1 — Finding & Project</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Finding ID *</label>
                    <input value={findingId} onChange={(e) => setFindingId(e.target.value)} placeholder="UUID of the finding"
                      disabled={step !== 'select'}
                      className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE] disabled:bg-[#F4F4F4]" />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Repository *</label>
                    <input value={repository} onChange={(e) => setRepository(e.target.value)} placeholder="owner/repo"
                      disabled={step !== 'select'}
                      className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE] disabled:bg-[#F4F4F4]" />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Jira Project *</label>
                    <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)}
                      className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE] bg-white">
                      <option value="">
                        {projectsLoading ? 'Loading…' : 'Select project…'}
                      </option>
                      {projects.map((p) => (
                        <option key={p.key} value={p.key}>{p.key} — {p.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">Issue Type</label>
                    <input value={issueType} onChange={(e) => setIssueType(e.target.value)} placeholder="Bug"
                      className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]" />
                  </div>
                </div>
                {step === 'select' && (
                  <div className="flex items-center justify-between">
                    {error && <p className="text-xs text-[#DA1E28] font-mono">{error}</p>}
                    <div className="ml-auto">
                      <button onClick={handleDraft}
                        disabled={draftLoading || !findingId.trim() || !repository.trim()}
                        className="px-5 py-2 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors disabled:opacity-60 flex items-center gap-2">
                        {draftLoading && <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>}
                        {draftLoading ? 'Generating Draft…' : 'Generate Draft'}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Step 2 — Review draft */}
              {draft && step === 'draft' && (
                <div className="bg-white border border-[#D0D0D0] p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-[#161616]">Step 2 — Review Draft</p>
                    <span className="text-[10px] font-mono bg-[#EDF4FF] text-[#0F62FE] px-2 py-0.5">AI GENERATED — REVIEW BEFORE CREATING</span>
                  </div>
                  <div>
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-1">Summary</p>
                    <p className="text-sm text-[#161616]">{draft.summary}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-1">Priority</p>
                    <span className="font-mono text-xs bg-[#F4F4F4] px-2 py-0.5 text-[#161616]">{draft.priority}</span>
                  </div>
                  <div>
                    <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-1">Description</p>
                    <p className="text-xs text-[#525252] leading-relaxed">{draft.description}</p>
                  </div>
                  {draft.acceptance_criteria.length > 0 && (
                    <div>
                      <p className="text-[10px] font-mono text-[#525252] uppercase tracking-wide mb-1">Acceptance Criteria</p>
                      <ul className="list-disc list-inside space-y-1">
                        {draft.acceptance_criteria.map((c, i) => (
                          <li key={i} className="text-xs text-[#161616]">{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {draft.labels.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                      {draft.labels.map((l) => (
                        <span key={l} className="text-[10px] font-mono bg-[#F4F4F4] text-[#525252] px-2 py-0.5">{l}</span>
                      ))}
                    </div>
                  )}
                  <div className="flex items-center gap-3 pt-2">
                    <button onClick={() => setStep('select')}
                      className="px-4 py-1.5 border border-[#D0D0D0] text-xs text-[#161616] hover:border-[#161616] transition-colors bg-white">
                      Edit Inputs
                    </button>
                    {error && <p className="text-xs text-[#DA1E28] font-mono flex-1">{error}</p>}
                    <button onClick={handleCreate}
                      disabled={createLoading || !selectedProject}
                      className="ml-auto px-5 py-2 bg-[#198038] text-white text-xs font-medium hover:bg-[#0E6027] transition-colors disabled:opacity-60 flex items-center gap-2">
                      {createLoading && <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>}
                      {createLoading ? 'Creating…' : 'Confirm & Create Issue'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
