// Status style mapping (fallback visual styles by status_id)
const statusStyles: Record<number, string> = {
  1: "bg-info/10 text-info border-info/20",
  2: "bg-warning/10 text-warning border-warning/20",
  3: "bg-muted text-muted-foreground",
  4: "bg-success/10 text-success border-success/20",
  5: "bg-destructive/10 text-destructive border-destructive/20",
};

export function getStatusStyle(id: number | null): string {
  if (id == null) return "bg-muted text-muted-foreground";
  return statusStyles[id] ?? "bg-muted text-muted-foreground";
}

export function deriveTitle(description: string, maxLen = 50): string {
  if (description.length <= maxLen) return description;
  const cut = description.substring(0, maxLen);
  const lastSpace = cut.lastIndexOf(" ");
  return (lastSpace > 20 ? cut.substring(0, lastSpace) : cut) + "…";
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("mk-MK", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function formatCoords(lat: number, lng: number): string {
  return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}

const priorityStyles: Record<string, string> = {
  low: "bg-slate-100 text-slate-700 border-slate-200",
  medium: "bg-blue-100 text-blue-700 border-blue-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  urgent: "bg-red-100 text-red-700 border-red-200",
};

export function getPriorityStyle(priority: string | null): string {
  if (!priority) return "bg-slate-100 text-slate-700 border-slate-200";
  return priorityStyles[priority.toLowerCase()] ?? "bg-slate-100 text-slate-700 border-slate-200";
}

export function formatPriority(priority: string | null): string {
  if (!priority) return "Непознато";
  const p = priority.toLowerCase();
  if (p === "low") return "Низок";
  if (p === "medium") return "Среден";
  if (p === "high") return "Висок";
  if (p === "urgent") return "Итен";
  return priority;
}
