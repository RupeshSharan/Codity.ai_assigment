import { useEffect, useState } from "react";
import { AppShell } from "./layouts/AppShell";
import { Overview } from "./pages/Overview";
import { Auth } from "./pages/Auth";
import { Queues } from "./pages/Queues";
import { Jobs } from "./pages/Jobs";
import { Workers } from "./pages/Workers";
import { DeadLetter } from "./pages/DeadLetter";
import { Policies } from "./pages/Policies";
import { api } from "./services/api";
import type { Job, OverviewMetrics, Queue, Worker } from "./types/api";

const fallbackMetrics: OverviewMetrics = {
  running_jobs: 0,
  queued_jobs: 0,
  failed_jobs: 0,
  completed_jobs: 0,
  workers_online: 0,
  queue_health: { active: 0, paused: 0 },
  retry_rate_percent: 0.0,
  average_execution_ms: null
};

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("pulsequeue_token"));
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Nav & Selection state
  const [currentTab, setCurrentTab] = useState("Overview");
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [projectName, setProjectName] = useState<string>("");

  // Live operation metrics/tables
  const [metrics, setMetrics] = useState<OverviewMetrics>(fallbackMetrics);
  const [queues, setQueues] = useState<Queue[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [workers, setWorkers] = useState<Worker[]>([]);

  // Check auth and bootstrap project
  useEffect(() => {
    if (!token) {
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    const bootstrap = async () => {
      try {
        // 1. Verify token & get current user
        await api.me();
        setIsAuthenticated(true);

        // 2. Fetch or create Organization
        let orgs = await api.organizations();
        let orgId = "";
        if (orgs.length === 0) {
          const newOrg = await api.createOrganization("Acme Organization");
          orgId = newOrg.id;
        } else {
          orgId = orgs[0].id;
        }

        // 3. Fetch or create Project
        let projs = await api.projects(orgId);
        let project = null;
        if (projs.length === 0) {
          project = await api.createProject(orgId, "Payment Processing", "Critical backend queues sandbox");
          projs = [project];
        } else {
          project = projs[0];
        }

        setProjects(projs);
        
        // 4. Set selected project
        const storedProjectId = localStorage.getItem("pulsequeue_project_id");
        const activeProject = projs.find(p => p.id === storedProjectId) || project;
        
        setSelectedProjectId(activeProject.id);
        setProjectName(`${orgs[0]?.name || "Acme"} / ${activeProject.name}`);
        localStorage.setItem("pulsequeue_project_id", activeProject.id);

      } catch (err) {
        console.error("Authentication or bootstrapping failed, clearing token", err);
        localStorage.removeItem("pulsequeue_token");
        setToken(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    bootstrap();
  }, [token]);

  // Periodic polling for selected project
  useEffect(() => {
    if (!isAuthenticated || !selectedProjectId) return;

    const poll = () => {
      Promise.allSettled([
        api.overview(),
        api.queues(selectedProjectId),
        api.jobs(selectedProjectId, { limit: 5 }),
        api.workers()
      ]).then((results) => {
        if (results[0].status === "fulfilled") setMetrics(results[0].value);
        if (results[1].status === "fulfilled") setQueues(results[1].value);
        if (results[2].status === "fulfilled") setJobs(results[2].value.items);
        if (results[3].status === "fulfilled") setWorkers(results[3].value);
      });
    };

    poll();
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, [isAuthenticated, selectedProjectId]);

  const handleAuthSuccess = (newToken: string) => {
    setToken(newToken);
  };

  const handleProjectChange = (projectId: string) => {
    setSelectedProjectId(projectId);
    localStorage.setItem("pulsequeue_project_id", projectId);
    const proj = projects.find(p => p.id === projectId);
    if (proj) {
      setProjectName(`Acme Organization / ${proj.name}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("pulsequeue_token");
    localStorage.removeItem("pulsequeue_project_id");
    setToken(null);
    setIsAuthenticated(false);
    setMetrics(fallbackMetrics);
    setQueues([]);
    setJobs([]);
    setWorkers([]);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-mist">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-pulse border-t-transparent"></div>
          <p className="mt-3 text-sm font-medium text-zinc-500">Initializing PulseQueue Console...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Auth onAuthSuccess={handleAuthSuccess} />;
  }

  // View Router switching
  const renderContent = () => {
    switch (currentTab) {
      case "Overview":
        return <Overview metrics={metrics} queues={queues} jobs={jobs} workers={workers} />;
      case "Queues":
        return <Queues projectId={selectedProjectId} />;
      case "Jobs":
        return <Jobs projectId={selectedProjectId} />;
      case "Workers":
        return <Workers />;
      case "Dead Letter":
        return <DeadLetter projectId={selectedProjectId} />;
      case "Policies":
        return <Policies projectId={selectedProjectId} />;
      default:
        return <Overview metrics={metrics} queues={queues} jobs={jobs} workers={workers} />;
    }
  };

  return (
    <AppShell
      currentTab={currentTab}
      onTabChange={setCurrentTab}
      projects={projects}
      selectedProjectId={selectedProjectId}
      onProjectChange={handleProjectChange}
      onLogout={handleLogout}
      projectName={projectName}
    >
      {renderContent()}
    </AppShell>
  );
}
