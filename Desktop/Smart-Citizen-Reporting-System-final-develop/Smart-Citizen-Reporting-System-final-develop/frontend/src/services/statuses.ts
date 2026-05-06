import { supabase } from "@/lib/supabase";

export interface Status {
  id: number;
  name: string;
}

export async function fetchStatuses(): Promise<Status[]> {
  const { data, error } = await supabase
    .from("statuses")
    .select("id, name")
    .order("id", { ascending: true });

  if (error) {
    throw new Error(error.message || "Failed to fetch statuses.");
  }

  return data ?? [];
}
