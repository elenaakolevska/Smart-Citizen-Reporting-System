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

function normalizePriority(priority: string | null | undefined): string {
  if (!priority || typeof priority !== "string") return "";
  return priority.trim().toLowerCase();
}

export function getPriorityLabel(priority: string | null | undefined): string {
  const normalized = normalizePriority(priority);
  if (normalized === "итен" || normalized === "urgent" || normalized === "critical") return "Итен";
  if (normalized === "висок" || normalized === "high") return "Висок";
  if (normalized === "среден" || normalized === "medium" || normalized === "normal") return "Среден";
  if (normalized === "низок" || normalized === "low") return "Низок";
  return "Непознат";
}

export function getPriorityStyle(priority: string | null | undefined): string {
  const normalized = normalizePriority(priority);
  if (normalized === "итен" || normalized === "urgent" || normalized === "critical") {
    return "bg-destructive/10 text-destructive border-destructive/20";
  }
  if (normalized === "висок" || normalized === "high") {
    return "bg-warning/10 text-warning border-warning/20";
  }
  if (normalized === "среден" || normalized === "medium" || normalized === "normal") {
    return "bg-info/10 text-info border-info/20";
  }
  if (normalized === "низок" || normalized === "low") {
    return "bg-success/10 text-success border-success/20";
  }
  return "bg-muted text-muted-foreground";
}

export const CATEGORY_TRANSLATIONS: Record<string, string> = {
  Environment: "Околина",
  Infrastructure: "Инфраструктура",
  Safety: "Безбедност",
  Other: "Друго",
};

export function getCategoryMacedonianName(categoryName: string): string {
  return CATEGORY_TRANSLATIONS[categoryName] || categoryName;
}
