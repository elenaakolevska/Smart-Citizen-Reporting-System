import { useState, useEffect } from "react";
import { fetchCategories, type Category } from "@/services/categories";
import { fetchStatuses, type Status } from "@/services/statuses";
import { getCategoryMacedonianName } from "@/lib/reportHelpers";

export function useLookups() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [statuses, setStatuses] = useState<Status[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchCategories(), fetchStatuses()])
      .then(([cats, stats]) => {
        if (!cancelled) {
          setCategories(cats);
          setStatuses(stats);
        }
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const categoryLabel = (id: number | null) => {
    if (id == null) return "Непознато";
    const categoryName = categories.find((c) => c.id === id)?.name;
    return categoryName ? getCategoryMacedonianName(categoryName) : `Категорија #${id}`;
  };

  const statusLabel = (id: number | null) => {
    if (id == null) return "Непознат";
    return statuses.find((s) => s.id === id)?.name ?? `Статус #${id}`;
  };

  return { categories, statuses, loading, categoryLabel, statusLabel };
}
