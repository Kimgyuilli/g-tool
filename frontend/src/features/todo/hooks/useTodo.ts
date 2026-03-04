import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type {
  Project,
  Task,
  ProjectCreateRequest,
  TaskCreateRequest,
  TaskUpdateRequest,
  ProjectsResponse,
  TasksResponse,
} from "@/features/todo/types";

interface UseTodoOptions {
  userId: number | null;
  enabled?: boolean;
}

export function useTodo({ userId, enabled = true }: UseTodoOptions) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const loadProjects = useCallback(async () => {
    if (!userId) return;
    try {
      const data = await apiFetch<ProjectsResponse>(
        `/api/todo/projects?user_id=${userId}`
      );
      setProjects(data.projects);
    } catch {
      setProjects([]);
    }
  }, [userId]);

  const loadTasks = useCallback(
    async (projectId: number) => {
      if (!userId) return;
      setLoading(true);
      try {
        const data = await apiFetch<TasksResponse>(
          `/api/todo/projects/${projectId}/tasks?user_id=${userId}`
        );
        setTasks(data.tasks);
      } catch {
        setTasks([]);
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  useEffect(() => {
    if (enabled && userId) {
      loadProjects();
    }
  }, [enabled, userId, loadProjects]);

  useEffect(() => {
    if (enabled && userId && selectedProjectId) {
      loadTasks(selectedProjectId);
    } else {
      setTasks([]);
    }
  }, [enabled, userId, selectedProjectId, loadTasks]);

  const selectProject = useCallback((id: number | null) => {
    setSelectedProjectId(id);
    setSelectedTaskId(null);
  }, []);

  const createProject = useCallback(
    async (data: ProjectCreateRequest) => {
      if (!userId) return null;
      const project = await apiFetch<Project>(
        `/api/todo/projects?user_id=${userId}`,
        { method: "POST", body: JSON.stringify(data) }
      );
      await loadProjects();
      setSelectedProjectId(project.id);
      return project;
    },
    [userId, loadProjects]
  );

  const updateProject = useCallback(
    async (projectId: number, data: Partial<ProjectCreateRequest>) => {
      if (!userId) return null;
      const project = await apiFetch<Project>(
        `/api/todo/projects/${projectId}?user_id=${userId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      );
      await loadProjects();
      return project;
    },
    [userId, loadProjects]
  );

  const deleteProject = useCallback(
    async (projectId: number) => {
      if (!userId) return;
      await apiFetch(`/api/todo/projects/${projectId}?user_id=${userId}`, {
        method: "DELETE",
      });
      if (selectedProjectId === projectId) {
        setSelectedProjectId(null);
        setSelectedTaskId(null);
      }
      await loadProjects();
    },
    [userId, selectedProjectId, loadProjects]
  );

  const createTask = useCallback(
    async (data: TaskCreateRequest) => {
      if (!userId) return null;
      const task = await apiFetch<Task>(
        `/api/todo/tasks?user_id=${userId}`,
        { method: "POST", body: JSON.stringify(data) }
      );
      if (selectedProjectId) {
        await loadTasks(selectedProjectId);
        await loadProjects();
      }
      return task;
    },
    [userId, selectedProjectId, loadTasks, loadProjects]
  );

  const updateTask = useCallback(
    async (taskId: number, data: TaskUpdateRequest) => {
      if (!userId) return null;
      const task = await apiFetch<Task>(
        `/api/todo/tasks/${taskId}?user_id=${userId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      );
      if (selectedProjectId) {
        await loadTasks(selectedProjectId);
      }
      return task;
    },
    [userId, selectedProjectId, loadTasks]
  );

  const deleteTask = useCallback(
    async (taskId: number) => {
      if (!userId) return;
      await apiFetch(`/api/todo/tasks/${taskId}?user_id=${userId}`, {
        method: "DELETE",
      });
      if (selectedTaskId === taskId) {
        setSelectedTaskId(null);
      }
      if (selectedProjectId) {
        await loadTasks(selectedProjectId);
        await loadProjects();
      }
    },
    [userId, selectedProjectId, selectedTaskId, loadTasks, loadProjects]
  );

  const selectedTask = tasks.find((t) => t.id === selectedTaskId) ?? null;

  return {
    projects,
    tasks,
    selectedProjectId,
    selectedTaskId,
    selectedTask,
    loading,
    selectProject,
    setSelectedTaskId,
    createProject,
    updateProject,
    deleteProject,
    createTask,
    updateTask,
    deleteTask,
    loadTasks,
    loadProjects,
  };
}
