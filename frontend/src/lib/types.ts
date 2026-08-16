export interface User {
  id: number;
  name: string;
  email: string;
  role: "admin" | "member";
  plan: "free" | "pro";
  created_at: string;
}

export interface Workspace {
  id: number;
  name: string;
  description: string;
  owner_id: number;
  created_at: string;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  missing: number;
  unique: number;
  sample: unknown[];
  stats: Record<string, unknown>;
}

export interface Dataset {
  id: number;
  workspace_id: number;
  name: string;
  filename: string;
  source_type: string;
  status: string;
  row_count: number;
  column_count: number;
  file_size: number;
  profile_json: { columns: ColumnProfile[]; row_count: number; column_count: number };
  schema: { columns: ColumnProfile[]; row_count: number; column_count: number };
  created_at: string;
}

export interface ChartFigure {
  data: Record<string, unknown>[];
  layout: Record<string, unknown>;
}

export interface QueryResult {
  id: number;
  question: string;
  sql: string;
  summary: string;
  chart: ChartFigure;
  columns: string[];
  rows: unknown[][];
  row_count: number;
  conversation_id: string;
  suggested_followups: string[];
  engine: "llm" | "rule";
}

export interface QueryRecord {
  id: number;
  dataset_id: number;
  question: string;
  sql: string;
  summary: string;
  chart_json: ChartFigure;
  result_preview_json: { columns: string[]; rows: unknown[][] };
  conversation_id: string;
  created_at: string;
}

export interface QueryHistory {
  items: QueryRecord[];
  total: number;
}

export interface Insight {
  title: string;
  category: string;
  description: string;
  severity: "info" | "low" | "medium" | "high";
  data: Record<string, unknown>;
  llm?: boolean;
}

export interface DashboardItem {
  id: number;
  query_id: number;
  title: string;
  chart_json: ChartFigure;
  config_json: { x?: number; y?: number; w?: number; h?: number };
  created_at: string;
}

export interface Dashboard {
  id: number;
  workspace_id: number;
  name: string;
  description: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  items: DashboardItem[];
}

export interface Usage {
  year_month: string;
  query_count: number;
  query_limit: number;
  storage_bytes: number;
  storage_limit_mb: number;
  dataset_count: number;
  dataset_limit: number;
}

export interface AdminStats {
  users: number;
  workspaces: number;
  datasets: number;
  queries: number;
  dashboards: number;
  datasets_by_user: { name: string; email: string; datasets: number }[];
  recent_queries: { question: string; user: string; created_at: string }[];
}
