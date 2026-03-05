"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useBookmarkContext } from "../BookmarkContext";
import type { Bookmark } from "../types";

interface FormFieldsProps {
  bookmark: Bookmark | null;
  categories: { id: number; name: string }[];
  onSubmit: (data: { title: string; url: string; description: string; categoryId: number | null }) => void;
  onClose: () => void;
  isEditing: boolean;
}

function FormFields({ bookmark, categories, onSubmit, onClose, isEditing }: FormFieldsProps) {
  const [title, setTitle] = useState(bookmark?.title ?? "");
  const [url, setUrl] = useState(bookmark?.url ?? "");
  const [description, setDescription] = useState(bookmark?.description ?? "");
  const [categoryId, setCategoryId] = useState<number | null>(bookmark?.category_id ?? null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !url.trim()) return;
    onSubmit({ title: title.trim(), url: url.trim(), description: description.trim(), categoryId });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4 py-4">
        <div className="space-y-2">
          <label htmlFor="title" className="text-sm font-medium">
            제목 <span className="text-destructive">*</span>
          </label>
          <Input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="북마크 제목"
            required
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="url" className="text-sm font-medium">
            URL <span className="text-destructive">*</span>
          </label>
          <Input
            id="url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="description" className="text-sm font-medium">
            설명
          </label>
          <Textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="북마크 설명 (선택사항)"
            rows={3}
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="category" className="text-sm font-medium">
            카테고리
          </label>
          <select
            id="category"
            value={categoryId ?? ""}
            onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : null)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <option value="">미분류</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>
          취소
        </Button>
        <Button type="submit" disabled={!title.trim() || !url.trim()}>
          {isEditing ? "수정" : "추가"}
        </Button>
      </DialogFooter>
    </form>
  );
}

export function AddBookmarkModal() {
  const {
    categories,
    addBookmarkOpen,
    setAddBookmarkOpen,
    editingBookmark,
    setEditingBookmark,
    onCreateBookmark,
    onUpdateBookmark,
  } = useBookmarkContext();

  const isEditing = !!editingBookmark;
  const isOpen = addBookmarkOpen || isEditing;

  const handleClose = () => {
    setAddBookmarkOpen(false);
    setEditingBookmark(null);
  };

  const handleFormSubmit = async (data: { title: string; url: string; description: string; categoryId: number | null }) => {
    if (isEditing) {
      await onUpdateBookmark(editingBookmark.id, {
        title: data.title,
        url: data.url,
        description: data.description || undefined,
        category_id: data.categoryId,
      });
    } else {
      await onCreateBookmark({
        title: data.title,
        url: data.url,
        description: data.description || undefined,
        category_id: data.categoryId,
      });
    }
    handleClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "북마크 수정" : "북마크 추가"}</DialogTitle>
        </DialogHeader>
        <FormFields
          key={editingBookmark?.id ?? "new"}
          bookmark={editingBookmark}
          categories={categories}
          onSubmit={handleFormSubmit}
          onClose={handleClose}
          isEditing={isEditing}
        />
      </DialogContent>
    </Dialog>
  );
}
