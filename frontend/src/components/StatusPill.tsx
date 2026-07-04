import type { JobStatus, QueueStatus, WorkerStatus } from "../types/api";

const styles: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  online: "bg-emerald-50 text-emerald-700 border-emerald-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  queued: "bg-sky-50 text-sky-700 border-sky-200",
  scheduled: "bg-indigo-50 text-indigo-700 border-indigo-200",
  claimed: "bg-amber-50 text-amber-700 border-amber-200",
  running: "bg-teal-50 text-teal-700 border-teal-200",
  paused: "bg-stone-100 text-stone-700 border-stone-200",
  draining: "bg-amber-50 text-amber-700 border-amber-200",
  failed: "bg-rose-50 text-rose-700 border-rose-200",
  dead_letter: "bg-red-50 text-red-700 border-red-200",
  offline: "bg-zinc-100 text-zinc-600 border-zinc-200"
};

export function StatusPill({ value }: { value: QueueStatus | JobStatus | WorkerStatus }) {
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${styles[value]}`}>
      {value.replace("_", " ")}
    </span>
  );
}

