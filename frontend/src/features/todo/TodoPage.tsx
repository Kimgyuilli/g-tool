"use client";

import { TodoProvider } from "@/features/todo/TodoContext";
import { KanbanBoard } from "@/features/todo/components/KanbanBoard";

export function TodoPage() {
  return (
    <TodoProvider>
      <KanbanBoard />
    </TodoProvider>
  );
}
