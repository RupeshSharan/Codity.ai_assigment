import { ServerCog } from "lucide-react";
import type { Worker } from "../types/api";
import { StatusPill } from "./StatusPill";

export function WorkerPanel({ workers }: { workers: Worker[] }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white p-4 shadow-panel">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-ink">Workers</h2>
        <ServerCog className="h-4 w-4 text-pulse" />
      </div>
      <div className="mt-4 space-y-3">
        {workers.map((worker) => (
          <div key={worker.id} className="rounded-md border border-zinc-100 bg-zinc-50 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="truncate font-mono text-xs text-ink">{worker.id}</span>
              <StatusPill value={worker.status} />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-zinc-600">
              <span>{worker.hostname}</span>
              <span className="text-right">{worker.active_jobs} active</span>
              <span>{worker.version}</span>
              <span className="text-right">{new Date(worker.last_heartbeat_at).toLocaleTimeString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

