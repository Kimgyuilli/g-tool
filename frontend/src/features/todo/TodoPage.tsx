"use client";

import { TodoProvider } from "@/features/todo/TodoContext";
import { KanbanBoard } from "@/features/todo/components/KanbanBoard";

interface TodoPageProps {
  userId: number | null;
}

export function TodoPage({ userId }: TodoPageProps) {
  return (
    <TodoProvider userId={userId}>
      <KanbanBoard />
    </TodoProvider>
  );
}
