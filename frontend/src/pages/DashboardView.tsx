import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { dashboardsApi, errMsg } from "../lib/api";
import type { Dashboard } from "../lib/types";
import ChartView from "../components/ChartView";

export default function DashboardView() {
  const { id } = useParams();
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setDash(await dashboardsApi.get(Number(id)));
    } catch (e) {
      setError(errMsg(e));
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const removeItem = async (itemId: number) => {
    await dashboardsApi.removeItem(itemId);
    load();
  };

  if (error)
    return (
      <div className="card p-8 text-rose-400">
        {error} — <Link to="/dashboards" className="text-indigo-400">back to dashboards</Link>
      </div>
    );
  if (!dash) return <div className="text-slate-500">Loading dashboard…</div>;

  return (
    <div className="max-w-6xl">
      <div className="mb-6">
        <Link to="/dashboards" className="text-sm text-slate-500 hover:text-slate-300">← Dashboards</Link>
        <h1 className="text-2xl font-bold text-slate-100 mt-2">{dash.name}</h1>
        {dash.description && <p className="text-slate-500 mt-1">{dash.description}</p>}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {dash.items.map((item) => (
          <div key={item.id} className="group relative">
            <ChartView figure={item.chart_json} height={340} />
            <div className="flex items-center justify-between px-4 pt-3">
              <div className="text-sm font-medium text-slate-300 truncate">{item.title}</div>
              <button onClick={() => removeItem(item.id)} className="text-slate-600 hover:text-rose-400 ml-2 shrink-0" title="Remove">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>

      {dash.items.length === 0 && (
        <div className="card p-10 text-center text-slate-500 text-sm">
          This dashboard is empty. Go to <Link to="/ask" className="text-indigo-400">Ask AI</Link>, run a question, and click "+ Add to dashboard".
        </div>
      )}
    </div>
  );
}
