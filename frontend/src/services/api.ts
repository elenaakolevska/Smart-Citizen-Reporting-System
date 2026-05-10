const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("auth_token");
  const isBodied = options?.body !== undefined && options.body !== null;

  // Only set Content-Type when we actually send a body — bare GETs don't need it,
  // and FormData uploads must be left alone so the browser sets the boundary.
  const headers: Record<string, string> = {
    ...(isBodied && !(options?.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers as Record<string, string> | undefined),
  };

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

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

    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return body as T;
}
