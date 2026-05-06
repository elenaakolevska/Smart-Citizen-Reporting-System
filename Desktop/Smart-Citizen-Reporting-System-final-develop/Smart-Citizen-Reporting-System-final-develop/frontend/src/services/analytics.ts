import { apiFetch } from "./api";

export interface AnalyticsSummary {
  kpis: {
    total: number;
    resolved: number;
    active: number;
    avgTime: string;
    activeCitizens: number;
  };
  categoryData: Array<{
    name: string;
    complaints: number;
    resolved: number;
    active: number;
  }>;
  pieData: Array<{
    name: string;
    value: number;
  }>;
  monthlyData: Array<{
    month: string;
    complaints: number;
    resolved: number;
    active: number;
  }>;
  resolutionRate: number;
}

export function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  return apiFetch<AnalyticsSummary>("/analytics/summary");
}

export async function exportToCsv() {
  const token = localStorage.getItem("auth_token");
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
  
  const response = await fetch(`${API_BASE_URL}/analytics/export/csv`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) throw new Error("Export failed");
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `UrbanCare_Export_${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export async function exportToPdf() {
  const token = localStorage.getItem("auth_token");
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
  
  const response = await fetch(`${API_BASE_URL}/analytics/export/pdf`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) throw new Error("Export failed");
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `UrbanCare_Export_${new Date().toISOString().split('T')[0]}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}
