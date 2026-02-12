"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { AgentTask } from "@/types/agents";

export function useAgentTask(taskId: string | null) {
  const [task, setTask] = useState<AgentTask | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const poll = useCallback(async () => {
    if (!taskId) return;

    try {
      const res = await api.get(`/agents/tasks/${taskId}`);
      const result = res.data as AgentTask;
      setTask(result);

      if (result.status === "completed" || result.status === "failed") {
        setIsPolling(false);
      }
    } catch {
      setIsPolling(false);
    }
  }, [taskId]);

  useEffect(() => {
    if (!taskId) return;

    setIsPolling(true);
    poll();
    const interval = setInterval(poll, 2000);

    return () => clearInterval(interval);
  }, [taskId, poll]);

  return { task, isPolling };
}
