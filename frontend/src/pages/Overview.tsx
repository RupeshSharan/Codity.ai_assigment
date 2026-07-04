import { Activity, AlertTriangle, CheckCircle2, Clock3, ServerCog } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { JobTable } from "../components/JobTable";
import { QueueTable } from "../components/QueueTable";
import { StatTile } from "../components/StatTile";
import { WorkerPanel } from "../components/WorkerPanel";
import type { Job, OverviewMetrics, Queue, Worker } from "../types/api";

const throughput = [
  { hour: "08:00", completed: 52, failed: 2 },
  { hour: "09:00", completed: 81, failed: 4 },
  { hour: "10:00", completed: 73, failed: 1 },
  { hour: "11:00", completed: 96, failed: 6 },
  { hour: "12:00", completed: 88, failed: 3 },
  { hour: "13:00", completed: 112, failed: 5 }
];

export function Overview({
  metrics,
  queues,
  jobs,
  workers
}: {
  metrics: OverviewMetrics;
  queues: Queue[];
  jobs: Job[];
  workers: Worker[];
}) {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatTile label="Running" value={metrics.running_jobs} Icon={Activity} tone="text-pulse" />
        <StatTile label="Queued" value={metrics.queued_jobs} Icon={Clock3} tone="text-sky-600" />
        <StatTile label="Failed" value={metrics.failed_jobs} Icon={AlertTriangle} tone="text-ember" />
        <StatTile label="Completed" value={metrics.completed_jobs} Icon={CheckCircle2} tone="text-emerald-600" />
        <StatTile label="Workers" value={metrics.workers_online} Icon={ServerCog} tone="text-plum" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_340px]">
        <div className="rounded-md border border-zinc-200 bg-white p-4 shadow-panel">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-ink">Throughput</h2>
            <span className="text-xs text-zinc-500">Retry rate {metrics.retry_rate_percent}%</span>
          </div>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={throughput}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                <XAxis dataKey="hour" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip />
                <Bar dataKey="completed" fill="#0e7c7b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="failed" fill="#c75000" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <WorkerPanel workers={workers} />
      </section>

      <section className="grid gap-6 2xl:grid-cols-2">
        <QueueTable queues={queues} />
        <JobTable jobs={jobs} />
      </section>
    </div>
  );
}

