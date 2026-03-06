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
  enabled?: boolean;
}

export function useBookmarks({ enabled = true }: UseBookmarksOptions = {}) {
  const [categories, setCategories] = useState<BookmarkCategory[]>([]);
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null); // null = all

  const loadCategories = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<CategoriesResponse>(
        "/api/bookmark/categories"
      );
      setCategories(data.categories);
    } catch {
      // 에러 시 기존 데이터 보존
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBookmarks = useCallback(async () => {
    setLoading(true);
    try {
      const url = selectedCategoryId !== null
        ? `/api/bookmark/bookmarks?category_id=${selectedCategoryId}`
        : "/api/bookmark/bookmarks";
      const data = await apiFetch<BookmarksResponse>(url);
      setBookmarks(data.bookmarks);
    } catch {
      // 에러 시 기존 데이터 보존
    } finally {
      setLoading(false);
    }
  }, [selectedCategoryId]);

  useEffect(() => {
    if (enabled) {
      loadCategories();
    }
  }, [enabled, loadCategories]);

  useEffect(() => {
    if (enabled) {
      loadBookmarks();
    }
  }, [enabled, selectedCategoryId, loadBookmarks]);

  const createCategory = useCallback(
    async (data: CategoryCreateRequest) => {
      const category = await apiFetch<BookmarkCategory>(
        "/api/bookmark/categories",
        { method: "POST", body: JSON.stringify(data) }
      );
      setCategories((prev) => [...prev, category]);
      return category;
    },
    []
  );

  const deleteCategory = useCallback(
    async (categoryId: number) => {
      setCategories((prev) => prev.filter((c) => c.id !== categoryId));
      await apiFetch(`/api/bookmark/categories/${categoryId}`, {
        method: "DELETE",
      });
      // Reload bookmarks to reflect uncategorized items
      await loadBookmarks();
    },
    [loadBookmarks]
  );

  const createBookmark = useCallback(
    async (data: BookmarkCreateRequest) => {
      const bookmark = await apiFetch<Bookmark>(
        "/api/bookmark/bookmarks",
        { method: "POST", body: JSON.stringify(data) }
      );
      setBookmarks((prev) => [...prev, bookmark]);
      // Reload categories to update counts
      await loadCategories();
      return bookmark;
    },
    [loadCategories]
  );

  const updateBookmark = useCallback(
    async (bookmarkId: number, data: BookmarkUpdateRequest) => {
      const updated = await apiFetch<Bookmark>(
        `/api/bookmark/bookmarks/${bookmarkId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      );
      setBookmarks((prev) =>
        prev.map((b) => (b.id === bookmarkId ? updated : b))
      );
      // Reload categories to update counts
      await loadCategories();
      return updated;
    },
    [loadCategories]
  );

  const deleteBookmark = useCallback(
    async (bookmarkId: number) => {
      setBookmarks((prev) => prev.filter((b) => b.id !== bookmarkId));
      await apiFetch(`/api/bookmark/bookmarks/${bookmarkId}`, {
        method: "DELETE",
      });
      // Reload categories to update counts
      await loadCategories();
    },
    [loadCategories]
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
