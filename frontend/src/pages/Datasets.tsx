import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { datasetsApi, errMsg, workspacesApi } from "../lib/api";
import type { Dataset, Workspace } from "../lib/types";
import DataTable from "../components/DataTable";
import UploadDataset from "../components/UploadDataset";

export default function Datasets() {
  const [params, setParams] = useSearchParams();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selected, setSelected] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<{ columns: string[]; rows: unknown[][] } | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    const [ds, ws] = await Promise.all([datasetsApi.list(), workspacesApi.list()]);
    setDatasets(ds.items);
    setWorkspaces(ws);
    const id = Number(params.get("ds")) || ds.items[0]?.id;
    if (id) {
      const match = ds.items.find((d) => d.id === id) ?? ds.items[0];
      select(match);
    }
    setLoading(false);
  };

  const select = async (d: Dataset) => {
    setSelected(d);
    setParams({ ds: String(d.id) });
    const p = await datasetsApi.preview(d.id);
    setPreview(p);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const del = async (d: Dataset) => {
    if (!confirm(`Delete dataset "${d.name}"? This cannot be undone.`)) return;
    try {
      await datasetsApi.remove(d.id);
      const next = datasets.filter((x) => x.id !== d.id);
      setDatasets(next);
      if (next[0]) await select(next[0]);
      else {
        setSelected(null);
        setPreview(null);
      }
    } catch (e) {
      alert(errMsg(e));
    }
  };

  const uploaded = (d: Dataset) => {
    setDatasets((prev) => [d, ...prev]);
    select(d);
  };

  const schema = useMemo(() => selected?.schema.columns ?? [], [selected]);

  return (
    <div className="max-w-6xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Datasets</h1>
        <p className="text-slate-500 mt-1">Upload CSV/Excel files. They are cleaned, profiled and stored for analysis.</p>
      </header>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="space-y-6">
          <UploadDataset workspaces={workspaces} onUploaded={uploaded} />
          <div>
            <h2 className="font-semibold text-slate-100 mb-3">Your datasets</h2>
            <div className="space-y-2">
              {datasets.map((d) => (
                <div
                  key={d.id}
                  onClick={() => select(d)}
                  className={`card p-3.5 cursor-pointer transition-colors ${
                    selected?.id === d.id ? "border-indigo-500/60" : "hover:border-slate-600"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-slate-200 text-sm truncate">{d.name}</div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        del(d);
                      }}
                      className="text-slate-600 hover:text-rose-400 ml-2"
                      title="Delete"
                    >
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6" />
                      </svg>
                    </button>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    {d.row_count.toLocaleString()} rows · {d.column_count} cols · {d.source_type.toUpperCase()}
                  </div>
                </div>
              ))}
              {!loading && datasets.length === 0 && (
                <div className="card p-6 text-center text-slate-500 text-sm">No datasets yet. Upload one above.</div>
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {selected && (
            <>
              <div className="card p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-100">{selected.name}</h2>
                    <p className="text-sm text-slate-500 mt-0.5">
                      {selected.row_count.toLocaleString()} rows · {selected.column_count} columns · uploaded{" "}
                      {new Date(selected.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="badge bg-emerald-500/15 text-emerald-400">ready</span>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-slate-200 mb-3">Data profile</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {schema.map((c) => (
                    <div key={c.name} className="card p-3.5">
                      <div className="font-medium text-slate-200 text-sm truncate" title={c.name}>
                        {c.name}
                      </div>
                      <div className="text-[11px] text-indigo-400 mt-0.5">{c.dtype}</div>
                      <div className="text-[11px] text-slate-500 mt-1.5">
                        {c.unique.toLocaleString()} unique{c.missing > 0 ? ` · ${c.missing} missing` : ""}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-slate-200 mb-3">Preview</h3>
                {preview ? (
                  <DataTable columns={preview.columns} rows={preview.rows} />
                ) : (
                  <div className="card p-6 text-center text-slate-500 text-sm">Loading preview…</div>
                )}
              </div>
            </>
          )}
          {!selected && <div className="card p-10 text-center text-slate-500">Select a dataset to inspect it.</div>}
        </div>
      </div>
    </div>
  );
}
