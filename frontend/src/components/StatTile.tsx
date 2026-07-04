import type { LucideIcon } from "lucide-react";

export function StatTile({
  label,
  value,
  Icon,
  tone
}: {
  label: string;
  value: string | number;
  Icon: LucideIcon;
  tone: string;
}) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white p-4 shadow-panel">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-normal text-zinc-500">{label}</span>
        <Icon className={`h-4 w-4 ${tone}`} aria-hidden="true" />
      </div>
      <div className="mt-3 text-2xl font-semibold text-ink">{value}</div>
    </div>
  );
}

