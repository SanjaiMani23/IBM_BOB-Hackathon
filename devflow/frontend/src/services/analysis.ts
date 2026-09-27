/**
 * analysis.ts — Analysis, debugging, optimization, testing, and summary API calls.
 */

import { apiFetch } from './api';

// ─────────────────────────────────────────────────────────────────────────────
// Shared types
// ─────────────────────────────────────────────────────────────────────────────

export type Severity = 'critical' | 'high' | 'medium' | 'low';
export type FindingType = 'security' | 'bug' | 'optimization' | 'structure' | 'quality';

export interface ApiFinding {
  id:             string;
  title:          string;
  severity:       Severity;
  finding_type:   FindingType;
  explanation:    string;
  recommendation: string;
  file_path:      string | null;
  line_number:    number | null;
  confidence:     string | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Analysis
// ─────────────────────────────────────────────────────────────────────────────

export interface AnalysisRequest {
  repository:  string;
  branch:      string;
  commit_sha?: string;
}

export interface AnalysisResponse {
  analysis_id:     string;
  repository:      string;
  branch:          string;
  commit_sha:      string;
  files_analyzed:  number;
  total_findings:  number;
  critical_count:  number;
  high_count:      number;
  medium_count:    number;
  low_count:       number;
  findings:        ApiFinding[];
  duration_ms:     number;
  created_at:      string;
}

export async function runAnalysis(req: AnalysisRequest): Promise<AnalysisResponse> {
  return apiFetch<AnalysisResponse>('/analysis', { method: 'POST', body: req });
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResponse> {
  return apiFetch<AnalysisResponse>(`/analysis/${analysisId}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// Debugging
// ─────────────────────────────────────────────────────────────────────────────

export interface DebugRequest {
  diff:       string;
  repository: string;
  language?:  string;
}

export interface DebugIssue {
  title:          string;
  severity:       Severity;
  explanation:    string;
  recommendation: string;
  line_number:    number | null;
  confidence:     string;
  finding_type:   string;
}

export interface DebugResponse {
  issues:      DebugIssue[];
  summary:     string;
  ai_enhanced: boolean;
  duration_ms: number;
}

export async function debugCode(req: DebugRequest): Promise<DebugResponse> {
  return apiFetch<DebugResponse>('/debug', { method: 'POST', body: req });
}

// ─────────────────────────────────────────────────────────────────────────────
// Optimization
// ─────────────────────────────────────────────────────────────────────────────

export interface OptimizationRequest {
  diff:       string;
  repository: string;
  language?:  string;
}

export interface OptimizationSuggestion {
  title:          string;
  priority:       string;
  explanation:    string;
  suggestion:     string;
  suggested_code: string | null;
  trade_offs:     string | null;
  file_path:      string | null;
  line_number:    number | null;
}

export interface OptimizationResponse {
  suggestions:  OptimizationSuggestion[];
  summary:      string;
  ai_enhanced:  boolean;
  duration_ms:  number;
}

export async function optimizeCode(req: OptimizationRequest): Promise<OptimizationResponse> {
  return apiFetch<OptimizationResponse>('/optimize', { method: 'POST', body: req });
}

// ─────────────────────────────────────────────────────────────────────────────
// Testing
// ─────────────────────────────────────────────────────────────────────────────

export interface TestRequest {
  diff:       string;
  repository: string;
  language?:  string;
  framework?: string;
}

export interface TestCase {
  name:        string;
  category:    string;
  description: string;
  code:        string;
  rationale:   string;
}

export interface TestResponse {
  tests:       TestCase[];
  summary:     string;
  disclaimer:  string;
  ai_enhanced: boolean;
  duration_ms: number;
}

export async function generateTests(req: TestRequest): Promise<TestResponse> {
  return apiFetch<TestResponse>('/testing', { method: 'POST', body: req });
}

// ─────────────────────────────────────────────────────────────────────────────
// Summaries
// ─────────────────────────────────────────────────────────────────────────────

export interface PrDescriptionRequest {
  diff?:       string;
  repository:  string;
  pr_number?:  number;
  branch?:     string;
}

export interface PrDescriptionResponse {
  title:             string;
  summary:           string;
  motivation:        string;
  changes:           string[];
  testing_notes:     string;
  breaking_changes:  string | null;
  reviewer_checklist: string[];
  ai_enhanced:       boolean;
}

export async function generatePrDescription(req: PrDescriptionRequest): Promise<PrDescriptionResponse> {
  return apiFetch<PrDescriptionResponse>('/summaries/pr', { method: 'POST', body: req });
}

export interface ReturnSummaryRequest {
  repository:  string;
  branch?:     string;
  since_days?: number;
}

export interface ReturnSummaryResponse {
  briefing:         string;
  recent_commits:   string[];
  open_prs:         string[];
  key_findings:     string[];
  recommended_actions: string[];
  ai_enhanced:      boolean;
}

export async function generateReturnSummary(req: ReturnSummaryRequest): Promise<ReturnSummaryResponse> {
  return apiFetch<ReturnSummaryResponse>('/summaries/return', { method: 'POST', body: req });
}
