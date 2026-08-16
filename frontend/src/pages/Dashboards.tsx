import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { dashboardsApi, errMsg, workspacesApi } from "../lib/api";
import type { Dashboard, Workspace } from "../lib/types";

export default function Dashboards() {
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [name, setName] = useState("");
  const [wsId, setWsId] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const [ds, ws] = await Promise.all([dashboardsApi.list(), workspacesApi.list()]);
    setDashboards(ds);
    setWorkspaces(ws);
    if (ws[0]) setWsId(ws[0].id);
  };

  useEffect(() => {
    load();
  }, []);

  const create = async () => {
    if (!name.trim() || !wsId) return;
    setBusy(true);
    try {
      const d = await dashboardsApi.create(wsId, name.trim(), "");
      setDashboards((prev) => [d, ...prev]);
      setName("");
      setShowCreate(false);
    } catch (e) {
      alert(errMsg(e));
    } finally {
      setBusy(false);
    }
  };

  const del = async (d: Dashboard) => {
    if (!confirm(`Delete dashboard "${d.name}"?`)) return;
    await dashboardsApi.remove(d.id);
    setDashboards((prev) => prev.filter((x) => x.id !== d.id));
  };

  return (
    <div className="max-w-6xl">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Dashboards</h1>
          <p className="text-slate-500 mt-1">Save query results from Ask AI and combine them into live dashboards.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(!showCreate)}>
          + New dashboard
        </button>
      </header>

      {showCreate && (
        <div className="card p-5 mb-6">
          <h3 className="font-semibold text-slate-100 mb-4">Create dashboard</h3>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[240px]">
              <label className="label">Name</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Sales KPI Dashboard" />
            </div>
            <div className="min-w-[200px]">
              <label className="label">Workspace</label>
              <select className="input" value={wsId} onChange={(e) => setWsId(Number(e.target.value))}>
                {workspaces.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
            </div>
            <button className="btn-primary" onClick={create} disabled={busy || !name.trim()}>
              {busy ? "Creating…" : "Create"}
            </button>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {dashboards.map((d) => (
          <div key={d.id} className="card p-5 hover:border-indigo-500/50 transition-colors group">
            <Link to={`/dashboards/${d.id}`} className="block">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-100">{d.name}</h3>
                <span className="badge bg-indigo-500/15 text-indigo-300">{d.items.length} charts</span>
              </div>
              <p className="text-sm text-slate-500 mt-2 line-clamp-2">{d.description || "No description"}</p>
              <div className="text-xs text-slate-600 mt-3">Updated {new Date(d.updated_at).toLocaleDateString()}</div>
            </Link>
            <button
              onClick={() => del(d)}
              className="absolute top-3 right-3 text-slate-600 opacity-0 group-hover:opacity-100 hover:text-rose-400 transition-opacity"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6" />
              </svg>
            </button>
          </div>
        ))}
        {dashboards.length === 0 && !showCreate && (
          <div className="card p-10 text-center text-slate-500 text-sm col-span-full">
            No dashboards yet. Ask a question in <Link to="/ask" className="text-indigo-400">Ask AI</Link>, then add results to a dashboard.
          </div>
        )}
      </div>
    </div>
  );
}
