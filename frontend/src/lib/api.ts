import type {
  Project,
  ProjectCreate,
  ProjectListResponse,
  ProjectUpdate,
  PrioritizationResponse,
  GenerateTasksResponse,
  SuggestedTask,
  Task,
  TaskCreate,
  TaskListResponse,
  TaskUpdate,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Projects
export const projectsApi = {
  list: () => request<ProjectListResponse>("/api/projects"),
  get: (id: string) => request<Project>(`/api/projects/${id}`),
  create: (data: ProjectCreate) =>
    request<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: ProjectUpdate) =>
    request<Project>(`/api/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<void>(`/api/projects/${id}`, { method: "DELETE" }),
};

// Tasks
export const tasksApi = {
  list: (projectId: string) =>
    request<TaskListResponse>(`/api/projects/${projectId}/tasks`),
  get: (projectId: string, taskId: string) =>
    request<Task>(`/api/projects/${projectId}/tasks/${taskId}`),
  create: (projectId: string, data: TaskCreate) =>
    request<Task>(`/api/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (projectId: string, taskId: string, data: TaskUpdate) =>
    request<Task>(`/api/projects/${projectId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (projectId: string, taskId: string) =>
    request<void>(`/api/projects/${projectId}/tasks/${taskId}`, {
      method: "DELETE",
    }),
};

// Prioritization
export const prioritizeApi = {
  run: (projectId: string) =>
    request<PrioritizationResponse>(`/api/projects/${projectId}/prioritize`, {
      method: "POST",
    }),
};

// Task Generation
export const generateApi = {
  generate: (projectId: string) =>
    request<GenerateTasksResponse>(
      `/api/projects/${projectId}/generate-tasks`,
      { method: "POST" }
    ),
  accept: (projectId: string, tasks: SuggestedTask[]) =>
    request<TaskListResponse>(`/api/projects/${projectId}/accept-tasks`, {
      method: "POST",
      body: JSON.stringify({ tasks }),
    }),
};
