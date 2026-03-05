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
import { useBookmarkContext } from "../BookmarkContext";
import { CATEGORY_COLORS } from "../types";
import { cn } from "@/lib/utils";

export function AddCategoryModal() {
  const { addCategoryOpen, setAddCategoryOpen, onCreateCategory } = useBookmarkContext();

  const [name, setName] = useState("");
  const [color, setColor] = useState("blue");

  const handleClose = () => {
    setAddCategoryOpen(false);
    setName("");
    setColor("blue");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    await onCreateCategory({
      name: name.trim(),
      color,
    });
    handleClose();
  };

  return (
    <Dialog open={addCategoryOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>카테고리 추가</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium">
                이름 <span className="text-destructive">*</span>
              </label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="카테고리 이름"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">색상</label>
              <div className="grid grid-cols-4 gap-3">
                {CATEGORY_COLORS.map((c) => (
                  <button
                    key={c.value}
                    type="button"
                    onClick={() => setColor(c.value)}
                    className={cn(
                      "flex flex-col items-center gap-2 p-3 rounded-md border-2 transition-colors",
                      color === c.value
                        ? "border-primary bg-accent"
                        : "border-transparent hover:border-muted-foreground/30"
                    )}
                  >
                    <span className={cn("h-6 w-6 rounded-full", c.class)} />
                    <span className="text-xs">{c.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              취소
            </Button>
            <Button type="submit" disabled={!name.trim()}>
              추가
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
