"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { useBookmarks } from "./hooks/useBookmarks";
import { toast } from "sonner";
import type {
  BookmarkCategory,
  Bookmark,
  CategoryCreateRequest,
  BookmarkCreateRequest,
  BookmarkUpdateRequest,
} from "./types";

interface BookmarkContextValue {
  categories: BookmarkCategory[];
  bookmarks: Bookmark[];
  loading: boolean;
  selectedCategoryId: number | null;
  onSelectCategory: (id: number | null) => void;
  onCreateCategory: (data: CategoryCreateRequest) => Promise<void>;
  onDeleteCategory: (id: number) => Promise<void>;
  onCreateBookmark: (data: BookmarkCreateRequest) => Promise<void>;
  onUpdateBookmark: (id: number, data: BookmarkUpdateRequest) => Promise<void>;
  onDeleteBookmark: (id: number) => Promise<void>;
  // Modal state
  addBookmarkOpen: boolean;
  setAddBookmarkOpen: (open: boolean) => void;
  editingBookmark: Bookmark | null;
  setEditingBookmark: (bm: Bookmark | null) => void;
  addCategoryOpen: boolean;
  setAddCategoryOpen: (open: boolean) => void;
}

const BookmarkCtx = createContext<BookmarkContextValue | null>(null);

export function useBookmarkContext() {
  const ctx = useContext(BookmarkCtx);
  if (!ctx) throw new Error("useBookmarkContext must be used within BookmarkProvider");
  return ctx;
}

interface BookmarkProviderProps {
  children: ReactNode;
}

export function BookmarkProvider({ children }: BookmarkProviderProps) {
  const [addBookmarkOpen, setAddBookmarkOpen] = useState(false);
  const [editingBookmark, setEditingBookmark] = useState<Bookmark | null>(null);
  const [addCategoryOpen, setAddCategoryOpen] = useState(false);

  const {
    categories,
    bookmarks,
    loading,
    selectedCategoryId,
    setSelectedCategoryId,
    createCategory,
    deleteCategory,
    createBookmark,
    updateBookmark,
    deleteBookmark,
  } = useBookmarks({ enabled: true });

  const onSelectCategory = useCallback((id: number | null) => {
    setSelectedCategoryId(id);
  }, [setSelectedCategoryId]);

  const onCreateCategory = useCallback(async (data: CategoryCreateRequest) => {
    try {
      await createCategory(data);
      toast.success("카테고리가 생성되었습니다");
      setAddCategoryOpen(false);
    } catch {
      toast.error("카테고리 생성에 실패했습니다");
    }
  }, [createCategory]);

  const onDeleteCategory = useCallback(async (id: number) => {
    try {
      await deleteCategory(id);
      toast.success("카테고리가 삭제되었습니다");
    } catch {
      toast.error("카테고리 삭제에 실패했습니다");
    }
  }, [deleteCategory]);

  const onCreateBookmark = useCallback(async (data: BookmarkCreateRequest) => {
    try {
      await createBookmark(data);
      toast.success("북마크가 생성되었습니다");
      setAddBookmarkOpen(false);
    } catch {
      toast.error("북마크 생성에 실패했습니다");
    }
  }, [createBookmark]);

  const onUpdateBookmark = useCallback(async (id: number, data: BookmarkUpdateRequest) => {
    try {
      await updateBookmark(id, data);
      toast.success("북마크가 수정되었습니다");
      setEditingBookmark(null);
    } catch {
      toast.error("북마크 수정에 실패했습니다");
    }
  }, [updateBookmark]);

  const onDeleteBookmark = useCallback(async (id: number) => {
    try {
      await deleteBookmark(id);
      toast.success("북마크가 삭제되었습니다");
    } catch {
      toast.error("북마크 삭제에 실패했습니다");
    }
  }, [deleteBookmark]);

  return (
    <BookmarkCtx.Provider
      value={{
        categories,
        bookmarks,
        loading,
        selectedCategoryId,
        onSelectCategory,
        onCreateCategory,
        onDeleteCategory,
        onCreateBookmark,
        onUpdateBookmark,
        onDeleteBookmark,
        addBookmarkOpen,
        setAddBookmarkOpen,
        editingBookmark,
        setEditingBookmark,
        addCategoryOpen,
        setAddCategoryOpen,
      }}
    >
      {children}
    </BookmarkCtx.Provider>
  );
}
