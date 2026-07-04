import { useState, useEffect } from "react";
import { api, RetryPolicy } from "../services/api";
import type { Queue } from "../types/api";
import { StatusPill } from "../components/StatusPill";
import { PauseCircle, PlayCircle, Plus, AlertCircle, RefreshCw } from "lucide-react";

export function Queues({ projectId }: { projectId: string }) {
  const [queues, setQueues] = useState<Queue[]>([]);
  const [policies, setPolicies] = useState<RetryPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState(50);
  const [maxConcurrency, setMaxConcurrency] = useState(5);
  const [policyId, setPolicyId] = useState("");
  const [createLoading, setCreateLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [queuesData, policiesData] = await Promise.all([
        api.queues(projectId),
        api.retryPolicies(projectId)
      ]);
      setQueues(queuesData);
      setPolicies(policiesData);
    } catch (err: any) {
      setError(err.message || "Failed to load queues and policies.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  const handleToggleStatus = async (queue: Queue) => {
    try {
      if (queue.status === "active") {
        await api.pauseQueue(queue.id);
      } else {
        await api.resumeQueue(queue.id);
      }
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to toggle status");
    }
  };

  const handleCreateQueue = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      await api.createQueue({
        project_id: projectId,
        name,
        description: description || null,
        priority,
        max_concurrency: maxConcurrency,
        retry_policy_id: policyId || null
      });
      setShowCreate(false);
      setName("");
      setDescription("");
      setPriority(50);
      setMaxConcurrency(5);
      setPolicyId("");
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create queue");
    } finally {
      setCreateLoading(false);
    }
  };

  if (loading) {
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
          <h2 className="text-lg font-bold text-ink">Job Queues</h2>
          <p className="text-xs text-zinc-500">Configure parallel background processing lanes.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadData}
            className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-zinc-200 bg-white px-3 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md bg-pulse px-3 text-xs font-semibold text-white hover:bg-pulse/90"
          >
            <Plus className="h-3.5 w-3.5" />
            New Queue
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-md border border-red-200 bg-red-50 p-4 text-xs text-red-700">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {showCreate && (
        <div className="rounded-md border border-zinc-200 bg-white p-6 shadow-panel">
          <h3 className="text-sm font-semibold text-ink border-b pb-2 mb-4">Create Processing Queue</h3>
          <form onSubmit={handleCreateQueue} className="grid gap-4 md:grid-cols-2 text-xs">
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Queue Name</label>
              <input
                type="text"
                required
                placeholder="e.g. email-delivery"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Retry Policy (Optional)</label>
              <select
                value={policyId}
                onChange={(e) => setPolicyId(e.target.value)}
                className="block w-full rounded border border-zinc-300 bg-white p-2.5 text-ink focus:border-pulse focus:outline-none"
              >
                <option value="">Default (No Policy / Retries disabled)</option>
                {policies.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.strategy})
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Description</label>
              <textarea
                placeholder="Describe what background tasks this queue handles"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Priority (1-100)</label>
              <input
                type="number"
                min="1"
                max="100"
                required
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Max Concurrency</label>
              <input
                type="number"
                min="1"
                max="50"
                required
                value={maxConcurrency}
                onChange={(e) => setMaxConcurrency(Number(e.target.value))}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
            <div className="md:col-span-2 border-t pt-4 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="rounded border border-zinc-200 px-4 py-2 font-semibold text-zinc-700 hover:bg-zinc-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createLoading}
                className="rounded bg-pulse px-4 py-2 font-semibold text-white hover:bg-pulse/90 disabled:opacity-50"
              >
                {createLoading ? "Creating..." : "Save Queue"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="overflow-hidden rounded-md border border-zinc-200 bg-white shadow-panel">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200 text-sm">
            <thead className="bg-zinc-50 text-left text-xs uppercase tracking-normal text-zinc-500">
              <tr>
                <th className="px-6 py-3">Queue Information</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Priority</th>
                <th className="px-6 py-3">Concurrency Limit</th>
                <th className="px-6 py-3">Retry Policy</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {queues.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-zinc-500 italic">
                    No queues configured. Click "New Queue" to create one.
                  </td>
                </tr>
              ) : (
                queues.map((queue) => {
                  const policy = policies.find((p) => p.id === queue.retry_policy_id);
                  return (
                    <tr key={queue.id} className="hover:bg-zinc-50">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-ink">{queue.name}</div>
                        <div className="mt-1 max-w-sm truncate text-xs text-zinc-500">
                          {queue.description ?? "No description provided."}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <StatusPill value={queue.status} />
                      </td>
                      <td className="px-6 py-4 text-zinc-700 font-mono font-medium">{queue.priority}</td>
                      <td className="px-6 py-4 text-zinc-700 font-mono">{queue.max_concurrency} worker slots</td>
                      <td className="px-6 py-4 text-xs text-zinc-500">
                        {policy ? (
                          <span className="rounded bg-indigo-50 border border-indigo-100 px-2 py-1 text-indigo-700 font-medium">
                            {policy.name}
                          </span>
                        ) : (
                          <span className="text-zinc-400 italic">None</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleToggleStatus(queue)}
                          className={`inline-flex items-center gap-1 rounded border px-2.5 py-1 text-xs font-semibold hover:bg-zinc-50 ${
                            queue.status === "active"
                              ? "text-ember border-zinc-200"
                              : "text-emerald-700 border-zinc-200"
                          }`}
                          title={queue.status === "active" ? "Pause processing lane" : "Resume processing lane"}
                        >
                          {queue.status === "active" ? (
                            <>
                              <PauseCircle className="h-3.5 w-3.5" />
                              Pause
                            </>
                          ) : (
                            <>
                              <PlayCircle className="h-3.5 w-3.5" />
                              Resume
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
