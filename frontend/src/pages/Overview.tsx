import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { datasetsApi, queryApi, workspacesApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { Dataset, QueryRecord, Usage, Workspace } from "../lib/types";

function formatBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(2)} MB`;
}

export default function Overview() {
  const { user } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [history, setHistory] = useState<QueryRecord[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);

  useEffect(() => {
    (async () => {
      const [ws, ds, hist] = await Promise.all([
        workspacesApi.list(),
        datasetsApi.list(),
        queryApi.history(),
      ]);
      setWorkspaces(ws);
      setDatasets(ds.items);
      setHistory(hist.items);
      if (ws[0]) setUsage(await workspacesApi.usage(ws[0].id));
    })();
  }, []);

  const queryPct = usage ? Math.min(100, Math.round((usage.query_count / usage.query_limit) * 100)) : 0;
  const storageMb = usage ? usage.storage_bytes / 1024 / 1024 : 0;
  const storagePct = usage ? Math.min(100, Math.round((storageMb / usage.storage_limit_mb) * 100)) : 0;
  const datasetPct = usage ? Math.min(100, Math.round((usage.dataset_count / usage.dataset_limit) * 100)) : 0;

  const stats = [
    { label: "Datasets", value: datasets.length, limit: usage?.dataset_limit, pct: datasetPct },
    { label: "Queries this month", value: usage?.query_count ?? 0, limit: usage?.query_limit, pct: queryPct },
    { label: "Storage used", value: formatBytes(usage?.storage_bytes ?? 0), limit: `${usage?.storage_limit_mb ?? 0} MB`, pct: storagePct },
    { label: "Plan", value: user?.plan === "pro" ? "Pro" : "Free", limit: user?.role === "admin" ? "Admin" : "Member", pct: null },
  ];

  return (
    <div className="max-w-6xl">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">
          Welcome back, {user?.name?.split(" ")[0]}
        </h1>
        <p className="text-slate-500 mt-1">Ask questions in plain English and get charts, SQL and business insights.</p>
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="card p-5">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{s.label}</div>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {typeof s.value === "number" ? s.value.toLocaleString() : s.value}
            </div>
            <div className="text-xs text-slate-500 mt-1">Limit: {s.limit}</div>
            {s.pct !== null && (
              <div className="w-full h-1.5 bg-slate-800 rounded-full mt-3 overflow-hidden">
                <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${s.pct}%` }} />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-100">Datasets</h2>
            <Link to="/datasets" className="text-sm text-indigo-400 hover:text-indigo-300">
              View all →
            </Link>
          </div>
          <div className="space-y-3">
            {datasets.slice(0, 5).map((d) => (
              <Link key={d.id} to={`/datasets?ds=${d.id}`} className="card p-4 block hover:border-indigo-500/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-slate-200">{d.name}</div>
                  <span className="badge bg-emerald-500/15 text-emerald-400">{d.row_count.toLocaleString()} rows</span>
                </div>
                <div className="text-xs text-slate-500 mt-1.5">
                  {d.column_count} columns · {d.source_type.toUpperCase()} · {new Date(d.created_at).toLocaleDateString()}
                </div>
              </Link>
            ))}
            {datasets.length === 0 && (
              <div className="card p-6 text-center text-slate-500 text-sm">
                No datasets yet. <Link to="/datasets" className="text-indigo-400">Upload your first one →</Link>
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-100">Recent questions</h2>
            <Link to="/ask" className="text-sm text-indigo-400 hover:text-indigo-300">
              Ask a question →
            </Link>
          </div>
          <div className="space-y-3">
            {history.slice(0, 6).map((q) => (
              <div key={q.id} className="card p-4">
                <div className="font-medium text-slate-200 text-sm">{q.question}</div>
                <div className="text-xs text-slate-500 mt-1.5 line-clamp-2">{q.summary}</div>
                <div className="text-[11px] text-slate-600 mt-1.5">{new Date(q.created_at).toLocaleString()}</div>
              </div>
            ))}
            {history.length === 0 && (
              <div className="card p-6 text-center text-slate-500 text-sm">
                <Link to="/ask" className="text-indigo-400">Ask your first question →</Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
