import { supabase } from "@/lib/supabase";

export interface Category {
  id: number;
  name: string;
}

export async function fetchCategories(): Promise<Category[]> {
  const { data, error } = await supabase
    .from("categories")
    .select("id, name")
    .order("id", { ascending: true });

  if (error) {
    throw new Error(error.message || "Failed to fetch categories.");
  }

  return data ?? [];
}
