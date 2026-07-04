import { useState, useEffect } from "react";
import { api, RetryPolicy } from "../services/api";
import { ShieldCheck, Plus, RefreshCw, AlertCircle } from "lucide-react";

export function Policies({ projectId }: { projectId: string }) {
  const [policies, setPolicies] = useState<RetryPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [strategy, setStrategy] = useState<"fixed" | "linear" | "exponential">("exponential");
  const [maxAttempts, setMaxAttempts] = useState(3);
  const [delaySeconds, setDelaySeconds] = useState(30);
  const [maxDelaySeconds, setMaxDelaySeconds] = useState(3600);
  const [createLoading, setCreateLoading] = useState(false);

  const loadPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.retryPolicies(projectId);
      setPolicies(data);
    } catch (err: any) {
      setError(err.message || "Failed to load retry policies.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, [projectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      await api.createRetryPolicy(projectId, {
        name,
        strategy,
        max_attempts: maxAttempts,
        delay_seconds: delaySeconds,
        max_delay_seconds: maxDelaySeconds
      });
      setShowCreate(false);
      setName("");
      setStrategy("exponential");
      setMaxAttempts(3);
      setDelaySeconds(30);
      setMaxDelaySeconds(3600);
      loadPolicies();
    } catch (err: any) {
      alert(err.message || "Failed to create policy");
    } finally {
      setCreateLoading(false);
    }
  };

  if (loading && policies.length === 0) {
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
          <h2 className="text-lg font-bold text-ink">Retry Policies</h2>
          <p className="text-xs text-zinc-500">Define backoff behaviors for handling temporary execution failures.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadPolicies}
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
            New Policy
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded bg-red-50 p-4 text-xs text-red-700">
          {error}
        </div>
      )}

      {showCreate && (
        <div className="rounded-md border border-zinc-200 bg-white p-6 shadow-panel">
          <h3 className="text-sm font-semibold text-ink border-b pb-2 mb-4">Create Retry Policy</h3>
          <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2 text-xs">
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Policy Name</label>
              <input
                type="text"
                required
                placeholder="e.g. exponential-backoff"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Backoff Strategy</label>
              <select
                value={strategy}
                onChange={(e: any) => setStrategy(e.target.value)}
                className="block w-full rounded border border-zinc-300 bg-white p-2.5 text-ink focus:border-pulse focus:outline-none"
              >
                <option value="fixed">Fixed Delay</option>
                <option value="linear">Linear Backoff</option>
                <option value="exponential">Exponential Backoff</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Max Attempts</label>
              <input
                type="number"
                min="1"
                max="25"
                required
                value={maxAttempts}
                onChange={(e) => setMaxAttempts(Number(e.target.value))}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Initial Delay (seconds)</label>
              <input
                type="number"
                min="1"
                required
                value={delaySeconds}
                onChange={(e) => setDelaySeconds(Number(e.target.value))}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-semibold text-zinc-500 uppercase mb-1">Maximum Delay (seconds)</label>
              <input
                type="number"
                min="1"
                required
                value={maxDelaySeconds}
                onChange={(e) => setMaxDelaySeconds(Number(e.target.value))}
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
                {createLoading ? "Creating..." : "Save Policy"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {policies.length === 0 ? (
          <div className="col-span-full rounded-md border border-dashed border-zinc-300 bg-white py-12 text-center text-zinc-500 italic text-sm">
            No custom retry policies configured yet.
          </div>
        ) : (
          policies.map((policy) => (
            <div key={policy.id} className="rounded-md border border-zinc-200 bg-white p-5 shadow-panel flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <div className="rounded bg-indigo-50 p-1.5 text-indigo-600">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-ink text-sm">{policy.name}</h4>
                    <p className="text-[10px] text-zinc-400 font-mono mt-0.5">ID: {policy.id.slice(0, 8)}...</p>
                  </div>
                </div>

                <div className="mt-4 border-t border-zinc-100 pt-4 space-y-2.5 text-xs text-zinc-600">
                  <div className="flex items-center justify-between">
                    <span>Backoff Algorithm</span>
                    <span className="rounded bg-zinc-100 px-2 py-0.5 font-semibold text-zinc-800 uppercase text-[10px]">
                      {policy.strategy}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Maximum Retry Attempts</span>
                    <span className="font-semibold text-ink">{policy.max_attempts} attempts</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Initial Delay</span>
                    <span className="font-semibold text-ink">{policy.delay_seconds} seconds</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Max Interval Cap</span>
                    <span className="font-semibold text-ink">{policy.max_delay_seconds} seconds</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
