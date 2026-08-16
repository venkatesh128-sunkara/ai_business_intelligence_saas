import Plotly from "react-plotly.js";
import type { ChartFigure } from "../lib/types";

interface Props {
  figure: ChartFigure | null;
  height?: number;
  loading?: boolean;
}

export default function ChartView({ figure, height = 380, loading = false }: Props) {
  if (loading) {
    return (
      <div className="card flex items-center justify-center" style={{ height }}>
        <div className="flex items-center gap-3 text-slate-400">
          <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Generating visualization…</span>
        </div>
      </div>
    );
  }
  if (!figure || !figure.data || figure.data.length === 0) {
    return (
      <div className="card flex items-center justify-center text-slate-500 text-sm" style={{ height }}>
        No chart data available
      </div>
    );
  }
  return (
    <div className="card overflow-hidden">
      <Plotly
        data={figure.data as never[]}
        layout={{
          autosize: true,
          height,
          ...(figure.layout as Record<string, unknown>),
        }}
        config={{ responsive: true, displaylogo: false, modeBarButtonsToRemove: ["lasso2d", "select2d"] }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
