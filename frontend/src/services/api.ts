import type { Job, OverviewMetrics, Queue, Worker, QueueStatus, JobStatus, WorkerStatus } from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("pulsequeue_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...headers,
      ...options?.headers
    }
  });

  if (!response.ok) {
    let errorDetail = "";
    try {
      const data = await response.json();
      errorDetail = data.detail || response.statusText;
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail || `API request failed: ${response.status}`);
  }

  // Handle empty or 204 responses
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export interface RetryPolicy {
  id: string;
  project_id: string;
  name: string;
  strategy: "fixed" | "linear" | "exponential";
  max_attempts: number;
  delay_seconds: number;
  max_delay_seconds: number;
}

export interface JobDetailResponse {
  job: Job;
  executions: Array<{
    id: string;
    job_id: string;
    worker_id: string | null;
    attempt_number: number;
    status: string;
    started_at: string;
    completed_at: string | null;
    duration_ms: number | null;
    error: string | null;
    result: Record<string, any> | null;
  }>;
  logs: Array<{
    id: string;
    job_id: string;
    level: string;
    message: string;
    context: Record<string, any>;
    created_at: string;
  }>;
}

export const api = {
  // Auth API
  register: (payload: any) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  login: (payload: any) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  me: () => request<any>("/auth/me"),

  // Organizations & Projects API
  organizations: () => request<any[]>("/organizations"),

  createOrganization: (name: string) =>
    request<any>("/organizations", {
      method: "POST",
      body: JSON.stringify({ name })
    }),

  projects: (orgId: string) => request<any[]>(`/organizations/${orgId}/projects`),

  createProject: (orgId: string, name: string, description?: string) =>
    request<any>(`/organizations/${orgId}/projects`, {
      method: "POST",
      body: JSON.stringify({ name, description })
    }),

  // Queues API
  overview: () => request<OverviewMetrics>("/metrics/overview"),

  queues: (projectId: string) => request<Queue[]>(`/queues?project_id=${projectId}`),

  createQueue: (payload: any) =>
    request<Queue>("/queues", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  pauseQueue: (queueId: string) =>
    request<Queue>(`/queues/${queueId}/pause`, { method: "POST" }),

  resumeQueue: (queueId: string) =>
    request<Queue>(`/queues/${queueId}/resume`, { method: "POST" }),

  // Retry Policies API
  retryPolicies: (projectId: string) =>
    request<RetryPolicy[]>(`/queues/retry-policies/${projectId}`),

  createRetryPolicy: (projectId: string, payload: any) =>
    request<RetryPolicy>(`/queues/retry-policies/${projectId}`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  // Jobs API
  jobs: (
    projectId: string,
    filters?: {
      queue_id?: string;
      worker_id?: string;
      status?: JobStatus;
      tag?: string;
      limit?: number;
      offset?: number;
    }
  ) => {
    const params = new URLSearchParams({ project_id: projectId });
    if (filters?.queue_id) params.append("queue_id", filters.queue_id);
    if (filters?.worker_id) params.append("worker_id", filters.worker_id);
    if (filters?.status) params.append("status", filters.status);
    if (filters?.tag) params.append("tag", filters.tag);
    if (filters?.limit) params.append("limit", filters.limit.toString());
    if (filters?.offset) params.append("offset", filters.offset.toString());
    return request<{ items: Job[]; total: number }>(`/jobs?${params.toString()}`);
  },

  submitJob: (payload: any) =>
    request<Job>("/jobs", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  jobDetails: (jobId: string) => request<JobDetailResponse>(`/jobs/${jobId}`),

  retryJob: (jobId: string) => request<Job>(`/jobs/${jobId}/retry`, { method: "POST" }),

  // Workers API
  workers: () => request<Worker[]>("/workers")
};
