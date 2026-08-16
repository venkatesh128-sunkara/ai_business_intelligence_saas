import { useEffect, useState } from "react";
import { adminApi } from "../lib/api";
import type { AdminStats } from "../lib/types";

export default function Admin() {
  const [stats, setStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    adminApi.stats().then(setStats).catch(() => {});
  }, []);

  if (!stats) return <div className="text-slate-500">Loading admin stats…</div>;

  const cards = [
    { label: "Users", value: stats.users },
    { label: "Workspaces", value: stats.workspaces },
    { label: "Datasets", value: stats.datasets },
    { label: "Queries", value: stats.queries },
    { label: "Dashboards", value: stats.dashboards },
  ];

  return (
    <div className="max-w-6xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Admin</h1>
        <p className="text-slate-500 mt-1">Platform-wide usage overview.</p>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {cards.map((c) => (
          <div key={c.label} className="card p-5">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{c.label}</div>
            <div className="text-2xl font-bold text-slate-100 mt-2">{c.value.toLocaleString()}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h3 className="font-semibold text-slate-100 mb-4">Datasets by user</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-slate-500 text-xs uppercase">
                <th className="pb-2">User</th>
                <th className="pb-2 text-right">Datasets</th>
              </tr>
            </thead>
            <tbody>
              {stats.datasets_by_user.map((u) => (
                <tr key={u.email} className="border-b border-slate-800/60">
                  <td className="py-2.5 text-slate-300">
                    {u.name}
                    <div className="text-xs text-slate-500">{u.email}</div>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-200">{u.datasets}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card p-5">
          <h3 className="font-semibold text-slate-100 mb-4">Recent queries</h3>
          <div className="space-y-3">
            {stats.recent_queries.map((q, i) => (
              <div key={i} className="border-b border-slate-800/60 pb-3 last:border-0">
                <div className="text-sm text-slate-300">{q.question}</div>
                <div className="text-xs text-slate-500 mt-1">
                  {q.user} · {new Date(q.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
