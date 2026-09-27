/**
 * github.ts — GitHub integration API calls.
 */

import { apiFetch } from './api';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface GithubRepository {
  full_name:    string;
  description:  string | null;
  default_branch: string;
  language:     string | null;
  stars:        number;
  open_prs:     number;
}

export interface GithubBranch {
  name:     string;
  sha:      string;
  protected: boolean;
}

export interface GithubCommit {
  sha:     string;
  message: string;
  author:  string;
  date:    string;
}

export interface GithubPullRequest {
  number:     number;
  title:      string;
  state:      string;
  author:     string;
  base_branch: string;
  head_branch: string;
  created_at:  string;
  updated_at:  string;
  url:         string;
}

export interface GithubChangedFile {
  path:      string;
  status:    string;
  additions: number;
  deletions: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Endpoints
// ─────────────────────────────────────────────────────────────────────────────

export async function getRepository(owner: string, repo: string): Promise<GithubRepository> {
  return apiFetch<GithubRepository>(`/github/repos/${owner}/${repo}`);
}

export async function listBranches(owner: string, repo: string): Promise<GithubBranch[]> {
  return apiFetch<GithubBranch[]>(`/github/repos/${owner}/${repo}/branches`);
}

export async function listCommits(
  owner: string,
  repo: string,
  branch?: string,
): Promise<GithubCommit[]> {
  return apiFetch<GithubCommit[]>(`/github/repos/${owner}/${repo}/commits`, {
    params: branch ? { branch } : undefined,
  });
}

export async function listPullRequests(
  owner: string,
  repo: string,
  state: 'open' | 'closed' | 'all' = 'open',
): Promise<GithubPullRequest[]> {
  return apiFetch<GithubPullRequest[]>(`/github/repos/${owner}/${repo}/pulls`, {
    params: { state },
  });
}

export async function getPullRequestDiff(
  owner: string,
  repo: string,
  prNumber: number,
): Promise<string> {
  return apiFetch<string>(`/github/repos/${owner}/${repo}/pulls/${prNumber}/diff`);
}

export async function listPullRequestFiles(
  owner: string,
  repo: string,
  prNumber: number,
): Promise<GithubChangedFile[]> {
  return apiFetch<GithubChangedFile[]>(`/github/repos/${owner}/${repo}/pulls/${prNumber}/files`);
}
