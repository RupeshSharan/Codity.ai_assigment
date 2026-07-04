import { useState, useEffect } from "react";
import { api } from "../services/api";
import type { Job, Queue, JobStatus } from "../types/api";
import { StatusPill } from "../components/StatusPill";
import { CreateJobModal } from "../components/CreateJobModal";
import { JobDetailDrawer } from "../components/JobDetailDrawer";
import { Search, Plus, RotateCcw, Eye, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";

export function Jobs({ projectId }: { projectId: string }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [queues, setQueues] = useState<Queue[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters State
  const [selectedQueue, setSelectedQueue] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<JobStatus | "">("");
  const [tagSearch, setTagSearch] = useState("");
  const [limit] = useState(15);
  const [offset, setOffset] = useState(0);

  // Modals & Panels State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const loadQueues = async () => {
    try {
      const data = await api.queues(projectId);
      setQueues(data);
    } catch (err) {
      console.error("Failed to load queues", err);
    }
  };

  const loadJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.jobs(projectId, {
        queue_id: selectedQueue || undefined,
        status: selectedStatus || undefined,
        tag: tagSearch.trim() || undefined,
        limit,
        offset
      });
      setJobs(data.items);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.message || "Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueues();
  }, [projectId]);

  useEffect(() => {
    loadJobs();
  }, [projectId, selectedQueue, selectedStatus, tagSearch, offset]);

  const handleRetryJob = async (jobId: string) => {
    try {
      await api.retryJob(jobId);
      loadJobs();
    } catch (err: any) {
      alert(err.message || "Failed to retry job");
    }
  };

  const handlePageChange = (direction: "prev" | "next") => {
    if (direction === "prev" && offset > 0) {
      setOffset(Math.max(0, offset - limit));
    } else if (direction === "next" && offset + limit < total) {
      setOffset(offset + limit);
    }
  };

  const activePage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">Job Explorer</h2>
          <p className="text-xs text-zinc-500">Inspect, search, and retry background processing jobs.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadJobs}
            className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-zinc-200 bg-white px-3 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md bg-pulse px-3 text-xs font-semibold text-white hover:bg-pulse/90"
          >
            <Plus className="h-3.5 w-3.5" />
            Submit Job
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="grid gap-3 rounded-md border border-zinc-200 bg-white p-4 shadow-panel md:grid-cols-3 text-xs">
        <div>
          <label className="block font-semibold text-zinc-500 uppercase mb-1">Filter by Queue</label>
          <select
            value={selectedQueue}
            onChange={(e) => {
              setSelectedQueue(e.target.value);
              setOffset(0);
            }}
            className="block w-full rounded border border-zinc-300 bg-white p-2.5 text-ink focus:border-pulse focus:outline-none"
          >
            <option value="">All Queues</option>
            {queues.map((q) => (
              <option key={q.id} value={q.id}>
                {q.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block font-semibold text-zinc-500 uppercase mb-1">Filter by Status</label>
          <select
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value as any);
              setOffset(0);
            }}
            className="block w-full rounded border border-zinc-300 bg-white p-2.5 text-ink focus:border-pulse focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="queued">Queued</option>
            <option value="scheduled">Scheduled</option>
            <option value="claimed">Claimed</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="dead_letter">Dead Letter</option>
          </select>
        </div>

        <div>
          <label className="block font-semibold text-zinc-500 uppercase mb-1">Search by Tag</label>
          <div className="relative">
            <input
              type="text"
              placeholder="e.g. payments"
              value={tagSearch}
              onChange={(e) => {
                setTagSearch(e.target.value);
                setOffset(0);
              }}
              className="block w-full rounded border border-zinc-300 p-2.5 pl-9 text-ink focus:border-pulse focus:outline-none"
            />
            <Search className="absolute left-3 top-3 h-4 w-4 text-zinc-400" />
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Jobs Table */}
      <div className="overflow-hidden rounded-md border border-zinc-200 bg-white shadow-panel">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200 text-sm">
            <thead className="bg-zinc-50 text-left text-xs uppercase tracking-normal text-zinc-500">
              <tr>
                <th className="px-6 py-3">Job ID / Tags</th>
                <th className="px-6 py-3">Queue</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Priority</th>
                <th className="px-6 py-3">Attempts</th>
                <th className="px-6 py-3">Scheduled At</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-10 text-center">
                    <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-pulse border-t-transparent"></div>
                  </td>
                </tr>
              ) : jobs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-10 text-center text-zinc-500 italic">
                    No jobs found matching the criteria.
                  </td>
                </tr>
              ) : (
                jobs.map((job) => {
                  const queue = queues.find((q) => q.id === job.queue_id);
                  return (
                    <tr
                      key={job.id}
                      className="hover:bg-zinc-50 cursor-pointer"
                      onClick={() => setSelectedJobId(job.id)}
                    >
                      <td className="px-6 py-4">
                        <div className="font-mono text-xs font-semibold text-ink">{job.id.slice(0, 8)}...</div>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {job.tags.length === 0 ? (
                            <span className="text-[10px] text-zinc-400 italic">untagged</span>
                          ) : (
                            job.tags.map((t) => (
                              <span key={t} className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-600 font-medium">
                                {t}
                              </span>
                            ))
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-xs font-semibold text-zinc-700">{queue ? queue.name : "unknown"}</td>
                      <td className="px-6 py-4">
                        <StatusPill value={job.status} />
                      </td>
                      <td className="px-6 py-4 text-zinc-700 font-mono">{job.priority}</td>
                      <td className="px-6 py-4 text-zinc-700 font-mono">{job.retry_count}</td>
                      <td className="px-6 py-4 text-xs text-zinc-600">
                        {new Date(job.scheduled_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setSelectedJobId(job.id)}
                            className="inline-flex h-8 w-8 items-center justify-center rounded border border-zinc-200 text-zinc-600 hover:bg-zinc-50"
                            title="Inspect job"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          {job.status === "dead_letter" && (
                            <button
                              onClick={() => handleRetryJob(job.id)}
                              className="inline-flex h-8 w-8 items-center justify-center rounded border border-zinc-200 text-emerald-700 hover:bg-zinc-50"
                              title="Requeue failed job"
                            >
                              <RotateCcw className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {!loading && total > 0 && (
          <div className="flex items-center justify-between border-t border-zinc-200 bg-zinc-50 px-6 py-3 text-xs text-zinc-600">
            <div>
              Showing <span className="font-semibold text-ink">{offset + 1}</span> to{" "}
              <span className="font-semibold text-ink">{Math.min(offset + limit, total)}</span> of{" "}
              <span className="font-semibold text-ink">{total}</span> jobs
            </div>
            <div className="flex items-center gap-4">
              <span>
                Page <span className="font-semibold text-ink">{activePage}</span> of{" "}
                <span className="font-semibold text-ink">{totalPages}</span>
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => handlePageChange("prev")}
                  disabled={offset === 0}
                  className="inline-flex h-8 w-8 items-center justify-center rounded border border-zinc-200 bg-white hover:bg-zinc-50 disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handlePageChange("next")}
                  disabled={offset + limit >= total}
                  className="inline-flex h-8 w-8 items-center justify-center rounded border border-zinc-200 bg-white hover:bg-zinc-50 disabled:opacity-40"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal / Drawer Overlays */}
      {showCreateModal && (
        <CreateJobModal
          queues={queues}
          onClose={() => setShowCreateModal(false)}
          onJobCreated={() => {
            setOffset(0);
            loadJobs();
          }}
        />
      )}

      {selectedJobId && (
        <JobDetailDrawer
          jobId={selectedJobId}
          onClose={() => setSelectedJobId(null)}
          onJobUpdated={loadJobs}
        />
      )}
    </div>
  );
}
