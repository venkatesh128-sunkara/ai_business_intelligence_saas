import { useEffect, useState } from "react";
import { datasetsApi, errMsg, insightsApi } from "../lib/api";
import type { Dataset, Insight } from "../lib/types";
import InsightCard from "../components/InsightCard";

export default function Insights() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [useLlm, setUseLlm] = useState(true);
  const [generatedFor, setGeneratedFor] = useState<number | null>(null);

  useEffect(() => {
    datasetsApi.list().then((r) => {
      setDatasets(r.items);
      if (r.items[0]) setDatasetId(r.items[0].id);
    });
  }, []);

  const generate = async () => {
    if (!datasetId) return;
    setLoading(true);
    setInsights([]);
    try {
      const result = await insightsApi.generate(datasetId, useLlm);
      setInsights(result);
      setGeneratedFor(datasetId);
    } catch (e) {
      alert(errMsg(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">AI Business Insights</h1>
        <p className="text-slate-500 mt-1">
          Statistical analysis of your data — trends, outliers, top performers, correlations and data-quality issues.
        </p>
      </header>

      <div className="card p-5 mb-8">
        <div className="flex flex-wrap items-end gap-4">
          <div className="min-w-[260px] flex-1">
            <label className="label">Dataset</label>
            <select className="input" value={datasetId ?? ""} onChange={(e) => setDatasetId(Number(e.target.value))}>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count.toLocaleString()} rows)
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2 pb-2">
            <button
              onClick={() => setUseLlm(!useLlm)}
              className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
                useLlm ? "bg-purple-500/15 text-purple-300 border-purple-500/50" : "bg-slate-800 text-slate-400 border-slate-700"
              }`}
            >
              {useLlm ? "AI narrative on" : "AI narrative off"}
            </button>
            <button className="btn-primary" onClick={generate} disabled={!datasetId || loading}>
              {loading ? "Analyzing…" : "Generate insights"}
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <div className="card p-10 text-center text-slate-400">
          <div className="w-7 h-7 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          Running statistical analysis…
        </div>
      )}

      {insights.length > 0 && (
        <div className="mb-4 text-sm text-slate-500">
          {insights.length} insights for <span className="text-slate-300 font-medium">{datasets.find((d) => d.id === generatedFor)?.name}</span>
        </div>
      )}

      <div className="grid gap-4">
        {insights.map((ins, i) => (
          <InsightCard key={i} insight={ins} />
        ))}
      </div>

      {!loading && insights.length === 0 && (
        <div className="card p-10 text-center text-slate-500 text-sm">
          Select a dataset and click "Generate insights" to see what InsightIQ found.
        </div>
      )}
    </div>
  );
}
