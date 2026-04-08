import { toast } from "sonner";

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
      // 인증 상태에 따라 안내 메시지를 구분한다.
      try {
        const body = await response.json();
        if (body?.detail?.code === "google_reconnect_required") {
          toast.warning("Google 권한이 변경되어 다시 연결이 필요합니다.");
        } else if (body?.detail?.code === "token_expired") {
          toast.warning("세션이 만료되었습니다. 다시 로그인해주세요.");
        }
      } catch {
        // JSON 파싱 실패 시 무시
      }
      window.location.href = "/";
      return new Promise(() => {}) as T;
    }
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
