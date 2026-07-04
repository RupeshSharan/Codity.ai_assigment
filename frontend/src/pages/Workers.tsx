import { useState, useEffect } from "react";
import { api } from "../services/api";
import type { Worker } from "../types/api";
import { StatusPill } from "../components/StatusPill";
import { Server, Activity, Cpu, RefreshCw, Layers } from "lucide-react";

export function Workers() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadWorkers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.workers();
      setWorkers(data);
    } catch (err: any) {
      setError(err.message || "Failed to load workers list.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkers();
    const timer = setInterval(loadWorkers, 5000); // Poll workers list every 5 seconds
    return () => clearInterval(timer);
  }, []);

  if (loading && workers.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-pulse border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">Worker Instances</h2>
          <p className="text-xs text-zinc-500">Monitor distributed worker health, heartbeat latency, and task distribution.</p>
        </div>
        <button
          onClick={loadWorkers}
          className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-zinc-200 bg-white px-3 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded bg-red-50 p-4 text-xs text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {workers.length === 0 ? (
          <div className="col-span-full rounded-md border border-dashed border-zinc-300 bg-white py-12 text-center text-zinc-500 italic text-sm">
            No worker nodes currently registered.
          </div>
        ) : (
          workers.map((worker) => (
            <div
              key={worker.id}
              className={`rounded-md border bg-white p-5 shadow-panel flex flex-col justify-between ${
                worker.status === "online" ? "border-zinc-200" :
                worker.status === "draining" ? "border-amber-200 bg-amber-50/10" :
                "border-zinc-200 opacity-60"
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <div className={`rounded p-1.5 ${
                      worker.status === "online" ? "bg-emerald-50 text-emerald-600" :
                      worker.status === "draining" ? "bg-amber-50 text-amber-600" :
                      "bg-zinc-100 text-zinc-500"
                    }`}>
                      <Server className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="font-mono text-xs font-semibold text-ink truncate max-w-[150px]" title={worker.id}>
                        {worker.id}
                      </h4>
                      <p className="text-[10px] text-zinc-500 mt-0.5">Hostname: {worker.hostname}</p>
                    </div>
                  </div>
                  <StatusPill value={worker.status} />
                </div>

                <div className="mt-4 border-t border-zinc-100 pt-4 space-y-2.5 text-xs text-zinc-600">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1"><Activity className="h-3.5 w-3.5 text-zinc-400" /> Active Threads</span>
                    <span className="font-semibold text-ink">{worker.active_jobs} running</span>
                  </div>
                  <div className="flex items-start justify-between">
                    <span className="flex items-center gap-1 mt-0.5"><Layers className="h-3.5 w-3.5 text-zinc-400" /> Subscribed Queues</span>
                    <div className="flex flex-wrap gap-1 justify-end max-w-[150px]">
                      {worker.queues.length === 0 ? (
                        <span className="text-zinc-400 italic text-[10px]">None</span>
                      ) : (
                        worker.queues.map((q) => (
                          <span key={q} className="rounded bg-zinc-100 border border-zinc-200 px-1 py-0.5 text-[9px] font-mono text-zinc-700">
                            {q.slice(0, 10)}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1"><Cpu className="h-3.5 w-3.5 text-zinc-400" /> Engine Version</span>
                    <span className="font-semibold text-zinc-800">{worker.version}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 border-t border-zinc-100 pt-3 text-[10px] text-zinc-400 flex items-center justify-between">
                <span>Heartbeat: {new Date(worker.last_heartbeat_at).toLocaleTimeString()}</span>
                {worker.status === "online" && (
                  <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
