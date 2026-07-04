import { PauseCircle, PlayCircle } from "lucide-react";
import type { Queue } from "../types/api";
import { StatusPill } from "./StatusPill";

export function QueueTable({ queues }: { queues: Queue[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-zinc-200 bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-ink">Queues</h2>
        <span className="text-xs text-zinc-500">{queues.length} configured</span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-200 text-sm">
          <thead className="bg-zinc-50 text-left text-xs uppercase tracking-normal text-zinc-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Concurrency</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {queues.map((queue) => (
              <tr key={queue.id} className="hover:bg-zinc-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-ink">{queue.name}</div>
                  <div className="mt-1 max-w-md truncate text-xs text-zinc-500">{queue.description ?? "No description"}</div>
                </td>
                <td className="px-4 py-3">
                  <StatusPill value={queue.status} />
                </td>
                <td className="px-4 py-3 text-zinc-700">{queue.priority}</td>
                <td className="px-4 py-3 text-zinc-700">{queue.max_concurrency}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-zinc-200 text-zinc-600 hover:bg-zinc-100"
                    title={queue.status === "active" ? "Pause queue" : "Resume queue"}
                  >
                    {queue.status === "active" ? <PauseCircle className="h-4 w-4" /> : <PlayCircle className="h-4 w-4" />}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

