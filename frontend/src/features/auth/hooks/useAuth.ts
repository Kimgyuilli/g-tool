import { useEffect, useState, useCallback, useSyncExternalStore } from "react";
import { apiFetch } from "@/lib/api";
import type { UserInfo } from "@/features/auth/types";

// --- auth state external store (SSR-safe) ---
interface AuthState {
  userInfo: UserInfo | null;
  loading: boolean;
}

let authState: AuthState = { userInfo: null, loading: true };
let authListeners: Array<() => void> = [];
let authChecked = false;

function getAuthSnapshot(): AuthState {
  return authState;
}

function getAuthServerSnapshot(): AuthState {
  return { userInfo: null, loading: true };
}

function subscribeAuth(onStoreChange: () => void): () => void {
  authListeners.push(onStoreChange);

  // Trigger auth check on first subscribe (client-side)
  if (!authChecked) {
    authChecked = true;
    apiFetch<UserInfo>("/auth/me")
      .then((info) => {
        authState = { userInfo: info, loading: false };
        authListeners.forEach((l) => l());
      })
      .catch(() => {
        authState = { userInfo: null, loading: false };
        authListeners.forEach((l) => l());
      });
  }

  return () => {
    authListeners = authListeners.filter((l) => l !== onStoreChange);
  };
}

function setAuthState(update: Partial<AuthState>) {
  authState = { ...authState, ...update };
  authListeners.forEach((l) => l());
}

export function useAuth() {
  const { userInfo, loading } = useSyncExternalStore(subscribeAuth, getAuthSnapshot, getAuthServerSnapshot);
  const [categories, setCategories] = useState<string[]>([]);

  const isLoggedIn = userInfo !== null;

  const setUserInfo = useCallback((updater: UserInfo | null | ((prev: UserInfo | null) => UserInfo | null)) => {
    const newInfo = typeof updater === "function" ? updater(authState.userInfo) : updater;
    setAuthState({ userInfo: newInfo });
  }, []);

  // Load categories when logged in
  useEffect(() => {
    if (!isLoggedIn) return;
    apiFetch<{ categories: string[] }>("/api/classify/categories")
      .then((data) => setCategories(data.categories))
      .catch(() => {});
  }, [isLoggedIn]);

  const handleLogin = useCallback(async () => {
    const data = await apiFetch<{ auth_url: string }>("/auth/login");
    window.location.href = data.auth_url;
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } catch {
      // ignore
    }
    setAuthState({ userInfo: null });
  }, []);

  return {
    isLoggedIn,
    loading,
    userInfo,
    setUserInfo,
    categories,
    handleLogin,
    handleLogout,
  };
}
