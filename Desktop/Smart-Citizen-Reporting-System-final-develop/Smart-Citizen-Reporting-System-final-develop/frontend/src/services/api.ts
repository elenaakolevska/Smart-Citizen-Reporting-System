const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("auth_token");

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  const contentType = res.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  let body: any = null;
  if (isJson) {
    body = await res.json();
  } else if (res.status !== 204) {
    const text = await res.text();
    body = text ? { detail: text } : null;
  }

  if (!res.ok) {
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : Array.isArray(body?.detail)
          ? body.detail.map((item: any) => item?.msg ?? JSON.stringify(item)).join(", ")
          : `API error: ${res.status} ${res.statusText}`;

    throw new Error(detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return body as T;
}
