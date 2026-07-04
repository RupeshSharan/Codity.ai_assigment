import { RotateCcw, Search } from "lucide-react";
import type { Job } from "../types/api";
import { StatusPill } from "./StatusPill";

export function JobTable({ jobs }: { jobs: Job[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-zinc-200 bg-white shadow-panel">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-ink">Job Explorer</h2>
        <div className="flex items-center gap-2">
          <button className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-zinc-200 text-zinc-600 hover:bg-zinc-100" title="Search jobs">
            <Search className="h-4 w-4" />
          </button>
          <button className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-zinc-200 text-zinc-600 hover:bg-zinc-100" title="Retry selected job">
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-200 text-sm">
          <thead className="bg-zinc-50 text-left text-xs uppercase tracking-normal text-zinc-500">
            <tr>
              <th className="px-4 py-3">Job</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Retries</th>
              <th className="px-4 py-3">Worker</th>
              <th className="px-4 py-3">Scheduled</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-zinc-50">
                <td className="px-4 py-3">
                  <div className="font-mono text-xs text-ink">{job.id.slice(0, 8)}</div>
                  <div className="mt-1 text-xs text-zinc-500">{job.tags.join(", ") || "untagged"}</div>
                </td>
                <td className="px-4 py-3">
                  <StatusPill value={job.status} />
                </td>
                <td className="px-4 py-3 text-zinc-700">{job.priority}</td>
                <td className="px-4 py-3 text-zinc-700">{job.retry_count}</td>
                <td className="px-4 py-3 text-zinc-700">{job.locked_by_worker_id ?? "-"}</td>
                <td className="px-4 py-3 text-zinc-700">{new Date(job.scheduled_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

