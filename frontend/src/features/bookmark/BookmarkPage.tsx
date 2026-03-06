"use client";

import { BookmarkProvider } from "./BookmarkContext";
import { BookmarkCategorySidebar } from "./components/BookmarkCategorySidebar";
import { BookmarkGrid } from "./components/BookmarkGrid";
import { AddBookmarkModal } from "./components/AddBookmarkModal";
import { AddCategoryModal } from "./components/AddCategoryModal";

export function BookmarkPage() {
  return (
    <BookmarkProvider>
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-56 shrink-0 border-r overflow-auto hidden md:flex flex-col">
          <BookmarkCategorySidebar />
        </aside>
        <main className="flex-1 overflow-auto">
          <BookmarkGrid />
        </main>
      </div>
      <AddBookmarkModal />
      <AddCategoryModal />
    </BookmarkProvider>
  );
}
