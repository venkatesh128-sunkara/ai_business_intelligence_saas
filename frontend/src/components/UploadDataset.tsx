import { useEffect, useRef, useState } from "react";
import { datasetsApi, errMsg } from "../lib/api";
import type { Dataset, Workspace } from "../lib/types";

interface Props {
  workspaces: Workspace[];
  onUploaded: (d: Dataset) => void;
}

export default function UploadDataset({ workspaces, onUploaded }: Props) {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [workspaceId, setWorkspaceId] = useState<number>(workspaces[0]?.id ?? 0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!workspaceId && workspaces[0]) setWorkspaceId(workspaces[0].id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaces]);

  const submit = async () => {
    setError("");
    setSuccess("");
    if (!file || !name.trim()) {
      setError("Pick a file and give it a name.");
      return;
    }
    if (!workspaceId) {
      setError("No workspace available. Create a workspace first.");
      return;
    }
    setBusy(true);
    try {
      const ds = await datasetsApi.upload(workspaceId, name.trim(), file);
      const displayName = name.trim();
      setName("");
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      setSuccess(`"${displayName}" uploaded (${ds.row_count.toLocaleString()} rows).`);
      onUploaded(ds);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card p-5">
      <h2 className="font-semibold text-slate-100 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
        </svg>
        Upload dataset
      </h2>
      <div className="space-y-4">
        <div>
          <label className="label">Dataset name</label>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Q2 Sales Data" />
        </div>
        <div>
          <label className="label">Workspace</label>
          <select className="input" value={workspaceId} onChange={(e) => setWorkspaceId(Number(e.target.value))}>
            {workspaces.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>
        <div
          className="border-2 border-dashed border-slate-700 rounded-lg p-5 text-center cursor-pointer hover:border-indigo-500 transition-colors"
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <div className="text-sm text-slate-400">
            {file ? (
              <span className="text-indigo-300 font-medium">{file.name}</span>
            ) : (
              <>
                Drop a <span className="text-indigo-300">CSV or Excel</span> file here, or click to browse
              </>
            )}
          </div>
          <div className="text-xs text-slate-600 mt-1">Automatic cleaning, type inference and profiling included</div>
        </div>
        {error && <div className="text-sm text-rose-400">{error}</div>}
        {success && (
          <div className="text-sm text-emerald-400 flex items-center gap-2">
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6L9 17l-5-5" />
            </svg>
            {success}
          </div>
        )}
        <button className="btn-primary w-full" onClick={submit} disabled={busy}>
          {busy ? "Processing…" : "Upload & analyze"}
        </button>
      </div>
    </div>
  );
}
