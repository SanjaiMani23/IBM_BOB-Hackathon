/**
 * jira.ts — Jira integration API calls.
 *
 * Issue creation always requires an explicit `confirmed: true` flag in the
 * request — reflecting the server-side safeguard.
 */

import { apiFetch } from './api';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface JiraProject {
  key:  string;
  name: string;
  id:   string;
}

export interface JiraProjectsResponse {
  projects: JiraProject[];
  total:    number;
}

export interface JiraDraft {
  finding_id:          string;
  summary:             string;
  description:         string;
  priority:            string;
  component:           string | null;
  labels:              string[];
  acceptance_criteria: string[];
  technical_notes:     string;
}

export interface JiraCreatedIssue {
  key:    string;
  id:     string;
  url:    string;
  status: string;
}

export interface JiraIssue {
  key:      string;
  id:       string;
  summary:  string;
  status:   string;
  priority: string;
  assignee: string | null;
  created:  string;
  updated:  string;
  url:      string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Endpoints
// ─────────────────────────────────────────────────────────────────────────────

export async function listProjects(): Promise<JiraProjectsResponse> {
  return apiFetch<JiraProjectsResponse>('/jira/projects');
}

export async function draftIssue(
  findingId: string,
  repository: string,
): Promise<JiraDraft> {
  return apiFetch<JiraDraft>('/jira/draft', {
    method: 'POST',
    body: { finding_id: findingId, repository },
  });
}

export interface CreateIssuePayload extends JiraDraft {
  project_key: string;
  issue_type?: string;
  confirmed:   true;   // must be literally true
}

export async function createIssue(payload: CreateIssuePayload): Promise<JiraCreatedIssue> {
  return apiFetch<JiraCreatedIssue>('/jira/issues', {
    method: 'POST',
    body: payload,
  });
}

export async function getIssue(issueKey: string): Promise<JiraIssue> {
  return apiFetch<JiraIssue>(`/jira/issues/${encodeURIComponent(issueKey)}`);
}
