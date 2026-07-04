import { useState } from "react";
import { api } from "../services/api";
import type { Queue } from "../types/api";
import { X, Play } from "lucide-react";

export function CreateJobModal({
  queues,
  onClose,
  onJobCreated
}: {
  queues: Queue[];
  onClose: () => void;
  onJobCreated: () => void;
}) {
  const [queueId, setQueueId] = useState(queues[0]?.id || "");
  const [kind, setKind] = useState<"immediate" | "delayed" | "scheduled" | "recurring">("immediate");
  const [delaySeconds, setDelaySeconds] = useState<number | "">("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [cronExpression, setCronExpression] = useState("");
  const [priority, setPriority] = useState(50);
  const [tagsInput, setTagsInput] = useState("");
  const [preset, setPreset] = useState("echo");
  const [payloadText, setPayloadText] = useState(
    JSON.stringify({ action: "echo", message: "hello world" }, null, 2)
  );
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const presets: Record<string, any> = {
    echo: { action: "echo", message: "hello world" },
    sleep: { action: "sleep", seconds: 5 },
    fail: { action: "fail", message: "simulated task execution failure" }
  };

  const handlePresetChange = (name: string) => {
    setPreset(name);
    setPayloadText(JSON.stringify(presets[name], null, 2));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    let parsedPayload = {};
    try {
      parsedPayload = JSON.parse(payloadText);
    } catch {
      setError("Payload must be valid JSON.");
      setLoading(false);
      return;
    }

    const tags = tagsInput
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    const payload: any = {
      queue_id: queueId,
      kind,
      payload: parsedPayload,
      priority,
      tags
    };

    if (kind === "delayed" && delaySeconds !== "") {
      payload.delay_seconds = Number(delaySeconds);
    } else if (kind === "scheduled" && scheduledAt) {
      payload.scheduled_at = new Date(scheduledAt).toISOString();
    } else if (kind === "recurring" && cronExpression) {
      payload.cron_expression = cronExpression;
    }

    if (idempotencyKey.trim()) {
      payload.idempotency_key = idempotencyKey.trim();
    }

    try {
      await api.submitJob(payload);
      onJobCreated();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to submit job.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-900/40 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-lg border border-zinc-200 bg-white p-6 shadow-2xl flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between border-b pb-3">
          <h3 className="text-base font-semibold text-ink flex items-center gap-2">
            <Play className="h-4.5 w-4.5 text-pulse" /> Submit Background Job
          </h3>
          <button onClick={onClose} className="rounded-full p-1 hover:bg-zinc-100 text-zinc-500">
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded bg-red-50 p-3 text-xs text-red-700 border border-red-100">
            {error}
          </div>
        )}

        <form className="mt-4 space-y-4 overflow-y-auto pr-1 flex-1 text-sm" onSubmit={handleSubmit}>
          {/* Target Queue */}
          <div>
            <label className="block text-xs font-semibold text-zinc-500 uppercase mb-1">Target Queue</label>
            <select
              required
              value={queueId}
              onChange={(e) => setQueueId(e.target.value)}
              className="block w-full rounded border border-zinc-300 bg-white p-2.5 text-ink focus:border-pulse focus:outline-none"
            >
              <option value="" disabled>Select a Queue</option>
              {queues.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.name} (Priority: {q.priority})
                </option>
              ))}
            </select>
          </div>

          {/* Job Kind */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase mb-1">Job Type</label>
              <select
                value={kind}
                onChange={(e: any) => setKind(e.target.value)}
                className="block w-full rounded border border-zinc-300 bg-white p-2.5 text-ink focus:border-pulse focus:outline-none"
              >
                <option value="immediate">Immediate</option>
                <option value="delayed">Delayed</option>
                <option value="scheduled">Scheduled</option>
                <option value="recurring">Recurring (Cron)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase mb-1">Priority (0-100)</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  className="w-full accent-pulse cursor-pointer"
                />
                <span className="font-mono font-semibold text-ink w-8 text-right">{priority}</span>
              </div>
            </div>
          </div>

          {/* Timing details based on Job Kind */}
          {kind === "delayed" && (
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase mb-1">Delay (seconds)</label>
              <input
                type="number"
                required
                min="1"
                placeholder="e.g. 15"
                value={delaySeconds}
                onChange={(e) => setDelaySeconds(e.target.value !== "" ? Number(e.target.value) : "")}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
          )}

          {kind === "scheduled" && (
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase mb-1">Scheduled Time</label>
              <input
                type="datetime-local"
                required
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>
          )}

          {kind === "recurring" && (
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase mb-1">Cron Expression</label>
              <input
                type="text"
                required
                placeholder="*/5 * * * * (every 5 mins)"
                value={cronExpression}
                onChange={(e) => setCronExpression(e.target.value)}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none font-mono text-xs"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            {/* Tags */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase mb-1">Tags (comma separated)</label>
              <input
                type="text"
                placeholder="e.g. payments, critical"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none"
              />
            </div>

            {/* Idempotency Key */}
            <div>
              <label className="block text-xs font-semibold text-zinc-500 uppercase mb-1">Idempotency Key (Optional)</label>
              <input
                type="text"
                placeholder="e.g. txn_109283"
                value={idempotencyKey}
                onChange={(e) => setIdempotencyKey(e.target.value)}
                className="block w-full rounded border border-zinc-300 p-2.5 text-ink focus:border-pulse focus:outline-none font-mono"
              />
            </div>
          </div>

          {/* Payload Presets & Editor */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-zinc-500 uppercase">JSON Payload</label>
              <div className="flex gap-2">
                {Object.keys(presets).map((p) => (
                  <button
                    type="button"
                    key={p}
                    onClick={() => handlePresetChange(p)}
                    className={`rounded px-2 py-0.5 text-[10px] font-semibold uppercase border ${
                      preset === p ? "bg-pulse text-white border-pulse" : "bg-zinc-50 text-zinc-600 border-zinc-200"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              required
              rows={4}
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              className="block w-full rounded border border-zinc-300 bg-zinc-50 p-2.5 font-mono text-xs text-ink focus:border-pulse focus:outline-none leading-relaxed"
            />
          </div>

          {/* Submit */}
          <div className="border-t pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-zinc-200 px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded bg-pulse px-4 py-2 text-xs font-semibold text-white hover:bg-pulse/90 disabled:opacity-50"
            >
              {loading ? "Submitting..." : "Submit Job"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
