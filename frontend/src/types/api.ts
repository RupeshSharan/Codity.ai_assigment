export type QueueStatus = "active" | "paused";
export type JobStatus = "queued" | "scheduled" | "claimed" | "running" | "completed" | "failed" | "dead_letter";
export type WorkerStatus = "online" | "draining" | "offline";

export interface OverviewMetrics {
  running_jobs: number;
  queued_jobs: number;
  failed_jobs: number;
  completed_jobs: number;
  workers_online: number;
  queue_health: Record<string, number>;
  retry_rate_percent: number;
  average_execution_ms: number | null;
}

export interface Queue {
  id: string;
  project_id: string;
  retry_policy_id?: string | null;
  name: string;
  description: string | null;
  priority: number;
  max_concurrency: number;
  status: QueueStatus;
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: string;
  queue_id: string;
  status: JobStatus;
  priority: number;
  retry_count: number;
  locked_by_worker_id: string | null;
  scheduled_at: string;
  completed_at: string | null;
  last_error: string | null;
  payload: Record<string, unknown>;
  job_metadata?: Record<string, unknown> | null;
  tags: string[];
}

export interface Worker {
  id: string;
  hostname: string;
  queues: string[];
  status: WorkerStatus;
  active_jobs: number;
  version: string;
  last_heartbeat_at: string;
}

