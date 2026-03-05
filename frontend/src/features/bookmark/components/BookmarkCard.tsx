"use client";

import { ExternalLink, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useBookmarkContext } from "../BookmarkContext";
import type { Bookmark } from "../types";
import { COLOR_DOT_MAP } from "../types";
import { cn } from "@/lib/utils";

interface BookmarkCardProps {
  bookmark: Bookmark;
}

function getDomain(url: string) {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

export function BookmarkCard({ bookmark }: BookmarkCardProps) {
  const { categories, setEditingBookmark, onDeleteBookmark } = useBookmarkContext();

  const category = categories.find((c) => c.id === bookmark.category_id);

  const handleEdit = () => {
    setEditingBookmark(bookmark);
  };

  const handleDelete = () => {
    if (confirm("북마크를 삭제하시겠습니까?")) {
      onDeleteBookmark(bookmark.id);
    }
  };

  const handleOpen = () => {
    window.open(bookmark.url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="group relative flex flex-col rounded-lg border bg-card p-4 hover:bg-accent/50 transition-colors">
      {/* Favicon and Title */}
      <div className="flex items-start gap-3 mb-2">
        {bookmark.favicon_url ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={bookmark.favicon_url}
            alt=""
            className="h-5 w-5 mt-0.5 shrink-0"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        ) : (
          <div className="h-5 w-5 rounded bg-muted shrink-0 mt-0.5" />
        )}
        <div className="flex-1 min-w-0">
          <h3
            className="font-medium text-sm line-clamp-2 cursor-pointer hover:underline"
            onClick={handleOpen}
          >
            {bookmark.title}
          </h3>
        </div>
      </div>

      {/* URL */}
      <p className="text-xs text-muted-foreground mb-2 truncate">
        {getDomain(bookmark.url)}
      </p>

      {/* Description */}
      {bookmark.description && (
        <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
          {bookmark.description}
        </p>
      )}

      {/* Category Badge */}
      {category && (
        <div className="mb-3">
          <Badge variant="secondary" className="text-xs">
            <span
              className={cn("inline-block h-2 w-2 rounded-full mr-1.5", COLOR_DOT_MAP[category.color])}
            />
            {category.name}
          </Badge>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-1 mt-auto pt-2 border-t opacity-0 group-hover:opacity-100 transition-opacity">
        <Button variant="ghost" size="sm" onClick={handleOpen}>
          <ExternalLink className="h-3.5 w-3.5" />
          <span className="ml-1 text-xs">열기</span>
        </Button>
        <Button variant="ghost" size="sm" onClick={handleEdit}>
          <Pencil className="h-3.5 w-3.5" />
          <span className="ml-1 text-xs">수정</span>
        </Button>
        <Button variant="ghost" size="sm" onClick={handleDelete}>
          <Trash2 className="h-3.5 w-3.5" />
          <span className="ml-1 text-xs">삭제</span>
        </Button>
      </div>
    </div>
  );
}
