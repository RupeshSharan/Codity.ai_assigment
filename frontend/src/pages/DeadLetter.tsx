import { useState, useEffect } from "react";
import { api } from "../services/api";
import type { Job } from "../types/api";
import { JobDetailDrawer } from "../components/JobDetailDrawer";
import { AlertTriangle, RefreshCw, Eye, Calendar, Clock } from "lucide-react";

export function DeadLetter({ projectId }: { projectId: string }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const loadDLQ = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch jobs with status 'dead_letter'
      const data = await api.jobs(projectId, { status: "dead_letter", limit: 50 });
      setJobs(data.items);
    } catch (err: any) {
      setError(err.message || "Failed to load dead letter queue.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDLQ();
  }, [projectId]);

  const handleRequeue = async (jobId: string) => {
    setActionLoadingId(jobId);
    try {
      await api.retryJob(jobId);
      loadDLQ();
    } catch (err: any) {
      alert(err.message || "Failed to requeue job");
    } finally {
      setActionLoadingId(null);
    }
  };

  if (loading && jobs.length === 0) {
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
          <h2 className="text-lg font-bold text-ink">Dead Letter Queue (DLQ)</h2>
          <p className="text-xs text-zinc-500">Inspect jobs that exhausted all retry policies and failed permanently.</p>
        </div>
        <button
          onClick={loadDLQ}
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

      <div className="overflow-hidden rounded-md border border-zinc-200 bg-white shadow-panel">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200 text-sm">
            <thead className="bg-zinc-50 text-left text-xs uppercase tracking-normal text-zinc-500">
              <tr>
                <th className="px-6 py-3">Job ID</th>
                <th className="px-6 py-3">Failed Reason / Error</th>
                <th className="px-6 py-3 text-center">Attempts</th>
                <th className="px-6 py-3">Created</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-zinc-500">
                    <AlertTriangle className="mx-auto h-8 w-8 text-zinc-400 mb-2" />
                    <p className="font-semibold text-zinc-700">All clear!</p>
                    <p className="text-xs text-zinc-400 mt-0.5">No failed jobs in the Dead Letter Queue.</p>
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr
                    key={job.id}
                    className="hover:bg-zinc-50 cursor-pointer"
                    onClick={() => setSelectedJobId(job.id)}
                  >
                    <td className="px-6 py-4">
                      <span className="font-mono text-xs font-semibold text-ink">{job.id.slice(0, 8)}...</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {job.tags.map((t) => (
                          <span key={t} className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-600 font-semibold">
                            {t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 max-w-md">
                      <div className="text-xs font-semibold text-rose-700 truncate" title={job.last_error || "Unknown Failure"}>
                        {job.last_error || "Execution exhausted maximum retry attempts"}
                      </div>
                      <div className="text-[10px] text-zinc-400 mt-0.5 truncate font-mono">
                        Action: {String(job.payload.action || "unknown")}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center font-mono text-zinc-700 font-semibold">
                      {job.retry_count} attempts
                    </td>
                    <td className="px-6 py-4 text-xs text-zinc-500 whitespace-nowrap">
                      <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> {new Date(job.scheduled_at).toLocaleDateString()}</span>
                      <span className="flex items-center gap-1 text-[10px] mt-0.5"><Clock className="h-3 w-3" /> {new Date(job.scheduled_at).toLocaleTimeString()}</span>
                    </td>
                    <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => setSelectedJobId(job.id)}
                          className="inline-flex h-8 w-8 items-center justify-center rounded border border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                          title="Inspect job audit logs and metadata"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleRequeue(job.id)}
                          disabled={actionLoadingId === job.id}
                          className="inline-flex h-8 w-8 items-center justify-center rounded border border-zinc-200 text-emerald-700 hover:bg-zinc-50 disabled:opacity-40"
                          title="Requeue back into active processing"
                        >
                          <RefreshCw className={`h-4 w-4 ${actionLoadingId === job.id ? "animate-spin" : ""}`} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedJobId && (
        <JobDetailDrawer
          jobId={selectedJobId}
          onClose={() => setSelectedJobId(null)}
          onJobUpdated={loadDLQ}
        />
      )}
    </div>
  );
}
