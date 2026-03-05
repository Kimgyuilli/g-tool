import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type {
  BookmarkCategory,
  Bookmark,
  BookmarkCreateRequest,
  BookmarkUpdateRequest,
  CategoryCreateRequest,
  CategoriesResponse,
  BookmarksResponse,
} from "../types";

interface UseBookmarksOptions {
  userId: number | null;
  enabled?: boolean;
}

export function useBookmarks({ userId, enabled = true }: UseBookmarksOptions) {
  const [categories, setCategories] = useState<BookmarkCategory[]>([]);
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null); // null = all

  const loadCategories = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const data = await apiFetch<CategoriesResponse>(
        `/api/bookmark/categories?user_id=${userId}`
      );
      setCategories(data.categories);
    } catch {
      // 에러 시 기존 데이터 보존
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const loadBookmarks = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const url = selectedCategoryId !== null
        ? `/api/bookmark/bookmarks?user_id=${userId}&category_id=${selectedCategoryId}`
        : `/api/bookmark/bookmarks?user_id=${userId}`;
      const data = await apiFetch<BookmarksResponse>(url);
      setBookmarks(data.bookmarks);
    } catch {
      // 에러 시 기존 데이터 보존
    } finally {
      setLoading(false);
    }
  }, [userId, selectedCategoryId]);

  useEffect(() => {
    if (enabled && userId) {
      loadCategories();
    }
  }, [enabled, userId, loadCategories]);

  useEffect(() => {
    if (enabled && userId) {
      loadBookmarks();
    }
  }, [enabled, userId, selectedCategoryId, loadBookmarks]);

  const createCategory = useCallback(
    async (data: CategoryCreateRequest) => {
      if (!userId) return null;
      const category = await apiFetch<BookmarkCategory>(
        `/api/bookmark/categories?user_id=${userId}`,
        { method: "POST", body: JSON.stringify(data) }
      );
      setCategories((prev) => [...prev, category]);
      return category;
    },
    [userId]
  );

  const deleteCategory = useCallback(
    async (categoryId: number) => {
      if (!userId) return;
      setCategories((prev) => prev.filter((c) => c.id !== categoryId));
      await apiFetch(`/api/bookmark/categories/${categoryId}?user_id=${userId}`, {
        method: "DELETE",
      });
      // Reload bookmarks to reflect uncategorized items
      await loadBookmarks();
    },
    [userId, loadBookmarks]
  );

  const createBookmark = useCallback(
    async (data: BookmarkCreateRequest) => {
      if (!userId) return null;
      const bookmark = await apiFetch<Bookmark>(
        `/api/bookmark/bookmarks?user_id=${userId}`,
        { method: "POST", body: JSON.stringify(data) }
      );
      setBookmarks((prev) => [...prev, bookmark]);
      // Reload categories to update counts
      await loadCategories();
      return bookmark;
    },
    [userId, loadCategories]
  );

  const updateBookmark = useCallback(
    async (bookmarkId: number, data: BookmarkUpdateRequest) => {
      if (!userId) return null;
      const updated = await apiFetch<Bookmark>(
        `/api/bookmark/bookmarks/${bookmarkId}?user_id=${userId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      );
      setBookmarks((prev) =>
        prev.map((b) => (b.id === bookmarkId ? updated : b))
      );
      // Reload categories to update counts
      await loadCategories();
      return updated;
    },
    [userId, loadCategories]
  );

  const deleteBookmark = useCallback(
    async (bookmarkId: number) => {
      if (!userId) return;
      setBookmarks((prev) => prev.filter((b) => b.id !== bookmarkId));
      await apiFetch(`/api/bookmark/bookmarks/${bookmarkId}?user_id=${userId}`, {
        method: "DELETE",
      });
      // Reload categories to update counts
      await loadCategories();
    },
    [userId, loadCategories]
  );

  return {
    categories,
    bookmarks,
    loading,
    selectedCategoryId,
    setSelectedCategoryId,
    loadCategories,
    loadBookmarks,
    createCategory,
    deleteCategory,
    createBookmark,
    updateBookmark,
    deleteBookmark,
  };
}
