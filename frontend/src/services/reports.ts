import { apiFetch } from "./api";

export interface HistoryRead {
  id: number;
  old_status_id: number | null;
  status_id: number | null;
  changed_by_user_id: string | null;
  created_at: string;
}

export interface CommentRead {
  id: number;
  user_id: string;
  content: string;
  created_at: string;
}

export interface ReportRead {
  id: number;
  description: string;
  latitude: number | null;
  longitude: number | null;
  category_id: number | null;
  status_id: number | null;
  user_id: string;
  created_at: string;
  priority: string | null;
  rating: number | null;
  rating_comment: string | null;
  possible_duplicate_of: number | null;
  history_entries: HistoryRead[];
  comments: CommentRead[];
}

export interface ReportCreate {
  description: string;
  latitude: number | null;
  longitude: number | null;
  category_id?: number | null;
  priority?: string | null;
}

export function fetchReports(): Promise<ReportRead[]> {
  return apiFetch<ReportRead[]>("/reports");
}

export function fetchReportById(id: number): Promise<ReportRead> {
  return apiFetch<ReportRead>(`/reports/${id}`);
}

export function createReport(data: ReportCreate): Promise<ReportRead> {
  return apiFetch<ReportRead>("/reports", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function addComment(reportId: number, content: string): Promise<CommentRead> {
  return apiFetch<CommentRead>(`/reports/${reportId}/comments`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

/**
 * Rate a closed report (CR-06)
 */
export async function rateReport(reportId: number, rating: number, comment?: string): Promise<void> {
  return apiFetch<void>(`/reports/${reportId}/rate`, {
    method: "POST",
    body: JSON.stringify({ rating, rating_comment: comment }),
  });
}

/**
 * Update report priority (CR-02)
 */
export async function updateReportPriority(reportId: number, priority: string): Promise<void> {
  return apiFetch<void>(`/reports/${reportId}`, {
    method: "PATCH",
    body: JSON.stringify({ priority }),
  });
}
