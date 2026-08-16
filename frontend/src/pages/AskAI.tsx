import { useEffect, useRef, useState } from "react";
import { datasetsApi, dashboardsApi, errMsg, queryApi, workspacesApi } from "../lib/api";
import type { Dashboard, Dataset, QueryResult, Workspace } from "../lib/types";
import ChartView from "../components/ChartView";
import DataTable from "../components/DataTable";

interface ChatMsg extends QueryResult {
  error?: string;
}

const suggestions = [
  "What were the highest-revenue products?",
  "Total sales by region",
  "Show monthly revenue trend",
  "How many orders in Q2?",
  "Top 5 customers by total revenue",
];

export default function AskAI() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [busy, setBusy] = useState(false);
  const [showSql, setShowSql] = useState<Set<number>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);
  const [added, setAdded] = useState<Set<number>>(new Set());

  useEffect(() => {
    (async () => {
      const [ds, ws] = await Promise.all([datasetsApi.list(), workspacesApi.list()]);
      setDatasets(ds.items);
      setWorkspaces(ws);
      if (ds.items[0]) setDatasetId(ds.items[0].id);
      if (ws[0]) setDashboards(await dashboardsApi.list());
    })();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const ask = async (question: string) => {
    if (!question.trim() || !datasetId || busy) return;
    setInput("");
    setBusy(true);
    const optimistic: ChatMsg = {
      id: Math.random(),
      question,
      sql: "",
      summary: "",
      chart: { data: [], layout: {} },
      columns: [],
      rows: [],
      row_count: 0,
      conversation_id: conversationId ?? "",
      suggested_followups: [],
      engine: "rule",
    };
    setMessages((prev) => [...prev, optimistic]);
    try {
      const res = await queryApi.ask(question, datasetId, conversationId);
      setConversationId(res.conversation_id);
      setMessages((prev) => [...prev.slice(0, -1), res]);
    } catch (e) {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { ...optimistic, error: errMsg(e), summary: "Sorry, I could not answer that." },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const newConversation = () => {
    setConversationId(undefined);
    setMessages([]);
    setAdded(new Set());
  };

  const addToDashboard = async (m: QueryResult) => {
    const ws = workspaces[0];
    if (!ws) return;
    try {
      let target = dashboards[0];
      if (!target) {
        target = await dashboardsApi.create(ws.id, "My Dashboard", "Auto-created from Ask AI");
        setDashboards((prev) => [...prev, target]);
      }
      await dashboardsApi.addItem(target.id, m.id, m.question);
      setAdded((prev) => new Set(prev).add(m.id));
    } catch (e) {
      alert(errMsg(e));
    }
  };

  const toggleSql = (id: number) => {
    setShowSql((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="max-w-5xl mx-auto">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Ask AI</h1>
          <p className="text-slate-500 mt-1">Type a question in plain English. InsightIQ writes the SQL, runs it, and charts the answer.</p>
        </div>
        <button className="btn-secondary" onClick={newConversation}>
          New conversation
        </button>
      </header>

      <div className="mb-5">
        <label className="label">Dataset</label>
        <div className="flex flex-wrap gap-2">
          {datasets.map((d) => (
            <button
              key={d.id}
              onClick={() => {
                setDatasetId(d.id);
                setConversationId(undefined);
                setMessages([]);
              }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${
                datasetId === d.id
                  ? "bg-indigo-500/15 text-indigo-300 border-indigo-500/50"
                  : "bg-ink-900 text-slate-400 border-slate-800 hover:border-slate-600"
              }`}
            >
              {d.name}
              <span className="ml-1.5 text-xs text-slate-500">{d.row_count.toLocaleString()}</span>
            </button>
          ))}
          {datasets.length === 0 && <div className="text-sm text-slate-500">Upload a dataset to start asking questions.</div>}
        </div>
      </div>

      <div className="space-y-6 mb-6">
        {messages.length === 0 && !busy && (
          <div className="card p-8">
            <div className="text-sm text-slate-500 mb-4">Try asking:</div>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s) => (
                <button key={s} onClick={() => ask(s)} className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm transition-colors">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-indigo-500 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z" />
                </svg>
              </div>
              <div className="font-semibold text-slate-100">{m.question}</div>
            </div>
            {m.error ? (
              <div className="ml-9 card p-4 text-sm text-rose-400">{m.error}</div>
            ) : (
              <div className="ml-9 space-y-3">
                <div className="card p-4">
                  <p className="text-sm text-slate-300 leading-relaxed">{m.summary}</p>
                  <div className="flex items-center gap-3 mt-3 text-xs">
                    <button onClick={() => toggleSql(m.id!)} className="text-indigo-400 hover:text-indigo-300 font-medium">
                      {showSql.has(m.id!) ? "Hide SQL" : "View SQL"}
                    </button>
                    <span className="text-slate-600">·</span>
                    <span className="text-slate-500">{m.row_count} rows · {m.engine === "llm" ? "LLM engine" : "Rule engine"}</span>
                    {m.id && !added.has(m.id) && (
                      <>
                        <span className="text-slate-600">·</span>
                        <button onClick={() => addToDashboard(m)} className="text-emerald-400 hover:text-emerald-300 font-medium">
                          + Add to dashboard
                        </button>
                      </>
                    )}
                  </div>
                  {showSql.has(m.id!) && (
                    <pre className="mt-3 p-3 rounded-lg bg-ink-950 text-xs text-emerald-300 overflow-x-auto">{m.sql}</pre>
                  )}
                </div>
                <ChartView figure={m.chart} />
                {m.rows.length > 0 && <DataTable columns={m.columns} rows={m.rows} />}
                {m.suggested_followups.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {m.suggested_followups.map((f) => (
                      <button
                        key={f}
                        onClick={() => ask(f)}
                        className="px-2.5 py-1.5 rounded-lg bg-slate-800/70 hover:bg-slate-700 text-slate-400 text-xs transition-colors"
                      >
                        ↳ {f}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {busy && (
          <div className="flex items-center gap-3 ml-9 text-slate-400 text-sm">
            <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            Analyzing your data…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="sticky bottom-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(input);
          }}
          className="card p-2 flex items-center gap-2"
        >
          <input
            className="flex-1 bg-transparent px-3 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder='Ask e.g. "What were our highest-revenue products?"'
            disabled={busy || !datasetId}
          />
          <button type="submit" className="btn-primary" disabled={busy || !input.trim() || !datasetId}>
            {busy ? "…" : "Ask"}
          </button>
        </form>
      </div>
    </div>
  );
}
