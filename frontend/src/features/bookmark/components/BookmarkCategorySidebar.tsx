"use client";

import { Plus, Trash2, FolderOpen, Folder } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useBookmarkContext } from "../BookmarkContext";
import { COLOR_DOT_MAP } from "../types";
import { cn } from "@/lib/utils";

export function BookmarkCategorySidebar() {
  const {
    categories,
    bookmarks,
    selectedCategoryId,
    onSelectCategory,
    onDeleteCategory,
    setAddCategoryOpen,
  } = useBookmarkContext();

  const totalCount = bookmarks.length;
  const uncategorizedCount = bookmarks.filter((b) => b.category_id === null).length;

  const handleDeleteCategory = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("카테고리를 삭제하시겠습니까? (북마크는 미분류로 이동됩니다)")) {
      onDeleteCategory(id);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="font-semibold text-sm">북마크</h2>
      </div>

      {/* Filters */}
      <div className="flex-1 overflow-auto p-2">
        {/* All */}
        <button
          onClick={() => onSelectCategory(null)}
          className={cn(
            "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
            selectedCategoryId === null
              ? "bg-accent text-accent-foreground font-medium"
              : "hover:bg-accent/50"
          )}
        >
          <FolderOpen className="h-4 w-4" />
          <span className="flex-1 text-left">전체</span>
          <span className="text-xs text-muted-foreground">{totalCount}</span>
        </button>

        {/* Uncategorized */}
        <button
          onClick={() => onSelectCategory(-1)}
          className={cn(
            "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
            selectedCategoryId === -1
              ? "bg-accent text-accent-foreground font-medium"
              : "hover:bg-accent/50"
          )}
        >
          <Folder className="h-4 w-4" />
          <span className="flex-1 text-left">미분류</span>
          <span className="text-xs text-muted-foreground">{uncategorizedCount}</span>
        </button>

        {/* Categories */}
        <div className="mt-4 space-y-0.5">
          <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground">
            카테고리
          </div>
          {categories.map((category) => (
            <div
              key={category.id}
              className={cn(
                "group flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
                selectedCategoryId === category.id
                  ? "bg-accent text-accent-foreground font-medium"
                  : "hover:bg-accent/50"
              )}
            >
              <button
                onClick={() => onSelectCategory(category.id)}
                className="flex-1 flex items-center gap-2 text-left"
              >
                <span
                  className={cn("inline-block h-3 w-3 rounded-full shrink-0", COLOR_DOT_MAP[category.color])}
                />
                <span className="flex-1 truncate">{category.name}</span>
                <span className="text-xs text-muted-foreground">{category.bookmark_count}</span>
              </button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                onClick={(e) => handleDeleteCategory(category.id, e)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Add category button */}
      <div className="p-3 border-t">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => setAddCategoryOpen(true)}
        >
          <Plus className="h-4 w-4" />
          <span className="ml-1.5">카테고리 추가</span>
        </Button>
      </div>
    </div>
  );
}
