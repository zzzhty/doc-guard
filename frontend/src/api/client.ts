const API_BASE = "/api/v1";

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function get<T>(url: string): Promise<T> {
  return request<T>(url, { method: "GET" });
}

export function post<T>(url: string, data?: unknown): Promise<T> {
  return request<T>(url, {
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
  });
}

export function put<T>(url: string, data?: unknown): Promise<T> {
  return request<T>(url, {
    method: "PUT",
    body: data ? JSON.stringify(data) : undefined,
  });
}

export function del<T>(url: string): Promise<T> {
  return request<T>(url, { method: "DELETE" });
}

export { API_BASE };
