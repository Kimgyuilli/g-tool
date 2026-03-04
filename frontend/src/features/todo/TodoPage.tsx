"use client";

import { useTodo } from "@/features/todo/hooks/useTodo";
import { useSubtasks } from "@/features/todo/hooks/useSubtasks";
import { ProjectSidebar } from "@/features/todo/components/ProjectSidebar";
import { TaskListView } from "@/features/todo/components/TaskListView";
import { TaskDetailView } from "@/features/todo/components/TaskDetailView";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { toast } from "sonner";

interface TodoPageProps {
  userId: number | null;
}

export function TodoPage({ userId }: TodoPageProps) {
  const {
    projects,
    tasks,
    selectedProjectId,
    selectedTask,
    selectProject,
    setSelectedTaskId,
    createProject,
    deleteProject,
    createTask,
    updateTask,
    deleteTask,
  } = useTodo({ userId, enabled: true });

  const { subtasks, createSubtask, toggleSubtask, deleteSubtask } =
    useSubtasks({ userId, taskId: selectedTask?.id ?? null });

  const selectedProject = projects.find((p) => p.id === selectedProjectId);

  const handleCreateProject = async (name: string) => {
    try {
      await createProject({ name });
      toast.success("프로젝트가 생성되었습니다");
    } catch {
      toast.error("프로젝트 생성에 실패했습니다");
    }
  };

  const handleDeleteProject = async (id: number) => {
    try {
      await deleteProject(id);
      toast.success("프로젝트가 삭제되었습니다");
    } catch {
      toast.error("프로젝트 삭제에 실패했습니다");
    }
  };

  const handleCreateTask = async (title: string) => {
    if (!selectedProjectId) return;
    try {
      await createTask({ project_id: selectedProjectId, title });
    } catch {
      toast.error("태스크 생성에 실패했습니다");
    }
  };

  const handleToggleStatus = async (taskId: number, currentStatus: string) => {
    const next = currentStatus === "done" ? "todo" : "done";
    try {
      await updateTask(taskId, { status: next });
    } catch {
      toast.error("상태 변경에 실패했습니다");
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    try {
      await deleteTask(taskId);
      toast.success("태스크가 삭제되었습니다");
    } catch {
      toast.error("태스크 삭제에 실패했습니다");
    }
  };

  const handleCreateSubtask = async (title: string) => {
    if (!selectedTask) return;
    try {
      await createSubtask({ task_id: selectedTask.id, title });
    } catch {
      toast.error("서브태스크 생성에 실패했습니다");
    }
  };

  return (
    <div className="flex-1 overflow-hidden flex">
      {/* Project sidebar */}
      <aside className="hidden md:flex w-56 shrink-0 border-r overflow-auto">
        <ProjectSidebar
          projects={projects}
          selectedProjectId={selectedProjectId}
          onSelectProject={selectProject}
          onCreateProject={handleCreateProject}
          onDeleteProject={handleDeleteProject}
        />
      </aside>

      <ResizablePanelGroup orientation="horizontal" className="flex-1">
        {/* Task list */}
        <ResizablePanel
          defaultSize={selectedTask ? 50 : 100}
          minSize={30}
        >
          {selectedProject ? (
            <TaskListView
              tasks={tasks}
              selectedTaskId={selectedTask?.id ?? null}
              projectName={selectedProject.name}
              onSelectTask={setSelectedTaskId}
              onCreateTask={handleCreateTask}
              onToggleStatus={handleToggleStatus}
              onDeleteTask={handleDeleteTask}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              프로젝트를 선택하세요
            </div>
          )}
        </ResizablePanel>

        {/* Task detail */}
        {selectedTask && (
          <>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={50} minSize={25}>
              <TaskDetailView
                task={selectedTask}
                subtasks={subtasks}
                onClose={() => setSelectedTaskId(null)}
                onUpdateTask={async (taskId, data) => {
                  try {
                    await updateTask(taskId, data);
                  } catch {
                    toast.error("태스크 수정에 실패했습니다");
                  }
                }}
                onCreateSubtask={handleCreateSubtask}
                onToggleSubtask={toggleSubtask}
                onDeleteSubtask={deleteSubtask}
              />
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>
    </div>
  );
}
