import type { Insight } from "../lib/types";

const severityStyle: Record<string, string> = {
  high: "bg-rose-500/15 text-rose-400",
  medium: "bg-amber-500/15 text-amber-400",
  low: "bg-sky-500/15 text-sky-400",
  info: "bg-slate-600/20 text-slate-400",
};

const categoryIcon: Record<string, string> = {
  trend: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  top_performer: "M8 21h8M12 17v4M7 4h10v4a5 5 0 01-10 0V4z",
  outlier: "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01",
  correlation: "M4 4v16h16M7 15l4-6 4 3 3-5",
  anomaly: "M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z",
  summary: "M4 6h16M4 12h16M4 18h16",
};

export default function InsightCard({ insight }: { insight: Insight }) {
  return (
    <div className="card p-4 flex gap-3">
      <div className="w-9 h-9 shrink-0 rounded-lg bg-indigo-500/15 flex items-center justify-center text-indigo-400">
        <svg className="w-4.5 h-4.5 w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d={categoryIcon[insight.category] ?? categoryIcon.summary} />
        </svg>
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-slate-100 text-sm">{insight.title}</h3>
          <span className={`badge ${severityStyle[insight.severity] ?? severityStyle.info}`}>{insight.severity}</span>
          {insight.llm && (
            <span className="badge bg-purple-500/15 text-purple-300" title="Enriched by LLM">
              AI
            </span>
          )}
        </div>
        <p className="text-sm text-slate-400 mt-1.5 leading-relaxed">{insight.description}</p>
      </div>
    </div>
  );
}
