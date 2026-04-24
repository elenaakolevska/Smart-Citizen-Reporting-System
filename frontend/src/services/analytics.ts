import { apiFetch } from "./api";

export interface AnalyticsSummary {
  kpis: {
    total: number;
    resolved: number;
    avgTime: string;
    activeCitizens: number;
  };
  categoryData: Array<{
    name: string;
    complaints: number;
    resolved: number;
  }>;
  pieData: Array<{
    name: string;
    value: number;
  }>;
  monthlyData: Array<{
    month: string;
    complaints: number;
    resolved: number;
  }>;
  ratingData: Array<{
    name: string;
    rating: number;
    count: number;
  }>;
  resolutionRate: number;
}

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  const data = await apiFetch<AnalyticsSummary>("/analytics/summary");
  
  // Mock rating data if not present in response (CR-06)
  if (!data.ratingData) {
    data.ratingData = [
      { name: "Инфраструктура", rating: 4.2, count: 45 },
      { name: "Комунални услуги", rating: 3.8, count: 82 },
      { name: "Администрација", rating: 4.5, count: 28 },
      { name: "Безбедност", rating: 4.0, count: 15 },
    ];
  }
  
  return data;
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
