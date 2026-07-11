import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  Circle,
  Loader2,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  useCreateTask,
  useDeleteTask,
  usePrioritize,
  useProject,
  useTasks,
  useUpdateTask,
} from "@/hooks/use-api";
import type { PrioritizationResponse, Task } from "@/types";

const taskSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().max(2000).optional(),
  deadline: z.string().optional(),
});

type TaskForm = z.infer<typeof taskSchema>;

function quadrantLabel(q: string) {
  switch (q) {
    case "urgent-important": return "Do First";
    case "not-urgent-important": return "Schedule";
    case "urgent-not-important": return "Quick Win";
    case "not-urgent-not-important": return "Consider Dropping";
    default: return q;
  }
}

function quadrantVariant(q: string) {
  switch (q) {
    case "urgent-important": return "destructive" as const;
    case "not-urgent-important": return "default" as const;
    case "urgent-not-important": return "warning" as const;
    case "not-urgent-not-important": return "secondary" as const;
    default: return "outline" as const;
  }
}

export function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [showAddTask, setShowAddTask] = useState(false);
  const [prioritization, setPrioritization] = useState<PrioritizationResponse | null>(null);

  const { data: project, isLoading: projectLoading } = useProject(projectId!);
  const { data: tasksData, isLoading: tasksLoading } = useTasks(projectId!);
  const createTask = useCreateTask(projectId!);
  const updateTask = useUpdateTask(projectId!);
  const deleteTask = useDeleteTask(projectId!);
  const prioritize = usePrioritize(projectId!);

  const form = useForm<TaskForm>({
    resolver: zodResolver(taskSchema),
    defaultValues: { title: "", description: "", deadline: "" },
  });

  const onSubmitTask = async (values: TaskForm) => {
    const cleaned = {
      title: values.title,
      ...(values.description && { description: values.description }),
      ...(values.deadline && { deadline: values.deadline }),
    };
    await createTask.mutateAsync(cleaned);
    setShowAddTask(false);
    form.reset();
  };

  const toggleComplete = (task: Task) => {
    const newStatus = task.status === "completed" ? "pending" : "completed";
    updateTask.mutate({ taskId: task.taskId, data: { status: newStatus } });
  };

  const handlePrioritize = async () => {
    const result = await prioritize.mutateAsync();
    setPrioritization(result);
  };

  if (projectLoading) {
    return <div className="py-12 text-center text-muted-foreground">Loading...</div>;
  }

  if (!project) {
    return <div className="py-12 text-center text-muted-foreground">Project not found</div>;
  }

  const activeTasks = tasksData?.tasks.filter((t) => t.status !== "completed") ?? [];
  const completedTasks = tasksData?.tasks.filter((t) => t.status === "completed") ?? [];

  // Map prioritization data to tasks
  const priorityMap = new Map(
    prioritization?.recommendations.map((r) => [r.taskId, r]) ?? []
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Button variant="ghost" size="sm" className="mb-2 -ml-2" onClick={() => navigate("/projects")}>
          <ArrowLeft className="h-4 w-4" />
          Projects
        </Button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">{project.name}</h1>
            {project.objective && (
              <p className="mt-1 text-muted-foreground">{project.objective}</p>
            )}
            {project.deadline && (
              <div className="mt-2 flex items-center gap-1.5 text-sm text-muted-foreground">
                <CalendarDays className="h-3.5 w-3.5" />
                <span>Due {project.deadline}</span>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowAddTask(true)}>
              <Plus className="h-4 w-4" />
              Add Task
            </Button>
            <Button
              onClick={handlePrioritize}
              disabled={prioritize.isPending || activeTasks.length === 0}
            >
              {prioritize.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Prioritize
            </Button>
          </div>
        </div>
      </div>

      {/* AI Summary */}
      {prioritization && (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-primary" />
              M1 Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{prioritization.summary}</p>
          </CardContent>
        </Card>
      )}

      {/* Active Tasks */}
      <div className="space-y-3">
        <h2 className="text-lg font-medium">
          Active Tasks {!tasksLoading && `(${activeTasks.length})`}
        </h2>

        {tasksLoading ? (
          <p className="text-sm text-muted-foreground">Loading tasks...</p>
        ) : activeTasks.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-muted-foreground">No active tasks. Add one to get started.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {activeTasks
              .sort((a, b) => {
                const pa = priorityMap.get(a.taskId)?.priorityScore ?? 0;
                const pb = priorityMap.get(b.taskId)?.priorityScore ?? 0;
                return pb - pa;
              })
              .map((task) => {
                const pri = priorityMap.get(task.taskId);
                return (
                  <Card key={task.taskId} className="transition-colors hover:bg-accent/30">
                    <CardContent className="flex items-start gap-3 p-4">
                      <button
                        onClick={() => toggleComplete(task)}
                        className="mt-0.5 text-muted-foreground hover:text-primary transition-colors"
                        aria-label={`Mark "${task.title}" complete`}
                      >
                        <Circle className="h-5 w-5" />
                      </button>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{task.title}</span>
                          {pri && (
                            <Badge variant={quadrantVariant(pri.quadrant)}>
                              {quadrantLabel(pri.quadrant)}
                            </Badge>
                          )}
                          {pri && (
                            <span className="text-xs text-muted-foreground">
                              Score: {pri.priorityScore}
                            </span>
                          )}
                        </div>
                        {task.description && (
                          <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                            {task.description}
                          </p>
                        )}
                        {pri && (
                          <div className="mt-2 space-y-1">
                            <p className="text-xs text-muted-foreground">
                              <span className="font-medium">Why:</span> {pri.reason}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              <span className="font-medium">Next:</span> {pri.nextAction}
                            </p>
                          </div>
                        )}
                        {task.deadline && (
                          <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                            <CalendarDays className="h-3 w-3" />
                            {task.deadline}
                          </div>
                        )}
                      </div>

                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-destructive"
                        onClick={() => deleteTask.mutate(task.taskId)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
          </div>
        )}
      </div>

      {/* Completed Tasks */}
      {completedTasks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-medium text-muted-foreground">
            Completed ({completedTasks.length})
          </h2>
          <div className="space-y-2">
            {completedTasks.map((task) => (
              <Card key={task.taskId} className="opacity-60">
                <CardContent className="flex items-center gap-3 p-4">
                  <button
                    onClick={() => toggleComplete(task)}
                    className="text-emerald-500 hover:text-muted-foreground transition-colors"
                    aria-label={`Mark "${task.title}" incomplete`}
                  >
                    <CheckCircle2 className="h-5 w-5" />
                  </button>
                  <span className="font-medium line-through">{task.title}</span>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Add Task Dialog */}
      <Dialog open={showAddTask} onOpenChange={setShowAddTask}>
        <DialogContent onClose={() => setShowAddTask(false)}>
          <DialogHeader>
            <DialogTitle>Add Task</DialogTitle>
          </DialogHeader>
          <form onSubmit={form.handleSubmit(onSubmitTask)} className="mt-4 space-y-4">
            <div className="space-y-2">
              <label htmlFor="title" className="text-sm font-medium">Title *</label>
              <Input id="title" placeholder="What needs to be done?" {...form.register("title")} />
              {form.formState.errors.title && (
                <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <label htmlFor="task-description" className="text-sm font-medium">Description</label>
              <Textarea id="task-description" placeholder="Details..." {...form.register("description")} />
            </div>
            <div className="space-y-2">
              <label htmlFor="task-deadline" className="text-sm font-medium">Deadline</label>
              <Input id="task-deadline" type="date" {...form.register("deadline")} />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowAddTask(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={createTask.isPending}>
                {createTask.isPending ? "Adding..." : "Add Task"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
