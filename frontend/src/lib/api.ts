const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    if (response.status === 401 && !endpoint.startsWith("/auth/me")) {
      window.location.href = "/";
      return new Promise(() => {}) as T;
    }
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
