import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { prioritizeApi, projectsApi, tasksApi, generateApi } from "@/lib/api";
import type {
  ProjectCreate,
  ProjectUpdate,
  SuggestedTask,
  TaskCreate,
  TaskUpdate,
} from "@/types";

// --- Projects ---

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: projectsApi.list,
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ["projects", id],
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectUpdate) => projectsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      qc.invalidateQueries({ queryKey: ["projects", id] });
    },
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

// --- Tasks ---

export function useTasks(projectId: string) {
  return useQuery({
    queryKey: ["tasks", projectId],
    queryFn: () => tasksApi.list(projectId),
    enabled: !!projectId,
  });
}

export function useCreateTask(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) => tasksApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });
}

export function useUpdateTask(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: TaskUpdate }) =>
      tasksApi.update(projectId, taskId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });
}

export function useDeleteTask(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => tasksApi.delete(projectId, taskId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });
}

// --- Prioritization ---

export function usePrioritize(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => prioritizeApi.run(projectId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });
}

// --- All Tasks (across projects) ---

export function useAllTasks(projectIds: string[]) {
  return useQueries({
    queries: projectIds.map((id) => ({
      queryKey: ["tasks", id],
      queryFn: () => tasksApi.list(id),
      enabled: !!id,
    })),
  });
}

// --- Task Generation ---

export function useGenerateTasks(projectId: string) {
  return useMutation({
    mutationFn: () => generateApi.generate(projectId),
  });
}

export function useAcceptTasks(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (tasks: SuggestedTask[]) =>
      generateApi.accept(projectId, tasks),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks", projectId] }),
  });
}
