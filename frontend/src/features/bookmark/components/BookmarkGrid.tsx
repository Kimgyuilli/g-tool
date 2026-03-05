"use client";

import { Plus } from "lucide-react";
import { useBookmarkContext } from "../BookmarkContext";
import { BookmarkCard } from "./BookmarkCard";
import { cn } from "@/lib/utils";

export function BookmarkGrid() {
  const { bookmarks, loading, setAddBookmarkOpen } = useBookmarkContext();

  if (loading) {
    return (
      <div className="p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-40 rounded-lg border bg-muted animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {/* Add bookmark card */}
        <button
          onClick={() => setAddBookmarkOpen(true)}
          className={cn(
            "flex flex-col items-center justify-center rounded-lg border-2 border-dashed",
            "hover:border-primary hover:bg-accent/50 transition-colors min-h-[10rem]",
            "text-muted-foreground hover:text-foreground"
          )}
        >
          <Plus className="h-8 w-8 mb-2" />
          <span className="text-sm font-medium">북마크 추가</span>
        </button>

        {/* Bookmark cards */}
        {bookmarks.map((bookmark) => (
          <BookmarkCard key={bookmark.id} bookmark={bookmark} />
        ))}
      </div>

      {/* Empty state */}
      {bookmarks.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-sm">북마크가 없습니다</p>
          <p className="text-xs mt-1">위 카드를 클릭하여 북마크를 추가하세요</p>
        </div>
      )}
    </div>
  );
}
