interface Props {
  columns: string[];
  rows: unknown[][];
  maxRows?: number;
}

export default function DataTable({ columns, rows, maxRows = 50 }: Props) {
  const shown = rows.slice(0, maxRows);
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800 bg-ink-950/60">
            {columns.map((c) => (
              <th key={c} className="text-left px-4 py-3 font-semibold text-slate-300 whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((row, i) => (
            <tr key={i} className="border-b border-slate-800/60 hover:bg-slate-800/30">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2.5 text-slate-400 whitespace-nowrap">
                  {formatCell(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > maxRows && (
        <div className="px-4 py-2 text-xs text-slate-500">
          Showing {maxRows} of {rows.length} rows
        </div>
      )}
    </div>
  );
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return Number.isInteger(v) ? v.toLocaleString() : v.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(v);
}
