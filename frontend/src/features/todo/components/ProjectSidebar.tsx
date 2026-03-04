"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Trash2, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Project } from "@/features/todo/types";

interface ProjectSidebarProps {
  projects: Project[];
  selectedProjectId: number | null;
  onSelectProject: (id: number | null) => void;
  onCreateProject: (name: string) => void;
  onDeleteProject: (id: number) => void;
}

export function ProjectSidebar({
  projects,
  selectedProjectId,
  onSelectProject,
  onCreateProject,
  onDeleteProject,
}: ProjectSidebarProps) {
  const [showInput, setShowInput] = useState(false);
  const [newName, setNewName] = useState("");

  const handleCreate = () => {
    const name = newName.trim();
    if (!name) return;
    onCreateProject(name);
    setNewName("");
    setShowInput(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => setShowInput(true)}
        >
          <Plus className="h-4 w-4 mr-1" />
          새 프로젝트
        </Button>
      </div>

      {showInput && (
        <div className="p-2 border-b">
          <Input
            autoFocus
            placeholder="프로젝트 이름"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
              if (e.key === "Escape") {
                setShowInput(false);
                setNewName("");
              }
            }}
            onBlur={() => {
              if (!newName.trim()) {
                setShowInput(false);
              }
            }}
          />
        </div>
      )}

      <nav className="flex-1 overflow-auto p-1">
        {projects.length === 0 && !showInput && (
          <p className="text-xs text-muted-foreground text-center py-8">
            프로젝트가 없습니다
          </p>
        )}
        {projects.map((project) => (
          <div
            key={project.id}
            className={cn(
              "group flex items-center gap-2 rounded-md px-2 py-1.5 text-sm cursor-pointer hover:bg-accent",
              selectedProjectId === project.id && "bg-accent"
            )}
            onClick={() => onSelectProject(project.id)}
          >
            <span
              className="h-2.5 w-2.5 rounded-full shrink-0"
              style={{ backgroundColor: project.color || "#6b7280" }}
            />
            <FolderOpen className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="flex-1 truncate">{project.name}</span>
            <span className="text-xs text-muted-foreground">
              {project.task_count}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 opacity-0 group-hover:opacity-100"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteProject(project.id);
              }}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        ))}
      </nav>
    </div>
  );
}
