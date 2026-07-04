import { useEffect, useState } from "react";
import { api, JobDetailResponse } from "../services/api";
import { X, Calendar, RefreshCw, Cpu, FileText, AlertCircle, CheckCircle } from "lucide-react";
import { StatusPill } from "./StatusPill";

export function JobDetailDrawer({ jobId, onClose, onJobUpdated }: { jobId: string; onClose: () => void; onJobUpdated?: () => void }) {
  const [details, setDetails] = useState<JobDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  const fetchDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.jobDetails(jobId);
      setDetails(data);
    } catch (err: any) {
      setError(err.message || "Failed to load job details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [jobId]);

  const handleRetry = async () => {
    if (!details) return;
    setRetrying(true);
    try {
      await api.retryJob(details.job.id);
      if (onJobUpdated) onJobUpdated();
      fetchDetails();
    } catch (err: any) {
      alert(err.message || "Failed to retry job");
    } finally {
      setRetrying(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl border-l border-zinc-200 bg-white p-6 shadow-2xl flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-pulse border-t-transparent"></div>
          <p className="mt-2 text-sm text-zinc-500">Loading details...</p>
        </div>
      </div>
    );
  }

  if (error || !details) {
    return (
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl border-l border-zinc-200 bg-white p-6 shadow-2xl">
        <div className="flex justify-between items-center border-b pb-3">
          <h3 className="font-semibold text-ink">Job Details</h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-zinc-100"><X className="h-5 w-5" /></button>
        </div>
        <div className="mt-8 text-center text-red-500">
          <AlertCircle className="mx-auto h-8 w-8 text-red-500" />
          <p className="mt-2">{error || "Failed to retrieve job details."}</p>
        </div>
      </div>
    );
  }

  const { job, executions, logs } = details;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl border-l border-zinc-200 bg-white shadow-2xl flex flex-col">
      <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-semibold text-ink">{job.id}</span>
            <StatusPill value={job.status} />
          </div>
          <p className="text-xs text-zinc-500 mt-1">Tags: {job.tags.join(", ") || "none"}</p>
        </div>
        <div className="flex items-center gap-3">
          {job.status === "dead_letter" && (
            <button
              onClick={handleRetry}
              disabled={retrying}
              className="inline-flex items-center gap-1.5 rounded bg-pulse px-3 py-1.5 text-xs font-semibold text-white hover:bg-pulse/95 disabled:opacity-50"
            >
              <RefreshCw className={`h-3 w-3 ${retrying ? "animate-spin" : ""}`} />
              Requeue
            </button>
          )}
          <button onClick={onClose} className="rounded-full p-1 hover:bg-zinc-100 text-zinc-500"><X className="h-5 w-5" /></button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Core Stats */}
        <div className="grid grid-cols-2 gap-4 rounded-md border border-zinc-100 bg-zinc-50 p-4 text-xs">
          <div className="space-y-1">
            <div className="text-zinc-500">Priority</div>
            <div className="font-semibold text-ink">{job.priority}</div>
          </div>
          <div className="space-y-1">
            <div className="text-zinc-500">Attempts</div>
            <div className="font-semibold text-ink">{job.retry_count}</div>
          </div>
          <div className="space-y-1">
            <div className="text-zinc-500">Scheduled At</div>
            <div className="font-semibold text-ink">{new Date(job.scheduled_at).toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div className="text-zinc-500">Worker Lock</div>
            <div className="font-mono font-semibold text-ink">{job.locked_by_worker_id ?? "-"}</div>
          </div>
        </div>

        {/* Payload / Metadata */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 flex items-center gap-1">
            <FileText className="h-3.5 w-3.5" /> Payload & Metadata
          </h4>
          <pre className="overflow-x-auto rounded border border-zinc-200 bg-zinc-50 p-3 font-mono text-xs text-ink leading-relaxed">
            {JSON.stringify({ payload: job.payload, metadata: job.job_metadata }, null, 2)}
          </pre>
        </div>

        {/* Error message */}
        {job.last_error && (
          <div className="rounded-md border border-rose-100 bg-rose-50 p-4 text-xs text-rose-700">
            <div className="font-semibold flex items-center gap-1.5 text-rose-800 mb-1">
              <AlertCircle className="h-4 w-4 text-rose-600" /> Last Error Message
            </div>
            <p className="font-mono break-all leading-normal whitespace-pre-wrap">{job.last_error}</p>
          </div>
        )}

        {/* Executions timeline */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 flex items-center gap-1">
            <Cpu className="h-3.5 w-3.5" /> Execution Attempts ({executions.length})
          </h4>
          {executions.length === 0 ? (
            <p className="text-xs text-zinc-500 italic">No execution attempts recorded.</p>
          ) : (
            <div className="space-y-3">
              {executions.map((exec) => (
                <div key={exec.id} className="rounded border border-zinc-200 bg-white p-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-zinc-800">Attempt #{exec.attempt_number}</span>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium border ${
                      exec.status === "succeeded" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                      exec.status === "running" ? "bg-teal-50 text-teal-700 border-teal-200" :
                      "bg-rose-50 text-rose-700 border-rose-200"
                    }`}>
                      {exec.status}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-y-1 text-zinc-600">
                    <div>Worker: <span className="font-mono">{exec.worker_id ?? "-"}</span></div>
                    <div className="text-right">Duration: {exec.duration_ms ? `${exec.duration_ms}ms` : "-"}</div>
                    <div>Started: {new Date(exec.started_at).toLocaleString()}</div>
                    {exec.completed_at && <div className="text-right">Ended: {new Date(exec.completed_at).toLocaleString()}</div>}
                  </div>
                  {exec.error && (
                    <div className="mt-2 rounded bg-zinc-50 p-2 font-mono text-[10px] text-rose-600 border border-rose-100 break-all leading-normal">
                      {exec.error}
                    </div>
                  )}
                  {exec.result && (
                    <div className="mt-2 rounded bg-zinc-50 p-2 font-mono text-[10px] text-emerald-700 border border-emerald-100 break-all leading-normal">
                      Result: {JSON.stringify(exec.result)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Logs */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" /> Job Audit Logs ({logs.length})
          </h4>
          {logs.length === 0 ? (
            <p className="text-xs text-zinc-500 italic">No audit logs for this job.</p>
          ) : (
            <div className="rounded border border-zinc-200 bg-zinc-50 overflow-hidden divide-y divide-zinc-200">
              {logs.map((log) => (
                <div key={log.id} className="p-3 text-[11px] font-mono leading-normal hover:bg-zinc-100/50">
                  <div className="flex items-center justify-between text-zinc-400 mb-1">
                    <span>{new Date(log.created_at).toLocaleTimeString()}</span>
                    <span className={`${
                      log.level === "ERROR" ? "text-rose-600 font-bold" :
                      log.level === "WARNING" ? "text-amber-600" :
                      "text-zinc-500"
                    }`}>{log.level}</span>
                  </div>
                  <div className="text-zinc-800 font-medium">{log.message}</div>
                  {Object.keys(log.context).length > 0 && (
                    <div className="text-zinc-500 mt-1 text-[10px] break-all">
                      Context: {JSON.stringify(log.context)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
