import {
  Activity,
  Boxes,
  LayoutDashboard,
  ListRestart,
  ServerCog,
  ShieldCheck,
  LogOut,
  FolderOpen
} from "lucide-react";
import type { ReactNode } from "react";

const nav = [
  { label: "Overview", Icon: LayoutDashboard },
  { label: "Queues", Icon: Boxes },
  { label: "Jobs", Icon: Activity },
  { label: "Workers", Icon: ServerCog },
  { label: "Dead Letter", Icon: ListRestart },
  { label: "Policies", Icon: ShieldCheck }
];

interface AppShellProps {
  children: ReactNode;
  currentTab: string;
  onTabChange: (tab: string) => void;
  projects: any[];
  selectedProjectId: string;
  onProjectChange: (projectId: string) => void;
  onLogout: () => void;
  projectName: string;
}

export function AppShell({
  children,
  currentTab,
  onTabChange,
  projects,
  selectedProjectId,
  onProjectChange,
  onLogout,
  projectName
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-mist text-ink flex">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-zinc-200 bg-white lg:block z-20">
        <div className="flex h-16 items-center border-b border-zinc-200 px-5 justify-between">
          <div className="flex items-center">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-pulse text-sm font-bold text-white">PQ</div>
            <div className="ml-3">
              <div className="text-sm font-semibold">PulseQueue</div>
              <div className="text-xs text-zinc-500">Operations Console</div>
            </div>
          </div>
        </div>

        {/* Project Selector inside sidebar */}
        {projects.length > 0 && (
          <div className="px-4 py-3 border-b border-zinc-100 bg-zinc-50">
            <label className="block text-[10px] font-semibold text-zinc-400 uppercase tracking-wider mb-1 flex items-center gap-1">
              <FolderOpen className="h-3 w-3" /> Active Project
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => onProjectChange(e.target.value)}
              className="block w-full rounded border border-zinc-300 bg-white px-2 py-1 text-xs text-ink focus:border-pulse focus:outline-none"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Nav list */}
        <nav className="space-y-1 px-3 py-4 flex-1">
          {nav.map(({ label, Icon }) => {
            const isActive = currentTab === label;
            return (
              <button
                key={label}
                onClick={() => onTabChange(label)}
                className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-pulse text-white shadow-sm"
                    : "text-zinc-600 hover:bg-zinc-100 hover:text-ink"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </button>
            );
          })}
        </nav>

        {/* Logout at bottom */}
        <div className="absolute bottom-0 w-full p-4 border-t border-zinc-100 bg-zinc-50/50">
          <button
            onClick={onLogout}
            className="flex w-full items-center gap-2 rounded px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Panel */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        <header className="sticky top-0 z-10 border-b border-zinc-200 bg-white/95 px-4 py-3 backdrop-blur lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-lg font-bold text-ink">Production Job Operations</h1>
              <p className="text-xs text-zinc-500 font-medium">{projectName || "Loading project..."}</p>
            </div>
            <div className="flex items-center gap-2 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live operations polling active</span>
            </div>
          </div>
        </header>
        <main className="flex-1 px-4 py-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
